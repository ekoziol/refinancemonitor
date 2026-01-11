"""Routes for parent Flask app."""
import os
from flask import render_template, jsonify, request, flash
from flask import current_app as app
from flask import send_from_directory
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required, logout_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from .models import Mortgage, Alert, User
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


@main_bp.route("/unsubscribe/<token>", methods=['GET', 'POST'])
def unsubscribe(token):
    """
    Handle email unsubscribe requests.
    GET: Display unsubscribe confirmation page
    POST: Process the unsubscribe request
    """
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    try:
        # Token valid for 30 days
        email = serializer.loads(token, salt='unsubscribe', max_age=2592000)
    except SignatureExpired:
        return render_template(
            'emails/unsubscribe_error.html',
            error_type='expired',
            message='This unsubscribe link has expired. Please use the link from a more recent email.'
        )
    except BadSignature:
        return render_template(
            'emails/unsubscribe_error.html',
            error_type='invalid',
            message='This unsubscribe link is invalid.'
        )

    if request.method == 'POST':
        # Find user and deactivate their alerts
        user = User.query.filter_by(email=email).first()
        if user:
            # Deactivate all active alerts for this user
            alerts = Alert.query.filter_by(user_id=user.id).all()
            for alert in alerts:
                if alert.payment_status == 'active':
                    alert.payment_status = 'unsubscribed'
            db.session.commit()
            app.logger.info(f"User {email} unsubscribed from alerts")

        return render_template(
            'emails/unsubscribe_success.html',
            email=email
        )

    # GET request - show confirmation page
    return render_template(
        'emails/unsubscribe_confirm.html',
        email=email,
        token=token
    )
