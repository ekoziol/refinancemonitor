"""Routes for parent Flask app."""
import os
from flask import render_template, jsonify, request
from flask import current_app as app
from flask import send_from_directory
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required, logout_user
from . import db
from .models import Mortgage, Alert, User
from .plots import *
from .scheduler import trigger_manual_check
from .notifications import send_unsubscribe_confirmation

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
    Handle email unsubscribe requests via token.
    GET: Show confirmation page
    POST: Process unsubscribe
    """
    user = User.query.filter_by(unsubscribe_token=token).first()

    if not user:
        return render_template(
            'unsubscribe.jinja2',
            title='Invalid Link',
            error='This unsubscribe link is invalid or has expired.',
            success=False
        ), 404

    if request.method == 'POST':
        user.email_unsubscribed = True
        db.session.commit()
        send_unsubscribe_confirmation(user.id)
        return render_template(
            'unsubscribe.jinja2',
            title='Unsubscribed',
            success=True,
            user_email=user.email
        )

    return render_template(
        'unsubscribe.jinja2',
        title='Confirm Unsubscribe',
        success=False,
        confirm=True,
        user_email=user.email
    )


@main_bp.route("/resubscribe", methods=['POST'])
@login_required
def resubscribe():
    """
    Allow logged-in users to resubscribe to emails.
    """
    current_user.email_unsubscribed = False
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'You have been resubscribed to emails.'})
