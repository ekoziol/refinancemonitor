"""REST API endpoints for React frontend."""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from sqlalchemy import func
import stripe
from . import db
from .models import User, Mortgage, Alert, MortgageRate, EmailLog, Trigger, Subscription, UserPreference
from .calc import calc_loan_monthly_payment
from .scheduler import get_scheduler_status
from .notifications import send_cancellation_confirmation


api_bp = Blueprint('api_bp', __name__, url_prefix='/api')


def mortgage_to_dict(mortgage):
    """Convert Mortgage model to dictionary."""
    return {
        'id': mortgage.id,
        'user_id': mortgage.user_id,
        'name': mortgage.name,
        'zip_code': mortgage.zip_code,
        'original_principal': mortgage.original_principal,
        'original_term': mortgage.original_term,
        'original_interest_rate': mortgage.original_interest_rate,
        'remaining_principal': mortgage.remaining_principal,
        'remaining_term': mortgage.remaining_term,
        'credit_score': mortgage.credit_score,
        'created_on': mortgage.created_on.isoformat() if mortgage.created_on else None,
        'updated_on': mortgage.updated_on.isoformat() if mortgage.updated_on else None,
    }


def alert_to_dict(alert):
    """Convert Alert model to dictionary."""
    return {
        'id': alert.id,
        'user_id': alert.user_id,
        'mortgage_id': alert.mortgage_id,
        'alert_type': alert.alert_type,
        'target_monthly_payment': alert.target_monthly_payment,
        'target_interest_rate': alert.target_interest_rate,
        'target_term': alert.target_term,
        'estimate_refinance_cost': alert.estimate_refinance_cost,
        'calculated_refinance_cost': alert.calculated_refinance_cost,
        'payment_status': alert.payment_status,
        'status': alert.get_status(),
        'is_paused': alert.is_paused,
        'paused_at': alert.paused_at.isoformat() if alert.paused_at else None,
        'created_on': alert.created_on.isoformat() if alert.created_on else None,
        'updated_on': alert.updated_on.isoformat() if alert.updated_on else None,
    }


def user_to_dict(user):
    """Convert User model to dictionary (excluding sensitive fields)."""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'credit_score': user.credit_score,
        'created_on': user.created_on.isoformat() if user.created_on else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
    }


# ============ Mortgage Endpoints ============

@api_bp.route('/mortgages', methods=['GET'])
@login_required
def get_mortgages():
    """Get all mortgages for the current user."""
    mortgages = Mortgage.query.filter_by(user_id=current_user.id).all()
    return jsonify([mortgage_to_dict(m) for m in mortgages])


