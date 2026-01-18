"""Routes for parent Flask app."""
import os
import time
from datetime import datetime, timedelta
from flask import render_template, jsonify
from flask import current_app as app
from flask import send_from_directory
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import func
from . import db
from .models import Mortgage, Alert, Trigger, Subscription, User, MortgageRate, EmailLog
from .plots import *
from .scheduler import trigger_manual_check
from . import db

# Blueprint Configuration
main_bp = Blueprint(
    'main_bp', __name__, template_folder='templates', static_folder='static'
)


# @main_bp.route('/')
# def home():
#     """Landing page."""
#     return render_template(
#         'index.jinja2',
#         title='Refinance Monitor',
#         description='Set it and forget it!',
#         template='home-template',
#         body="We watch mortgage rates so you don't have to",
#     )


@main_bp.route('/setalert/')
def setalert():
    """Set alert page"""
    return render_template(
        'setalert.jinja2',
        title='Set Refinance Alert',
        description='Set your alert!',
        template='home-template',
        body="We watch mortgage rates so you don't have to",
    )


@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )


@main_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    """Logged-in User Dashboard."""

    mortgages = Mortgage.query.filter_by(user_id=current_user.id)
    mortgage_ids = [m.id for m in mortgages]
    alerts = Alert.query.join(Subscription).filter(
        Alert.mortgage_id.in_(mortgage_ids),
        Subscription.initial_payment == True
    ).all()

    # Refresh mortgages query for iteration
    mortgages = Mortgage.query.filter_by(user_id=current_user.id)
    mortgage_alerts = []
    for m in mortgages:
        matched = 0
        for a in alerts:
            if m.id == a.mortgage_id:
                mortgage_alerts.append(
                    [m, a, status_target_payment_plot(m.id), time_target_plot(m.id)]
                )
                matched += 1
        if matched == 0:
            mortgage_alerts.append([m, None, None, None])

    return render_template(
        'dashboard.jinja2',
        title='Refinance Monitor Dashboard',
        template='dashboard-template',
        current_user=current_user,
        body="Refinance Monitor Dashboard for " + current_user.name,
        mortgages=mortgages,
        alerts=alerts,
        mortgage_alerts=mortgage_alerts,
    )


@main_bp.route('/manage', methods=['GET'])
@login_required
def manage():
    """Logged-in User Dashboard."""

    mortgages = Mortgage.query.filter_by(user_id=current_user.id)
    mortgage_ids = [m.id for m in mortgages]
    alerts = Alert.query.join(Subscription).filter(
        Alert.mortgage_id.in_(mortgage_ids),
        Subscription.initial_payment == True
    ).all()

    # Refresh mortgages query for iteration
    mortgages = Mortgage.query.filter_by(user_id=current_user.id)
    mortgage_alerts = []
    for m in mortgages:
        matched = 0
        for a in alerts:
            if m.id == a.mortgage_id:
                mortgage_alerts.append(
                    [m, a, status_target_payment_plot(m.id), time_target_plot(m.id)]
                )
                matched += 1
        if matched == 0:
            mortgage_alerts.append([m, None, None, None])

    return render_template(
        'manage.jinja2',
        title='Refinance Monitor Management',
        template='manage-template',
        current_user=current_user,
        body="Refinance Monitor Management for " + current_user.name,
        mortgages=mortgages,
        alerts=alerts,
        mortgage_alerts=mortgage_alerts,
    )


@main_bp.route("/logout")
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    return redirect(url_for('auth_bp.login'))


