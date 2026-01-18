"""Background scheduler for automated rate updates and alert evaluation."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, current_app
from datetime import datetime
from . import db
from .models import Alert, Trigger, Mortgage, User
from .calc import calc_loan_monthly_payment
from .notifications import send_alert_notification
from .rate_updater import RateUpdater

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def scheduled_rate_update():
    """
    Scheduled task function that updates mortgage rates.

    This function is called by APScheduler according to the cron schedule.
    It runs within the Flask app context to access the database.
    """
    from . import init_app

    # Create app context for database access
    app = init_app()
    with app.app_context():
        logger.info("Running scheduled rate update...")
        try:
            updater = RateUpdater()
            results = updater.update_all_rates()
            logger.info(
                f"Scheduled update complete: "
                f"updated={results['updated']}, "
                f"alerts_triggered={results['alerts_triggered']}, "
                f"current_rate={results['current_rate']:.4f}"
            )
        except Exception as e:
            logger.error(f"Scheduled rate update failed: {e}")
            logger.exception("Full traceback:")


def evaluate_alert(alert):
    """
    Evaluate if an alert's conditions are met based on current market rates.

    Args:
        alert: Alert object to evaluate

    Returns:
        tuple: (triggered: bool, reason: str, current_rate: float)
    """
    mortgage = Mortgage.query.get(alert.mortgage_id)
    if not mortgage:
        return False, "Mortgage not found", None

    # Get current market rates from RateUpdater
    updater = RateUpdater()
    current_rates = updater.rate_fetcher.fetch_rates()

    # Determine term in years for rate lookup
    target_term_years = alert.target_term // 12
    if target_term_years not in current_rates:
        # Find closest term
        closest_term = min(current_rates.keys(), key=lambda x: abs(x - target_term_years))
        current_market_rate = current_rates[closest_term]
    else:
        current_market_rate = current_rates[target_term_years]

    triggered = False
    reason = ""

    if alert.alert_type == "monthly_payment" and alert.target_monthly_payment:
        # Calculate what monthly payment would be at current rates
        potential_monthly = calc_loan_monthly_payment(
            mortgage.remaining_principal,
            current_market_rate,
            alert.target_term
        )

        # Check if current rates would allow user to meet their target monthly payment
        # Include refinance costs in calculation
        adjusted_principal = mortgage.remaining_principal + alert.estimate_refinance_cost
        adjusted_monthly = calc_loan_monthly_payment(
            adjusted_principal,
            current_market_rate,
            alert.target_term
        )

        if adjusted_monthly <= alert.target_monthly_payment:
            triggered = True
            reason = f"Current market rate of {current_market_rate*100:.2f}% allows monthly payment of ${adjusted_monthly:.2f}, which meets your target of ${alert.target_monthly_payment:.2f}"

    elif alert.alert_type == "interest_rate" and alert.target_interest_rate:
        # Check if current market rate is below target
        if current_market_rate <= alert.target_interest_rate:
            triggered = True
            reason = f"Current market rate of {current_market_rate*100:.2f}% has reached your target of {alert.target_interest_rate*100:.2f}%"

    return triggered, reason, current_market_rate


def check_and_trigger_alerts():
    """
    Check all active alerts and trigger notifications if conditions are met.

    This function runs on a schedule and evaluates all active paid alerts.
    """
    try:
        current_app.logger.info("Starting scheduled alert check...")

        # Get all active alerts with paid subscriptions (not paused, not soft-deleted)
        active_alerts = Alert.query.filter_by(payment_status='active', deleted_at=None).filter(
            Alert.paused_at.is_(None)
        ).all()

        current_app.logger.info(f"Found {len(active_alerts)} active alerts to check")

        triggered_count = 0
        for alert in active_alerts:
            try:
                # Evaluate if alert conditions are met
                triggered, reason, current_rate = evaluate_alert(alert)

                if triggered:
                    # Check if we already triggered this alert recently (within 24 hours)
                    recent_trigger = Trigger.query.filter_by(
                        alert_id=alert.id,
                        alert_trigger_status=1
                    ).order_by(Trigger.created_on.desc()).first()

                    # Only trigger if no recent trigger, or if rate has improved significantly
                    should_create_trigger = True
                    if recent_trigger and recent_trigger.created_on:
                        hours_since_last = (datetime.utcnow() - recent_trigger.created_on).total_seconds() / 3600
                        if hours_since_last < 24:
                            should_create_trigger = False
                            current_app.logger.info(f"Alert {alert.id} already triggered within 24 hours, skipping")

                    if should_create_trigger:
                        # Create trigger record
                        trigger = Trigger(
                            alert_id=alert.id,
                            alert_type=alert.alert_type,
                            alert_trigger_status=1,
                            alert_trigger_reason=reason,
                            alert_trigger_date=datetime.utcnow(),
                            created_on=datetime.utcnow(),
                            updated_on=datetime.utcnow()
                        )
                        db.session.add(trigger)
                        db.session.commit()

                        current_app.logger.info(f"Alert {alert.id} triggered: {reason}")

                        # Send notification
                        send_alert_notification(trigger.id)
                        triggered_count += 1

            except Exception as e:
                current_app.logger.error(f"Error evaluating alert {alert.id}: {str(e)}")
                continue

        current_app.logger.info(f"Alert check complete. Triggered {triggered_count} alerts.")

    except Exception as e:
        current_app.logger.error(f"Error in scheduled alert check: {str(e)}")


def init_scheduler(app: Flask):
    """
    Initialize and start the APScheduler for scheduled tasks.

    Args:
        app: Flask application instance

    The scheduler is configured to run:
    - Daily rate updates at configured time (default 9:00 AM EST)
    - Alert checks every 4 hours and daily at 9 AM
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already initialized, skipping...")
        return scheduler

    # Create scheduler
    scheduler = BackgroundScheduler(
        daemon=True,
        timezone='America/New_York'  # EST/EDT timezone
    )

    # Schedule daily rate updates at configured time
    schedule_hour = app.config.get('RATE_UPDATE_HOUR', 9)
    schedule_minute = app.config.get('RATE_UPDATE_MINUTE', 0)

    scheduler.add_job(
        func=scheduled_rate_update,
        trigger=CronTrigger(
            hour=schedule_hour,
            minute=schedule_minute,
            timezone='America/New_York'
        ),
        id='daily_rate_update',
        name='Daily Mortgage Rate Update',
        replace_existing=True
    )

    # Add job to check alerts daily at 9 AM
    scheduler.add_job(
        func=lambda: check_and_trigger_alerts(),
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_alert_check',
        name='Check mortgage alerts daily',
        replace_existing=True
    )

    # Optional: Add more frequent checks (every 4 hours)
    scheduler.add_job(
        func=lambda: check_and_trigger_alerts(),
        trigger=CronTrigger(hour='*/4'),
        id='frequent_alert_check',
        name='Check mortgage alerts every 4 hours',
        replace_existing=True
    )

    # Start the scheduler
    scheduler.start()
    logger.info(
        f"Scheduler started. Daily rate updates scheduled for "
        f"{schedule_hour:02d}:{schedule_minute:02d} EST"
    )
    logger.info(f"Alert checks scheduled: daily at 9 AM and every 4 hours")

    # Shutdown scheduler when app terminates
    import atexit
    atexit.register(lambda: scheduler.shutdown())

    return scheduler


def get_scheduler_status():
    """
    Get information about scheduled jobs.

    Returns:
        List of job information dictionaries
    """
    if scheduler is None:
        return []

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    return jobs


def shutdown_scheduler():
    """Shutdown the background scheduler gracefully."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")


def trigger_manual_check():
    """
    Manually trigger an alert check (useful for testing or admin operations).

    Returns:
        str: Status message
    """
    try:
        check_and_trigger_alerts()
        return "Manual alert check completed successfully"
    except Exception as e:
        return f"Manual alert check failed: {str(e)}"
