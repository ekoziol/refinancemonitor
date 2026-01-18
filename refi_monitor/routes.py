"""Routes for parent Flask app."""
import os
import time
from flask import render_template, jsonify
from flask import current_app as app
from flask import send_from_directory
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required, logout_user
from .models import Mortgage, Alert
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
