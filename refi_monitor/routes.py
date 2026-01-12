"""Routes for parent Flask app."""
import os
from functools import wraps
from flask import render_template, jsonify, abort
from flask import current_app as app
from flask import send_from_directory
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required, logout_user
from .models import Mortgage, Alert, Trigger
from .plots import *
from .scheduler import trigger_manual_check


def admin_required(f):
    """Decorator to require admin privileges for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def get_user_notifications(user_id, limit=10):
    """
    Fetch recent notifications/triggers for a user.

    Args:
        user_id: The user's ID
        limit: Maximum number of notifications to return

    Returns:
        List of notification dictionaries
    """
    # Get user's mortgages and alerts
    mortgages = Mortgage.query.filter_by(user_id=user_id).all()
    mortgage_ids = [m.id for m in mortgages]

    if not mortgage_ids:
        return []

    # Get alerts for these mortgages
    alerts = Alert.query.filter(Alert.mortgage_id.in_(mortgage_ids)).all()
    alert_ids = [a.id for a in alerts]

    if not alert_ids:
        return []

    # Get triggers (notifications) for these alerts
    triggers = Trigger.query.filter(
        Trigger.alert_id.in_(alert_ids)
    ).order_by(Trigger.created_on.desc()).limit(limit).all()

    notifications = []
    for trigger in triggers:
        alert = Alert.query.get(trigger.alert_id)
        mortgage = Mortgage.query.get(alert.mortgage_id) if alert else None

        notifications.append({
            'type': 'trigger',
            'title': f'Alert Triggered: {mortgage.name if mortgage else "Unknown"}',
            'message': trigger.alert_trigger_reason,
            'date': trigger.alert_trigger_date.strftime('%b %d, %Y at %I:%M %p') if trigger.alert_trigger_date else 'N/A',
            'is_new': trigger.alert_trigger_status == 1,  # Assuming 1 = new/unread
            'trigger_id': trigger.id,
            'alert_id': trigger.alert_id
        })

    return notifications


def get_alerts_summary(user_id):
    """
    Get summary counts of user's alerts.

    Args:
        user_id: The user's ID

    Returns:
        Dictionary with active, triggered, and inactive counts
    """
    mortgages = Mortgage.query.filter_by(user_id=user_id).all()
    mortgage_ids = [m.id for m in mortgages]

    if not mortgage_ids:
        return {'active': 0, 'triggered': 0, 'inactive': 0}

    alerts = Alert.query.filter(Alert.mortgage_id.in_(mortgage_ids)).all()

    active = 0
    triggered = 0
    inactive = 0

    for alert in alerts:
        if alert.payment_status == 'active':
            # Check if this alert has been triggered
            trigger_count = Trigger.query.filter_by(alert_id=alert.id).count()
            if trigger_count > 0:
                triggered += 1
            else:
                active += 1
        else:
            inactive += 1

    return {'active': active, 'triggered': triggered, 'inactive': inactive}

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
    alerts = Alert.query.filter(
        Alert.mortgage_id.in_([m.id for m in mortgages]), Alert.initial_payment == True
    )

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

    # Get notification center data
    notifications = get_user_notifications(current_user.id)
    alerts_summary = get_alerts_summary(current_user.id)

    return render_template(
        'dashboard.jinja2',
        title='Refinance Monitor Dashboard',
        template='dashboard-template',
        current_user=current_user,
        body="Refinance Monitor Dashboard for " + current_user.name,
        mortgages=mortgages,
        alerts=alerts,
        mortgage_alerts=mortgage_alerts,
        notifications=notifications,
        alerts_summary=alerts_summary,
    )


@main_bp.route('/v2', methods=['GET'])
@login_required
def dashboard_v2():
    """Modern Dashboard V2 - New layout with component structure."""
    mortgages = Mortgage.query.filter_by(user_id=current_user.id)
    alerts = Alert.query.filter(
        Alert.mortgage_id.in_([m.id for m in mortgages]), Alert.initial_payment == True
    )

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
        'dashboard_v2.jinja2',
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
    alerts = Alert.query.filter(
        Alert.mortgage_id.in_([m.id for m in mortgages]), Alert.initial_payment == True
    )

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


@main_bp.route("/api/notifications", methods=['GET'])
@login_required
def api_notifications():
    """
    API endpoint to fetch user notifications.
    Returns JSON data for AJAX updates to the notification center.
    """
    notifications = get_user_notifications(current_user.id)
    alerts_summary = get_alerts_summary(current_user.id)

    return jsonify({
        'status': 'success',
        'notifications': notifications,
        'alerts_summary': alerts_summary
    }), 200


@main_bp.route("/admin/trigger-alerts", methods=['POST'])
@login_required
@admin_required
def admin_trigger_alerts():
    """
    Admin endpoint to manually trigger alert checks.
    Requires admin privileges.
    """
    try:
        result = trigger_manual_check()
        return jsonify({'status': 'success', 'message': result}), 200
    except Exception as e:
        app.logger.error(f"Admin trigger-alerts failed: {e}")
        return jsonify({'status': 'error', 'message': 'Alert check failed'}), 500
