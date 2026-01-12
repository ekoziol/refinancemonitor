"""Routes for parent Flask app."""
import os
from datetime import datetime, timedelta
from flask import render_template, jsonify
from flask import current_app as app
from flask import send_from_directory
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required, logout_user
from .models import Mortgage, Alert, MortgageRate
from .plots import *
from .scheduler import trigger_manual_check
from . import db
from sqlalchemy import func


def get_mortgage_overview(user_id):
    """
    Calculate overview metrics for the user's mortgages.

    Returns dict with:
        - total_mortgages: count of user's mortgages
        - total_principal: sum of remaining principal
        - avg_user_rate: average rate across user's mortgages
        - current_30yr_rate: latest 30-year market rate
        - current_15yr_rate: latest 15-year market rate
        - rate_change_30yr: change from previous rate (positive = up)
        - potential_savings: estimated monthly savings if refinancing
    """
    # Get user's mortgages
    mortgages = Mortgage.query.filter_by(user_id=user_id).all()

    if not mortgages:
        return None

    total_mortgages = len(mortgages)
    total_principal = sum(m.remaining_principal for m in mortgages)

    # Calculate weighted average rate (weighted by principal)
    weighted_rate_sum = sum(
        m.original_interest_rate * m.remaining_principal
        for m in mortgages
    )
    avg_user_rate = weighted_rate_sum / total_principal if total_principal > 0 else 0

    # Get latest market rates from MortgageRate table
    # Look for most recent 30-year (360 months) and 15-year (180 months) rates
    latest_30yr = MortgageRate.query.filter_by(term_months=360).order_by(
        MortgageRate.rate_date.desc()
    ).first()

    latest_15yr = MortgageRate.query.filter_by(term_months=180).order_by(
        MortgageRate.rate_date.desc()
    ).first()

    # Get previous 30yr rate for change calculation
    previous_30yr = None
    if latest_30yr:
        previous_30yr = MortgageRate.query.filter(
            MortgageRate.term_months == 360,
            MortgageRate.rate_date < latest_30yr.rate_date
        ).order_by(MortgageRate.rate_date.desc()).first()

    current_30yr_rate = latest_30yr.rate if latest_30yr else 0.0650  # Default fallback
    current_15yr_rate = latest_15yr.rate if latest_15yr else 0.0580  # Default fallback

    # Calculate rate change
    rate_change_30yr = 0
    if latest_30yr and previous_30yr:
        rate_change_30yr = latest_30yr.rate - previous_30yr.rate

    # Estimate potential savings (simplified calculation)
    # If user's average rate > current 30yr rate, calculate monthly savings
    potential_savings = 0
    if avg_user_rate > current_30yr_rate and total_principal > 0:
        # Simplified: savings = principal * (rate_diff / 12)
        rate_diff = avg_user_rate - current_30yr_rate
        potential_savings = total_principal * (rate_diff / 12)

    return {
        'total_mortgages': total_mortgages,
        'total_principal': total_principal,
        'avg_user_rate': avg_user_rate * 100,  # Convert to percentage
        'current_30yr_rate': current_30yr_rate * 100,
        'current_15yr_rate': current_15yr_rate * 100,
        'rate_change_30yr': rate_change_30yr * 100,  # basis points style
        'potential_savings': potential_savings,
        'rate_date': latest_30yr.rate_date if latest_30yr else None
    }

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

    # Get mortgage overview metrics
    overview = get_mortgage_overview(current_user.id)

    return render_template(
        'dashboard.jinja2',
        title='Refinance Monitor Dashboard',
        template='dashboard-template',
        current_user=current_user,
        body="Refinance Monitor Dashboard for " + current_user.name,
        mortgages=mortgages,
        alerts=alerts,
        mortgage_alerts=mortgage_alerts,
        overview=overview,
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


# React App Routes
# Serve the React SPA for /app and all sub-routes
@main_bp.route('/app')
@main_bp.route('/app/<path:path>')
@login_required
def react_app(path=None):
    """
    Serve React application.
    All /app/* routes return the React index.html for client-side routing.
    """
    react_build_dir = os.path.join(app.root_path, 'static', 'react')
    return send_from_directory(react_build_dir, 'index.html')
