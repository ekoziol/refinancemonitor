"""REST API endpoints for React frontend."""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
from . import db
from .models import User, Mortgage, Alert, MortgageRate
from .calc import calc_loan_monthly_payment


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


@api_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    """Delete an alert."""
    alert = Alert.query.filter_by(id=alert_id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    mortgage = Mortgage.query.filter_by(id=alert.mortgage_id, user_id=current_user.id).first()
    if not mortgage:
        return jsonify({'error': 'Alert not found'}), 404

    db.session.delete(alert)
    db.session.commit()
    return jsonify({'message': 'Alert deleted successfully'})


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