@api_bp.route('/mortgages/<int:mortgage_id>', methods=['GET'])
@login_required
def get_mortgage(mortgage_id):
    """Get a specific mortgage by ID."""
    mortgage = Mortgage.query.filter_by(id=mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Mortgage not found'}), 404
    return jsonify(mortgage_to_dict(mortgage))


@api_bp.route('/mortgages', methods=['POST'])
@login_required
def create_mortgage():
    """Create a new mortgage."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['name', 'zip_code', 'original_principal', 'original_term',
                       'original_interest_rate', 'remaining_principal', 'remaining_term',
                       'credit_score']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    mortgage = Mortgage(
        user_id=current_user.id,
        name=data['name'],
        zip_code=data['zip_code'],
        original_principal=data['original_principal'],
        original_term=data['original_term'],
        original_interest_rate=data['original_interest_rate'],
        remaining_principal=data['remaining_principal'],
        remaining_term=data['remaining_term'],
        credit_score=data['credit_score'],
        created_on=datetime.utcnow(),
        updated_on=datetime.utcnow(),
    )
    db.session.add(mortgage)
    db.session.commit()
    return jsonify(mortgage_to_dict(mortgage)), 201


@api_bp.route('/mortgages/<int:mortgage_id>', methods=['PUT'])
@login_required
def update_mortgage(mortgage_id):
    """Update an existing mortgage."""
    mortgage = Mortgage.query.filter_by(id=mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Mortgage not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    updatable_fields = ['name', 'zip_code', 'original_principal', 'original_term',
                        'original_interest_rate', 'remaining_principal', 'remaining_term',
                        'credit_score']
    for field in updatable_fields:
        if field in data:
            setattr(mortgage, field, data[field])

    mortgage.updated_on = datetime.utcnow()
    db.session.commit()
    return jsonify(mortgage_to_dict(mortgage))


@api_bp.route('/mortgages/<int:mortgage_id>', methods=['DELETE'])
@login_required
def delete_mortgage(mortgage_id):
    """Delete a mortgage."""
    mortgage = Mortgage.query.filter_by(id=mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Mortgage not found'}), 404

    db.session.delete(mortgage)
    db.session.commit()
    return jsonify({'message': 'Mortgage deleted successfully'})


# ============ Alert Endpoints ============

@api_bp.route('/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Get all alerts for the current user."""
    mortgages = Mortgage.query.filter_by(user_id=current_user.id).all()
    mortgage_ids = [m.id for m in mortgages]
    alerts = Alert.query.filter(Alert.mortgage_id.in_(mortgage_ids)).all()
    return jsonify([alert_to_dict(a) for a in alerts])


@api_bp.route('/alerts/<int:alert_id>', methods=['GET'])
@login_required
def get_alert(alert_id):
    """Get a specific alert by ID."""
    alert = Alert.query.filter_by(id=alert_id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    mortgage = Mortgage.query.filter_by(id=alert.mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Alert not found'}), 404

    return jsonify(alert_to_dict(alert))


@api_bp.route('/alerts', methods=['POST'])
@login_required
def create_alert():
    """Create a new alert."""
    # Block unverified users from creating alerts
    if not current_user.email_verified:
        return jsonify({
            'error': 'Email verification required',
            'message': 'Please verify your email address before creating alerts.'
        }), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['mortgage_id', 'alert_type', 'target_term', 'estimate_refinance_cost']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    mortgage = Mortgage.query.filter_by(id=data['mortgage_id'], user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Mortgage not found'}), 404

    alert = Alert(
        user_id=current_user.id,
        mortgage_id=data['mortgage_id'],
        alert_type=data['alert_type'],
        target_monthly_payment=data.get('target_monthly_payment'),
        target_interest_rate=data.get('target_interest_rate'),
        target_term=data['target_term'],
        estimate_refinance_cost=data['estimate_refinance_cost'],
        created_on=datetime.utcnow(),
        updated_on=datetime.utcnow(),
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify(alert_to_dict(alert)), 201


@api_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
@login_required
def update_alert(alert_id):
    """Update an existing alert."""
    alert = Alert.query.filter_by(id=alert_id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    mortgage = Mortgage.query.filter_by(id=alert.mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Alert not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    updatable_fields = ['alert_type', 'target_monthly_payment', 'target_interest_rate',
                        'target_term', 'estimate_refinance_cost']
    for field in updatable_fields:
        if field in data:
            setattr(alert, field, data[field])

    alert.updated_on = datetime.utcnow()
    db.session.commit()
    return jsonify(alert_to_dict(alert))


@api_bp.route('/alerts/<int:alert_id>', methods=['PATCH'])
@login_required
def patch_alert(alert_id):
    """Partially update an alert's threshold values.

    Accepts partial updates for threshold fields only:
    - target_monthly_payment
    - target_interest_rate
    - target_term
    - estimate_refinance_cost
    """
    alert = Alert.query.filter_by(id=alert_id, deleted_at=None).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    mortgage = Mortgage.query.filter_by(id=alert.mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Alert not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Only allow threshold fields to be updated via PATCH
    threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                        'target_term', 'estimate_refinance_cost']

    updated_fields = []
    for field in threshold_fields:
        if field in data:
            setattr(alert, field, data[field])
            updated_fields.append(field)

    if not updated_fields:
        return jsonify({'error': 'No valid threshold fields provided'}), 400

    alert.updated_on = datetime.utcnow()
    db.session.commit()

    return jsonify(alert_to_dict(alert))


@api_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    """Delete an alert by canceling the Stripe subscription and soft-deleting the record."""
    alert = Alert.query.filter_by(id=alert_id, deleted_at=None).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    mortgage = Mortgage.query.filter_by(id=alert.mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Alert not found'}), 404

    # Cancel Stripe subscription if exists
    subscription_id = alert.stripe_subscription_id or alert.stripe_invoice_id
    if subscription_id:
        try:
            stripe.Subscription.cancel(subscription_id)
        except stripe.error.InvalidRequestError as e:
            # Subscription may already be canceled or not exist
            print(f"Stripe subscription cancel error: {e}")
        except stripe.error.StripeError as e:
            print(f"Stripe error: {e}")
            return jsonify({'error': 'Error canceling subscription. Please try again.'}), 500

    # Soft delete the alert and update subscription status
    alert.deleted_at = datetime.utcnow()
    if alert.subscription:
        alert.subscription.payment_status = 'canceled'
        alert.subscription.updated_on = datetime.utcnow()
    db.session.commit()

    # Send cancellation confirmation email
    user = User.query.get(current_user.id)
    if user:
        send_cancellation_confirmation(user.email, alert_id)

    return jsonify({'message': 'Alert deleted successfully'})


@api_bp.route('/alerts/<int:alert_id>/pause', methods=['POST'])
@login_required
def pause_alert(alert_id):
    """Pause an alert to temporarily stop monitoring."""
    alert = Alert.query.filter_by(id=alert_id, deleted_at=None).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    mortgage = Mortgage.query.filter_by(id=alert.mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Alert not found'}), 404

    if alert.is_paused:
        return jsonify({'error': 'Alert is already paused'}), 400

    alert.paused_at = datetime.utcnow()
    alert.updated_on = datetime.utcnow()
    db.session.commit()

    return jsonify(alert_to_dict(alert))


@api_bp.route('/alerts/<int:alert_id>/resume', methods=['POST'])
@login_required
def resume_alert(alert_id):
    """Resume a paused alert to restart monitoring."""
    alert = Alert.query.filter_by(id=alert_id, deleted_at=None).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    mortgage = Mortgage.query.filter_by(id=alert.mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Alert not found'}), 404

    if not alert.is_paused:
        return jsonify({'error': 'Alert is not paused'}), 400

    alert.paused_at = None
    alert.updated_on = datetime.utcnow()
    db.session.commit()

    return jsonify(alert_to_dict(alert))


# ============ User Endpoints ============

@api_bp.route('/user', methods=['GET'])
@login_required
def get_user():
    """Get current user information."""
    return jsonify(user_to_dict(current_user))


@api_bp.route('/user', methods=['PUT'])
@login_required
def update_user():
    """Update current user information."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    updatable_fields = ['name', 'credit_score']
    for field in updatable_fields:
        if field in data:
            setattr(current_user, field, data[field])

    current_user.updated_on = datetime.utcnow()
    db.session.commit()
    return jsonify(user_to_dict(current_user))


# ============ KPI Metrics Endpoints ============

def calculate_refi_score(user_rate, market_rate, monthly_savings, remaining_term):
    """
    Calculate a refinance score from 0-100 based on potential savings.

    Score factors:
    - Rate differential (40%): Higher difference = better score
    - Monthly savings (30%): Higher savings = better score
    - Remaining term (30%): Longer term = more benefit from refi

    Returns score 0-100 where higher is better opportunity to refinance.
    """
    if user_rate <= market_rate:
        return 0  # No benefit if user rate is already at or below market

    score = 0

    # Rate differential component (0-40 points)
    rate_diff = user_rate - market_rate
    rate_diff_pct = min(rate_diff / 0.02, 1.0)  # Cap at 2% difference
    score += rate_diff_pct * 40

    # Monthly savings component (0-30 points)
    if monthly_savings > 0:
        savings_pct = min(monthly_savings / 500, 1.0)  # Cap at $500/month savings
        score += savings_pct * 30

    # Remaining term component (0-30 points)
    term_pct = min(remaining_term / 360, 1.0)  # Cap at 30 years
    score += term_pct * 30

    return round(score)


@api_bp.route('/kpi-metrics', methods=['GET'])
@login_required
def get_kpi_metrics():
    """
    Get KPI metrics for the dashboard: market rate, user rate, savings, refi score.

    Query params:
    - mortgage_id (optional): Specific mortgage to calculate metrics for.
                              If not provided, uses first mortgage.

    Returns:
    {
        "market_rate": 0.0294,
        "market_rate_display": "2.94%",
        "your_rate": 0.045,
        "your_rate_display": "4.50%",
        "monthly_savings": 250.50,
        "monthly_savings_display": "$250.50",
        "refi_score": 75,
        "refi_score_label": "Good"
    }
    """
    mortgage_id = request.args.get('mortgage_id', type=int)

    # Get mortgage
    if mortgage_id:
        mortgage = Mortgage.query.filter_by(
            id=mortgage_id, user_id=current_user.id
        ).first()
    else:
        mortgage = Mortgage.query.filter_by(user_id=current_user.id).first()

    if not mortgage:
        return jsonify({
            'market_rate': None,
            'market_rate_display': '--',
            'your_rate': None,
            'your_rate_display': '--',
            'monthly_savings': None,
            'monthly_savings_display': '--',
            'refi_score': None,
            'refi_score_label': 'N/A'
        })

    # Get market rate (latest 30-year rate or default)
    latest_rate = MortgageRate.query.filter_by(
        term_months=360
    ).order_by(MortgageRate.rate_date.desc()).first()

    market_rate = latest_rate.rate if latest_rate else 0.0294  # Default 2.94%

    # User's current rate
    your_rate = mortgage.original_interest_rate

    # Calculate monthly payments
    current_payment = calc_loan_monthly_payment(
        mortgage.remaining_principal,
        your_rate,
        mortgage.remaining_term
    )
    market_payment = calc_loan_monthly_payment(
        mortgage.remaining_principal,
        market_rate,
        mortgage.remaining_term
    )

    monthly_savings = max(0, current_payment - market_payment)

    # Calculate refi score
    refi_score = calculate_refi_score(
        your_rate, market_rate, monthly_savings, mortgage.remaining_term
    )

    # Score labels
    if refi_score >= 70:
        score_label = 'Excellent'
    elif refi_score >= 50:
        score_label = 'Good'
    elif refi_score >= 30:
        score_label = 'Fair'
    else:
        score_label = 'Low'

    return jsonify({
        'market_rate': market_rate,
        'market_rate_display': f'{market_rate * 100:.2f}%',
        'your_rate': your_rate,
        'your_rate_display': f'{your_rate * 100:.2f}%',
        'monthly_savings': round(monthly_savings, 2),
        'monthly_savings_display': f'${monthly_savings:,.2f}',
        'refi_score': refi_score,
        'refi_score_label': score_label,
        'mortgage_id': mortgage.id,
        'mortgage_name': mortgage.name
    })


# ============ Timeline Endpoints ============

@api_bp.route('/timeline', methods=['GET'])
@login_required
def get_timeline():
    """
    Get timeline data for visualization showing mortgage events and rate forecast.

    Query params:
    - mortgage_id (optional): Specific mortgage to get timeline for.
                              If not provided, uses first mortgage.
    - forecast_days (optional): Number of days to forecast (default 30)

    Returns:
    {
        "events": [
            {"date": "2025-01-15", "type": "mortgage_created", "label": "Mortgage Created", "value": null},
            {"date": "2025-02-01", "type": "alert_created", "label": "Alert Set", "value": 3.5},
            {"date": "2025-02-10", "type": "trigger", "label": "Rate Target Met", "value": 3.2},
            ...
        ],
        "rate_history": [
            {"date": "2025-01-01", "rate": 6.5},
            {"date": "2025-01-02", "rate": 6.48},
            ...
        ],
        "forecast": [
            {"date": "2025-02-15", "rate": 6.3, "upper": 6.5, "lower": 6.1},
            ...
        ],
        "target_rate": 5.5
    }
    """
    import numpy as np
    from datetime import timedelta

    mortgage_id = request.args.get('mortgage_id', type=int)
    forecast_days = request.args.get('forecast_days', default=30, type=int)

    # Get mortgage
    if mortgage_id:
        mortgage = Mortgage.query.filter_by(
            id=mortgage_id, user_id=current_user.id
        ).first()
    else:
        mortgage = Mortgage.query.filter_by(user_id=current_user.id).first()

    if not mortgage:
        return jsonify({
            'events': [],
            'rate_history': [],
            'forecast': [],
            'target_rate': None
        })

    events = []

    # Add mortgage creation event
    if mortgage.created_on:
        events.append({
            'date': mortgage.created_on.strftime('%Y-%m-%d'),
            'type': 'mortgage_created',
            'label': 'Mortgage Created',
            'description': f'{mortgage.name} - ${mortgage.original_principal:,.0f}',
            'value': None
        })

    # Get alerts and their triggers
    alerts = Alert.query.filter_by(
        mortgage_id=mortgage.id, deleted_at=None
    ).all()

    for alert in alerts:
        if alert.created_on:
            target_val = alert.target_interest_rate or alert.target_monthly_payment
            events.append({
                'date': alert.created_on.strftime('%Y-%m-%d'),
                'type': 'alert_created',
                'label': 'Alert Set',
                'description': f'Target: {alert.target_interest_rate}%' if alert.target_interest_rate else f'Target: ${alert.target_monthly_payment:,.0f}/mo',
                'value': target_val
            })

        # Get triggers for this alert
        from .models import Trigger
        triggers = Trigger.query.filter_by(alert_id=alert.id).all()
        for trigger in triggers:
            if trigger.alert_trigger_date and trigger.alert_trigger_status == 1:
                events.append({
                    'date': trigger.alert_trigger_date.strftime('%Y-%m-%d'),
                    'type': 'trigger',
                    'label': 'Rate Target Met',
                    'description': trigger.alert_trigger_reason or 'Target achieved',
                    'value': None
                })

    # Get rate history
    rate_history = []
    historical_rates = MortgageRate.query.filter_by(
        zip_code=mortgage.zip_code,
        term_months=mortgage.original_term
    ).order_by(MortgageRate.rate_date).all()

    for rate_record in historical_rates:
        rate_history.append({
            'date': rate_record.rate_date.strftime('%Y-%m-%d'),
            'rate': round(rate_record.rate * 100, 3)  # Convert to percentage
        })

    # Generate forecast if we have rate history
    forecast = []
    if len(rate_history) >= 2:
        # Convert to numeric for regression
        import pandas as pd
        df = pd.DataFrame(rate_history)
        df['date'] = pd.to_datetime(df['date'])
        df['day_num'] = (df['date'] - df['date'].min()).dt.days

        # Linear regression
        coeffs = np.polyfit(df['day_num'], df['rate'], 1)
        slope, intercept = coeffs

        # Calculate residual std for confidence interval
        predicted = slope * df['day_num'] + intercept
        residuals = df['rate'] - predicted
        std_dev = residuals.std()

        # Generate forecast points
        last_date = df['date'].max()
        last_day_num = df['day_num'].max()

        for i in range(1, forecast_days + 1):
            forecast_date = last_date + timedelta(days=i)
            day_num = last_day_num + i
            rate = slope * day_num + intercept

            forecast.append({
                'date': forecast_date.strftime('%Y-%m-%d'),
                'rate': round(rate, 3),
                'upper': round(rate + 1.96 * std_dev, 3),
                'lower': round(rate - 1.96 * std_dev, 3)
            })

    # Get target rate from active alert if exists
    target_rate = None
    active_alert = Alert.query.filter_by(
        mortgage_id=mortgage.id,
        deleted_at=None
    ).first()
    if active_alert and active_alert.target_interest_rate:
        target_rate = active_alert.target_interest_rate

    # Sort events by date
    events.sort(key=lambda x: x['date'])

    return jsonify({
        'events': events,
        'rate_history': rate_history,
        'forecast': forecast,
        'target_rate': target_rate,
        'mortgage_id': mortgage.id,
        'mortgage_name': mortgage.name
    })


# ============ Savings Impact Endpoints ============

@api_bp.route('/savings-impact', methods=['GET'])
@login_required
def get_savings_impact():
    """
    Get savings impact data comparing current mortgage vs refinance scenario.

    Query params:
    - mortgage_id (optional): Specific mortgage to calculate for.
                              If not provided, uses first mortgage.
    - target_rate (optional): Target refinance rate. Defaults to current market rate.
    - target_term (optional): Target refinance term in months. Defaults to remaining term.
    - refi_cost (optional): Estimated refinance closing costs. Defaults to 5000.

    Returns:
    {
        "savings_data": [
            {"month": 0, "cumulative_savings": -5000, "monthly_diff": 200},
            {"month": 1, "cumulative_savings": -4800, "monthly_diff": 200},
            ...
        ],
        "summary": {
            "current_payment": 2015.11,
            "refi_payment": 1815.11,
            "monthly_savings": 200.00,
            "breakeven_month": 25,
            "total_savings_at_term": 67000,
            "refi_cost": 5000
        },
        "mortgage_id": 1,
        "mortgage_name": "Primary Home"
    }
    """
    mortgage_id = request.args.get('mortgage_id', type=int)
    target_rate = request.args.get('target_rate', type=float)
    target_term = request.args.get('target_term', type=int)
    refi_cost = request.args.get('refi_cost', default=5000, type=float)

    # Get mortgage
    if mortgage_id:
        mortgage = Mortgage.query.filter_by(
            id=mortgage_id, user_id=current_user.id
        ).first()
    else:
        mortgage = Mortgage.query.filter_by(user_id=current_user.id).first()

    if not mortgage:
        return jsonify({
            'savings_data': [],
            'summary': None,
            'mortgage_id': None,
            'mortgage_name': None
        })

    # Get market rate if target_rate not provided
    if target_rate is None:
        latest_rate = MortgageRate.query.filter_by(
            term_months=360
        ).order_by(MortgageRate.rate_date.desc()).first()
        target_rate = latest_rate.rate if latest_rate else 0.0294

    # Use remaining term if target_term not provided
    if target_term is None:
        target_term = mortgage.remaining_term

    # Calculate current and refinance payments
    current_payment = calc_loan_monthly_payment(
        mortgage.remaining_principal,
        mortgage.original_interest_rate,
        mortgage.remaining_term
    )

    refi_payment = calc_loan_monthly_payment(
        mortgage.remaining_principal,
        target_rate,
        target_term
    )

    monthly_diff = current_payment - refi_payment

    # Generate savings data points
    savings_data = []
    breakeven_month = None

    for month in range(0, target_term + 1):
        cumulative_savings = (monthly_diff * month) - refi_cost

        savings_data.append({
            'month': month,
            'cumulative_savings': round(cumulative_savings, 2),
            'monthly_diff': round(monthly_diff, 2)
        })

        # Find breakeven month
        if breakeven_month is None and cumulative_savings >= 0:
            breakeven_month = month

    # Calculate total savings at end of term
    total_savings_at_term = (monthly_diff * target_term) - refi_cost

    summary = {
        'current_payment': round(current_payment, 2),
        'refi_payment': round(refi_payment, 2),
        'monthly_savings': round(monthly_diff, 2),
        'breakeven_month': breakeven_month,
        'total_savings_at_term': round(total_savings_at_term, 2),
        'refi_cost': refi_cost,
        'current_rate': mortgage.original_interest_rate,
        'target_rate': target_rate,
        'target_term': target_term
    }

    return jsonify({
        'savings_data': savings_data,
        'summary': summary,
        'mortgage_id': mortgage.id,
        'mortgage_name': mortgage.name
    })


# ============ System Health Endpoints ============

@api_bp.route('/system-health', methods=['GET'])
@login_required
def get_system_health():
    """
    Get system health metrics for the admin dashboard.

    Returns rate fetch status, email delivery rates, and error logs.
    """
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Rate fetch status from scheduler
    scheduler_jobs = get_scheduler_status()

    # Email delivery stats
    email_stats_24h = _get_email_stats(day_ago)
    email_stats_7d = _get_email_stats(week_ago)
    email_stats_30d = _get_email_stats(month_ago)

    # Recent errors (failed emails)
    recent_errors = EmailLog.query.filter(
        EmailLog.status == 'failed'
    ).order_by(EmailLog.created_on.desc()).limit(20).all()

    error_logs = [{
        'id': e.id,
        'email_type': e.email_type,
        'recipient': e.recipient_email,
        'subject': e.subject,
        'error_message': e.error_message,
        'created_on': e.created_on.isoformat() if e.created_on else None
    } for e in recent_errors]

    # Alert statistics
    alert_stats = _get_alert_stats()

    # Trigger statistics
    trigger_stats = _get_trigger_stats(day_ago, week_ago, month_ago)

    return jsonify({
        'scheduler_jobs': scheduler_jobs,
        'email_stats': {
            '24h': email_stats_24h,
            '7d': email_stats_7d,
            '30d': email_stats_30d
        },
        'error_logs': error_logs,
        'alert_stats': alert_stats,
        'trigger_stats': trigger_stats,
        'generated_at': now.isoformat()
    })


def _get_email_stats(since):
    """Get email statistics since a given datetime."""
    total = EmailLog.query.filter(EmailLog.created_on >= since).count()
    sent = EmailLog.query.filter(
        EmailLog.status == 'sent',
        EmailLog.created_on >= since
    ).count()
    failed = EmailLog.query.filter(
        EmailLog.status == 'failed',
        EmailLog.created_on >= since
    ).count()
    pending = EmailLog.query.filter(
        EmailLog.status == 'pending',
        EmailLog.created_on >= since
    ).count()

    # By type breakdown
    by_type = db.session.query(
        EmailLog.email_type,
        func.count(EmailLog.id)
    ).filter(
        EmailLog.created_on >= since
    ).group_by(EmailLog.email_type).all()

    success_rate = round((sent / total * 100), 1) if total > 0 else 0

    return {
        'total': total,
        'sent': sent,
        'failed': failed,
        'pending': pending,
        'success_rate': success_rate,
        'by_type': {t: c for t, c in by_type}
    }


def _get_alert_stats():
    """Get current alert status distribution."""
    # Total alerts (not deleted)
    total_alerts = Alert.query.filter(Alert.deleted_at.is_(None)).count()

    # Active (paid, not paused)
    active_alerts = Alert.query.join(Subscription).filter(
        Subscription.payment_status == 'active',
        Alert.deleted_at.is_(None),
        Alert.paused_at.is_(None)
    ).count()

    # Paused
    paused_alerts = Alert.query.filter(
        Alert.deleted_at.is_(None),
        Alert.paused_at.isnot(None)
    ).count()

    # Waiting for payment
    waiting_alerts = Alert.query.join(Subscription).filter(
        Alert.deleted_at.is_(None),
        Subscription.initial_payment == False
    ).count()

    return {
        'total': total_alerts,
        'active': active_alerts,
        'paused': paused_alerts,
        'waiting': waiting_alerts
    }


def _get_trigger_stats(day_ago, week_ago, month_ago):
    """Get trigger statistics for different time periods."""
    triggers_24h = Trigger.query.filter(
        Trigger.created_on >= day_ago,
        Trigger.alert_trigger_status == 1
    ).count()

    triggers_7d = Trigger.query.filter(
        Trigger.created_on >= week_ago,
        Trigger.alert_trigger_status == 1
    ).count()

    triggers_30d = Trigger.query.filter(
        Trigger.created_on >= month_ago,
        Trigger.alert_trigger_status == 1
    ).count()

    return {
        '24h': triggers_24h,
        '7d': triggers_7d,
        '30d': triggers_30d
    }


# ============ Rates Endpoints ============

@api_bp.route('/rates/current', methods=['GET'])
@login_required
def get_current_rates():
    """
    Get current mortgage rates.

    Query params:
    - zip_code (optional): Filter by zip code. If not provided, uses user's first mortgage zip.
    - term_months (optional): Filter by term (e.g., 180 for 15-year, 360 for 30-year).
                              If not provided, returns all available terms.

    Returns:
    {
        "rates": [
            {"term_months": 180, "term_years": 15, "rate": 0.055, "rate_display": "5.50%", "rate_date": "2026-01-18"},
            {"term_months": 360, "term_years": 30, "rate": 0.0625, "rate_display": "6.25%", "rate_date": "2026-01-18"}
        ],
        "zip_code": "12345",
        "as_of": "2026-01-18T10:00:00"
    }
    """
    zip_code = request.args.get('zip_code')
    term_months = request.args.get('term_months', type=int)

    # If no zip code, get from user's first mortgage
    if not zip_code:
        mortgage = Mortgage.query.filter_by(user_id=current_user.id).first()
        if mortgage:
            zip_code = mortgage.zip_code
        else:
            return jsonify({
                'rates': [],
                'zip_code': None,
                'as_of': datetime.utcnow().isoformat(),
                'message': 'No mortgage found to determine zip code'
            })

    # Build query
    query = MortgageRate.query.filter_by(zip_code=zip_code)
    if term_months:
        query = query.filter_by(term_months=term_months)

    # Get latest rate for each term
    subquery = db.session.query(
        MortgageRate.term_months,
        func.max(MortgageRate.rate_date).label('max_date')
    ).filter_by(zip_code=zip_code)

    if term_months:
        subquery = subquery.filter_by(term_months=term_months)

    subquery = subquery.group_by(MortgageRate.term_months).subquery()

    rates = MortgageRate.query.join(
        subquery,
        db.and_(
            MortgageRate.term_months == subquery.c.term_months,
            MortgageRate.rate_date == subquery.c.max_date,
            MortgageRate.zip_code == zip_code
        )
    ).order_by(MortgageRate.term_months).all()

    rate_list = []
    for rate in rates:
        rate_list.append({
            'term_months': rate.term_months,
            'term_years': rate.term_months // 12,
            'rate': rate.rate,
            'rate_display': f'{rate.rate * 100:.2f}%',
            'rate_date': rate.rate_date.strftime('%Y-%m-%d') if rate.rate_date else None
        })

    return jsonify({
        'rates': rate_list,
        'zip_code': zip_code,
        'as_of': datetime.utcnow().isoformat()
    })


@api_bp.route('/rates/history', methods=['GET'])
@login_required
def get_rate_history():
    """
    Get historical mortgage rate data.

    Query params:
    - zip_code (optional): Filter by zip code. If not provided, uses user's first mortgage zip.
    - term_months (required): Loan term in months (e.g., 360 for 30-year).
    - days (optional): Number of days of history to return (default: 30, max: 365).

    Returns:
    {
        "history": [
            {"date": "2026-01-15", "rate": 0.0625, "rate_display": "6.25%"},
            {"date": "2026-01-16", "rate": 0.062, "rate_display": "6.20%"},
            ...
        ],
        "statistics": {
            "current_rate": 0.062,
            "min_rate": 0.058,
            "max_rate": 0.065,
            "avg_rate": 0.061,
            "change": -0.005,
            "change_display": "-0.50%",
            "data_points": 30
        },
        "zip_code": "12345",
        "term_months": 360
    }
    """
    zip_code = request.args.get('zip_code')
    term_months = request.args.get('term_months', type=int)
    days = request.args.get('days', default=30, type=int)

    # Validate days
    days = min(max(1, days), 365)

    # If no zip code, get from user's first mortgage
    if not zip_code:
        mortgage = Mortgage.query.filter_by(user_id=current_user.id).first()
        if mortgage:
            zip_code = mortgage.zip_code
        else:
            return jsonify({
                'history': [],
                'statistics': None,
                'zip_code': None,
                'term_months': term_months,
                'message': 'No mortgage found to determine zip code'
            })

    # Default to 30-year if not specified
    if not term_months:
        term_months = 360

    # Get historical rates
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    rates = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.term_months == term_months,
        MortgageRate.rate_date >= cutoff_date
    ).order_by(MortgageRate.rate_date.asc()).all()

    if not rates:
        return jsonify({
            'history': [],
            'statistics': None,
            'zip_code': zip_code,
            'term_months': term_months,
            'message': 'No rate data available for this zip code and term'
        })

    # Build history list
    history = []
    for rate in rates:
        history.append({
            'date': rate.rate_date.strftime('%Y-%m-%d') if rate.rate_date else None,
            'rate': rate.rate,
            'rate_display': f'{rate.rate * 100:.2f}%'
        })

    # Calculate statistics
    rate_values = [r.rate for r in rates]
    current_rate = rates[-1].rate
    oldest_rate = rates[0].rate
    rate_change = current_rate - oldest_rate

    statistics = {
        'current_rate': current_rate,
        'min_rate': min(rate_values),
        'max_rate': max(rate_values),
        'avg_rate': round(sum(rate_values) / len(rate_values), 5),
        'change': round(rate_change, 5),
        'change_display': f'{rate_change * 100:+.2f}%',
        'data_points': len(rates)
    }

    return jsonify({
        'history': history,
        'statistics': statistics,
        'zip_code': zip_code,
        'term_months': term_months
    })


# ============ Report Preview Endpoint ============

@api_bp.route('/report-preview', methods=['GET'])
@login_required
def get_report_preview():
    """
    Get a preview of the user's refinancing report.

    Query params:
    - mortgage_id (optional): Specific mortgage to generate report for.
                              If not provided, includes all mortgages.

    Returns:
    {
        "user": {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com"
        },
        "generated_at": "2026-01-18T10:00:00",
        "mortgages": [
            {
                "id": 1,
                "name": "Primary Home",
                "zip_code": "12345",
                "original_principal": 300000,
                "original_rate": 0.065,
                "remaining_principal": 275000,
                "remaining_term": 300,
                "current_monthly_payment": 1896.20
            }
        ],
        "rate_statistics": {
            "180": {
                "current_rate": 0.055,
                "min_rate": 0.052,
                "max_rate": 0.058,
                "avg_rate": 0.055,
                "rate_change_30d": -0.003,
                "data_points": 30
            },
            "360": {...}
        },
        "savings_opportunities": [
            {
                "mortgage_id": 1,
                "mortgage_name": "Primary Home",
                "term_months": 360,
                "term_years": 30,
                "current_rate": 0.058,
                "new_monthly_payment": 1650.50,
                "monthly_savings": 245.70,
                "total_interest_savings": 45000,
                "break_even_months": 12,
                "refi_cost": 3000,
                "rate_trend": "down",
                "rate_change_30d": -0.003
            }
        ]
    }
    """
    from .report_aggregator import ReportDataAggregationService

    mortgage_id = request.args.get('mortgage_id', type=int)

    # Generate report
    service = ReportDataAggregationService(days=30)

    if mortgage_id:
        # Verify mortgage belongs to user
        mortgage = Mortgage.query.filter_by(
            id=mortgage_id, user_id=current_user.id
        ).first()
        if not mortgage:
            return jsonify({'error': 'Mortgage not found'}), 404

        # Get status for specific mortgage
        mortgage_status = service.get_mortgage_status(mortgage)
        mortgages = [mortgage_status]

        # Get rate stats for this mortgage's zip
        rate_stats = service.aggregate_rate_data_bulk(mortgage.zip_code)

        # Find opportunities
        opportunities = service.find_savings_opportunities(mortgage_status, rate_stats)
        for opp in opportunities:
            opp['mortgage_id'] = mortgage.id
            opp['mortgage_name'] = mortgage.name

        user_data = {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email
        }
    else:
        # Generate full report
        report = service.generate_user_report(current_user.id)
        if not report:
            return jsonify({
                'user': {
                    'id': current_user.id,
                    'name': current_user.name,
                    'email': current_user.email
                },
                'generated_at': datetime.utcnow().isoformat(),
                'mortgages': [],
                'rate_statistics': {},
                'savings_opportunities': []
            })

        mortgages = report.mortgages
        rate_stats = report.rate_statistics
        opportunities = report.savings_opportunities
        user_data = {
            'id': report.user_id,
            'name': report.user_name,
            'email': report.user_email
        }

    # Format mortgages for response
    mortgage_list = []
    for m in mortgages:
        mortgage_list.append({
            'id': m.mortgage_id,
            'name': m.name,
            'zip_code': m.zip_code,
            'original_principal': m.original_principal,
            'original_rate': m.original_rate,
            'original_term': m.original_term,
            'remaining_principal': m.remaining_principal,
            'remaining_term': m.remaining_term,
            'current_monthly_payment': round(m.current_monthly_payment, 2),
            'current_rate': m.current_rate
        })

    # Format rate statistics for response
    rate_stats_dict = {}
    for term, stats in rate_stats.items():
        rate_stats_dict[str(term)] = {
            'current_rate': stats.current_rate,
            'min_rate': stats.min_rate,
            'max_rate': stats.max_rate,
            'avg_rate': round(stats.avg_rate, 5),
            'rate_change_30d': round(stats.rate_change_30d, 5),
            'data_points': stats.data_points
        }

    # Format savings opportunities for response
    savings_list = []
    for opp in opportunities:
        savings = opp.get('savings')
        if savings:
            savings_list.append({
                'mortgage_id': opp.get('mortgage_id'),
                'mortgage_name': opp.get('mortgage_name'),
                'term_months': opp.get('term_months'),
                'term_years': opp.get('term_years'),
                'current_rate': opp.get('current_rate'),
                'new_monthly_payment': round(savings.new_monthly_payment, 2),
                'monthly_savings': round(savings.monthly_savings, 2),
                'total_interest_savings': round(savings.total_interest_savings, 2),
                'break_even_months': savings.break_even_months,
                'refi_cost': savings.refi_cost,
                'rate_trend': opp.get('rate_trend'),
                'rate_change_30d': opp.get('rate_change_30d')
            })

    return jsonify({
        'user': user_data,
        'generated_at': datetime.utcnow().isoformat(),
        'mortgages': mortgage_list,
        'rate_statistics': rate_stats_dict,
        'savings_opportunities': savings_list
    })


# ============ User Preferences Endpoints ============

def preference_to_dict(preference):
    """Convert UserPreference model to dictionary."""
    return {
        'id': preference.id,
        'user_id': preference.user_id,
        'monthly_report_enabled': preference.monthly_report_enabled,
        'weekly_digest_enabled': preference.weekly_digest_enabled,
        'theme': preference.theme,
        'created_on': preference.created_on.isoformat() if preference.created_on else None,
        'updated_on': preference.updated_on.isoformat() if preference.updated_on else None,
    }


@api_bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get current user preferences. Creates default preferences if none exist."""
    preference = UserPreference.query.filter_by(user_id=current_user.id).first()

    if not preference:
        preference = UserPreference(
            user_id=current_user.id,
            monthly_report_enabled=True,
            weekly_digest_enabled=False,
            theme='light',
            created_on=datetime.utcnow(),
            updated_on=datetime.utcnow()
        )
        db.session.add(preference)
        db.session.commit()

    return jsonify(preference_to_dict(preference))


@api_bp.route('/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Update current user preferences."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    preference = UserPreference.query.filter_by(user_id=current_user.id).first()

    if not preference:
        preference = UserPreference(
            user_id=current_user.id,
            created_on=datetime.utcnow()
        )
        db.session.add(preference)

    updatable_fields = ['monthly_report_enabled', 'weekly_digest_enabled', 'theme']
    for field in updatable_fields:
        if field in data:
            if field == 'theme' and data[field] not in ['light', 'dark', 'system']:
                return jsonify({'error': 'Invalid theme value. Must be light, dark, or system.'}), 400
            setattr(preference, field, data[field])

    preference.updated_on = datetime.utcnow()
    db.session.commit()
    return jsonify(preference_to_dict(preference))
