"""APScheduler configuration for running scheduled tasks."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
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


def init_scheduler(app: Flask):
    """
    Initialize and start the APScheduler for scheduled tasks.

    Args:
        app: Flask application instance

    The scheduler is configured to run the rate update task daily at 9:00 AM EST.
    You can modify the cron schedule in the code or move it to configuration.
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

    # Schedule daily rate updates at 9:00 AM EST
    # You can configure this via environment variables or config.py
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

    # Start the scheduler
    scheduler.start()
    logger.info(
        f"Scheduler started. Daily rate updates scheduled for "
        f"{schedule_hour:02d}:{schedule_minute:02d} EST"
    )

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