@main_bp.route("/admin/trigger-alerts", methods=['POST'])
@login_required
def admin_trigger_alerts():
    """
    Admin endpoint to manually trigger alert checks.
    Useful for testing and on-demand alert evaluation.
    """
    # TODO: Add proper admin role checking
    # For now, any logged-in user can trigger (should be restricted in production)
    try:
        result = trigger_manual_check()
        return jsonify({'status': 'success', 'message': result}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/history', methods=['GET'])
@login_required
def history():
    """Alert History View - shows past triggers with dates, reasons, and actions."""
    mortgages = Mortgage.query.filter_by(user_id=current_user.id).all()
    mortgage_ids = [m.id for m in mortgages]

    alerts = Alert.query.join(Subscription).filter(
        Alert.mortgage_id.in_(mortgage_ids),
        Subscription.initial_payment == True
    ).all()
    alert_ids = [a.id for a in alerts]

    triggers = Trigger.query.filter(
        Trigger.alert_id.in_(alert_ids)
    ).order_by(Trigger.alert_trigger_date.desc()).all()

    # Build trigger data with related alert and mortgage info
    trigger_history = []
    for trigger in triggers:
        alert = Alert.query.get(trigger.alert_id)
        mortgage = Mortgage.query.get(alert.mortgage_id) if alert else None
        trigger_history.append({
            'trigger': trigger,
            'alert': alert,
            'mortgage': mortgage
        })

    return render_template(
        'alert_history.jinja2',
        title='Alert History',
        template='history-template',
        current_user=current_user,
        trigger_history=trigger_history,
        alerts=alerts,
        mortgages=mortgages
    )


@main_bp.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    """Admin Dashboard with user counts, subscription metrics, and system status."""

    # User metrics
    total_users = User.query.count()
    verified_users = User.query.filter_by(email_verified=True).count()
    unverified_users = total_users - verified_users

    # Users created in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_on >= week_ago).count()

    # Subscription metrics
    total_subscriptions = Subscription.query.count()
    active_subscriptions = Subscription.query.filter_by(payment_status='active').count()
    failed_subscriptions = Subscription.query.filter_by(payment_status='payment_failed').count()
    incomplete_subscriptions = Subscription.query.filter_by(payment_status='incomplete').count()
    paused_subscriptions = Subscription.query.filter(Subscription.paused_at.isnot(None)).count()

    # Alert metrics
    total_alerts = Alert.query.filter(Alert.deleted_at.is_(None)).count()
    deleted_alerts = Alert.query.filter(Alert.deleted_at.isnot(None)).count()

    # Mortgage metrics
    total_mortgages = Mortgage.query.count()

    # Trigger metrics
    total_triggers = Trigger.query.count()
    triggered_alerts = Trigger.query.filter_by(alert_trigger_status=1).count()

    # Recent triggers (last 7 days)
    recent_triggers = Trigger.query.filter(Trigger.created_on >= week_ago).count()

    # Email metrics
    total_emails = EmailLog.query.count()
    sent_emails = EmailLog.query.filter_by(status='sent').count()
    failed_emails = EmailLog.query.filter_by(status='failed').count()
    recent_emails = EmailLog.query.filter(EmailLog.created_on >= week_ago).count()

    # System status - latest mortgage rate update
    latest_rate = MortgageRate.query.order_by(MortgageRate.created_on.desc()).first()
    latest_rate_update = latest_rate.created_on if latest_rate else None

    # Recent users (last 10)
    recent_users = User.query.order_by(User.created_on.desc()).limit(10).all()

    return render_template(
        'admin_dashboard.jinja2',
        title='Admin Dashboard',
        template='admin-template',
        current_user=current_user,
        # User metrics
        total_users=total_users,
        verified_users=verified_users,
        unverified_users=unverified_users,
        new_users_week=new_users_week,
        # Subscription metrics
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        failed_subscriptions=failed_subscriptions,
        incomplete_subscriptions=incomplete_subscriptions,
        paused_subscriptions=paused_subscriptions,
        # Alert metrics
        total_alerts=total_alerts,
        deleted_alerts=deleted_alerts,
        # Mortgage metrics
        total_mortgages=total_mortgages,
        # Trigger metrics
        total_triggers=total_triggers,
        triggered_alerts=triggered_alerts,
        recent_triggers=recent_triggers,
        # Email metrics
        total_emails=total_emails,
        sent_emails=sent_emails,
        failed_emails=failed_emails,
        recent_emails=recent_emails,
        # System status
        latest_rate_update=latest_rate_update,
        # Recent data
        recent_users=recent_users,
    )


# ============================================================
# Health Check Endpoints - CI/CD Integration
# ============================================================

@main_bp.route("/health", methods=['GET'])
def health_check():
    """
    Health check endpoint for CI/CD deploy verification.
    Returns overall application health status.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': app.config.get('VERSION', '1.0.0'),
    }

    # Check database connectivity
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status['database'] = 'healthy'
    except Exception as e:
        health_status['database'] = 'unhealthy'
        health_status['database_error'] = str(e)
        health_status['status'] = 'degraded'

    # Check if scheduler is running
    try:
        from .scheduler import scheduler
        if scheduler and scheduler.running:
            health_status['scheduler'] = 'running'
        else:
            health_status['scheduler'] = 'stopped'
    except Exception:
        health_status['scheduler'] = 'unknown'

    http_status = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), http_status


@main_bp.route("/health/ready", methods=['GET'])
def readiness_check():
    """
    Readiness probe for container orchestration.
    Returns 200 only when app is ready to serve traffic.
    """
    try:
        # Verify database is accessible
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'ready': True}), 200
    except Exception as e:
        return jsonify({'ready': False, 'error': str(e)}), 503


@main_bp.route("/health/live", methods=['GET'])
def liveness_check():
    """
    Liveness probe for container orchestration.
    Returns 200 if the process is running.
    """
    return jsonify({'alive': True}), 200
