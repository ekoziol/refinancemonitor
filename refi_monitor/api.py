"""API endpoints for dashboard integration with rate tracking and calculator."""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from .models import Mortgage, Mortgage_Tracking, Alert, MortgageRate
from .rate_updater import RateFetcher
from . import calc
from . import db

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')


# Rate Tracking Endpoints

@api_bp.route('/rates/current', methods=['GET'])
@login_required
def get_current_rates():
    """
    Get current mortgage rates.

    Returns all available rate types (30 YR FRM, 15 YR FRM, etc.)
    """
    try:
        fetcher = RateFetcher()
        rates = fetcher.fetch_current_rates()
        return jsonify({
            'status': 'success',
            'data': {
                'rates': rates,
                'fetched_at': datetime.utcnow().isoformat()
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/rates/history', methods=['GET'])
@login_required
def get_rate_history():
    """
    Get historical mortgage rates.

    Query params:
        - zip_code: Optional zip code filter
        - term_months: Optional term filter (360 for 30yr, 180 for 15yr)
        - days: Number of days of history (default 30, max 365)
    """
    zip_code = request.args.get('zip_code')
    term_months = request.args.get('term_months', type=int)
    days = min(request.args.get('days', 30, type=int), 365)

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = MortgageRate.query.filter(MortgageRate.rate_date >= cutoff_date)

    if zip_code:
        query = query.filter(MortgageRate.zip_code == zip_code)
    if term_months:
        query = query.filter(MortgageRate.term_months == term_months)

    rates = query.order_by(MortgageRate.rate_date.desc()).all()

    return jsonify({
        'status': 'success',
        'data': {
            'rates': [
                {
                    'zip_code': r.zip_code,
                    'term_months': r.term_months,
                    'rate': r.rate,
                    'rate_date': r.rate_date.isoformat()
                }
                for r in rates
            ],
            'count': len(rates),
            'days': days
        }
    }), 200


@api_bp.route('/rates/user-tracking', methods=['GET'])
@login_required
def get_user_rate_tracking():
    """
    Get rate tracking data for the current user's mortgages.
    """
    mortgages = Mortgage.query.filter_by(user_id=current_user.id).all()

    tracking_data = []
    for mortgage in mortgages:
        latest_tracking = Mortgage_Tracking.query.filter_by(
            mortgage_id=mortgage.id
        ).order_by(Mortgage_Tracking.updated_on.desc()).first()

        tracking_data.append({
            'mortgage_id': mortgage.id,
            'mortgage_name': mortgage.name,
            'original_rate': mortgage.original_interest_rate,
            'current_rate': latest_tracking.current_rate if latest_tracking else None,
            'remaining_principal': latest_tracking.current_remaining_principal if latest_tracking else mortgage.remaining_principal,
            'remaining_term': latest_tracking.current_remaining_term if latest_tracking else mortgage.remaining_term,
            'last_updated': latest_tracking.updated_on.isoformat() if latest_tracking else None
        })

    return jsonify({
        'status': 'success',
        'data': {
            'tracking': tracking_data,
            'count': len(tracking_data)
        }
    }), 200


# Calculator Endpoints

@api_bp.route('/calculator/monthly-payment', methods=['POST'])
@login_required
def calculate_monthly_payment():
    """
    Calculate monthly mortgage payment.

    Request body:
        - principal: Loan principal amount
        - rate: Annual interest rate (as decimal, e.g., 0.065 for 6.5%)
        - term: Loan term in months
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Request body required'
        }), 400

    required_fields = ['principal', 'rate', 'term']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400

    try:
        principal = float(data['principal'])
        rate = float(data['rate'])
        term = int(data['term'])

        monthly_payment = calc.calc_loan_monthly_payment(principal, rate, term)
        total_payment = calc.total_payment(monthly_payment, term)
        total_interest = total_payment - principal

        return jsonify({
            'status': 'success',
            'data': {
                'monthly_payment': round(monthly_payment, 2),
                'total_payment': round(total_payment, 2),
                'total_interest': round(total_interest, 2),
                'principal': principal,
                'rate': rate,
                'term': term
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/calculator/target-rate', methods=['POST'])
@login_required
def calculate_target_rate():
    """
    Find the interest rate needed to achieve a target monthly payment.

    Request body:
        - principal: Loan principal amount
        - term: Loan term in months
        - target_payment: Desired monthly payment
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Request body required'
        }), 400

    required_fields = ['principal', 'term', 'target_payment']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400

    try:
        principal = float(data['principal'])
        term = int(data['term'])
        target_payment = float(data['target_payment'])

        target_rate = calc.find_target_interest_rate(principal, term, target_payment)

        return jsonify({
            'status': 'success',
            'data': {
                'target_rate': round(target_rate, 5),
                'target_rate_percent': round(target_rate * 100, 3),
                'principal': principal,
                'term': term,
                'target_payment': target_payment
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/calculator/savings-projection', methods=['POST'])
@login_required
def calculate_savings_projection():
    """
    Calculate potential savings from refinancing.

    Request body:
        - original_principal: Original loan amount
        - original_rate: Original interest rate
        - original_term: Original term in months
        - remaining_principal: Current remaining principal
        - remaining_term: Remaining months on original loan
        - new_rate: New interest rate for refinancing
        - new_term: New loan term in months
        - refi_cost: Estimated refinancing costs
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Request body required'
        }), 400

    required_fields = [
        'original_principal', 'original_rate', 'original_term',
        'remaining_principal', 'remaining_term',
        'new_rate', 'new_term', 'refi_cost'
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400

    try:
        original_principal = float(data['original_principal'])
        original_rate = float(data['original_rate'])
        original_term = int(data['original_term'])
        remaining_principal = float(data['remaining_principal'])
        remaining_term = int(data['remaining_term'])
        new_rate = float(data['new_rate'])
        new_term = int(data['new_term'])
        refi_cost = float(data['refi_cost'])

        # Calculate current monthly payment
        current_monthly = calc.calc_loan_monthly_payment(
            original_principal, original_rate, original_term
        )

        # Calculate new monthly payment
        new_monthly = calc.calc_loan_monthly_payment(
            remaining_principal, new_rate, new_term
        )

        # Monthly savings
        monthly_savings = current_monthly - new_monthly

        # Time to break even
        if monthly_savings > 0:
            break_even_months = calc.time_to_even(refi_cost, monthly_savings)
        else:
            break_even_months = None

        # Total remaining cost on current loan
        total_remaining_current = current_monthly * remaining_term

        # Total cost of new loan
        total_new = new_monthly * new_term + refi_cost

        # Lifetime savings (comparing remaining current vs new)
        lifetime_savings = total_remaining_current - total_new

        # Calculate recoup timeline
        recoup_data = calc.calculate_recoup_data(
            current_monthly, new_monthly, new_term, refi_cost
        )

        return jsonify({
            'status': 'success',
            'data': {
                'current_monthly_payment': round(current_monthly, 2),
                'new_monthly_payment': round(new_monthly, 2),
                'monthly_savings': round(monthly_savings, 2),
                'break_even_months': int(break_even_months) if break_even_months else None,
                'total_remaining_current': round(total_remaining_current, 2),
                'total_new_loan_cost': round(total_new, 2),
                'lifetime_savings': round(lifetime_savings, 2),
                'refi_cost': refi_cost,
                'recoup_timeline': recoup_data[['month', 'monthly_savings']].to_dict('records')
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/calculator/amortization', methods=['POST'])
@login_required
def calculate_amortization():
    """
    Generate amortization schedule for a loan.

    Request body:
        - principal: Loan principal amount
        - rate: Annual interest rate (as decimal)
        - term: Loan term in months
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Request body required'
        }), 400

    required_fields = ['principal', 'rate', 'term']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400

    try:
        principal = float(data['principal'])
        rate = float(data['rate'])
        term = int(data['term'])

        # Create mortgage table
        df = calc.create_mortgage_table(principal, rate, term)
        monthly_payment = calc.calc_loan_monthly_payment(principal, rate, term)

        # Convert to list of records, limiting to reasonable size
        # For full term, sample every 12 months for 30-year loans
        if term > 120:
            # Sample annually for long-term loans
            schedule = df[df['month'] % 12 == 0].to_dict('records')
        else:
            schedule = df.to_dict('records')

        return jsonify({
            'status': 'success',
            'data': {
                'monthly_payment': round(monthly_payment, 2),
                'schedule': schedule,
                'principal': principal,
                'rate': rate,
                'term': term
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Dashboard Summary Endpoint

@api_bp.route('/dashboard/summary', methods=['GET'])
@login_required
def get_dashboard_summary():
    """
    Get comprehensive dashboard summary for current user.

    Returns mortgage overview, current rates, alerts status, and potential savings.
    """
    try:
        # Get user's mortgages
        mortgages = Mortgage.query.filter_by(user_id=current_user.id).all()

        # Get current rates
        fetcher = RateFetcher()
        current_rates = fetcher.fetch_current_rates()
        primary_rate = current_rates.get('30 YR FRM', 0)

        # Get alerts status
        mortgage_ids = [m.id for m in mortgages]
        alerts = Alert.query.filter(
            Alert.mortgage_id.in_(mortgage_ids),
            Alert.payment_status == 'paid'
        ).all()

        # Build mortgage summaries with savings potential
        mortgage_summaries = []
        total_potential_savings = 0

        for mortgage in mortgages:
            # Calculate current monthly payment
            current_monthly = calc.calc_loan_monthly_payment(
                mortgage.original_principal,
                mortgage.original_interest_rate,
                mortgage.original_term
            )

            # Calculate potential new payment at current rate
            if primary_rate < mortgage.original_interest_rate:
                potential_monthly = calc.calc_loan_monthly_payment(
                    mortgage.remaining_principal,
                    primary_rate,
                    mortgage.remaining_term
                )
                monthly_savings = current_monthly - potential_monthly
                annual_savings = monthly_savings * 12
            else:
                potential_monthly = current_monthly
                monthly_savings = 0
                annual_savings = 0

            total_potential_savings += annual_savings

            # Get associated alerts
            mortgage_alerts = [a for a in alerts if a.mortgage_id == mortgage.id]

            mortgage_summaries.append({
                'id': mortgage.id,
                'name': mortgage.name,
                'original_principal': mortgage.original_principal,
                'original_rate': mortgage.original_interest_rate,
                'remaining_principal': mortgage.remaining_principal,
                'remaining_term': mortgage.remaining_term,
                'current_monthly_payment': round(current_monthly, 2),
                'potential_monthly_payment': round(potential_monthly, 2),
                'potential_monthly_savings': round(monthly_savings, 2),
                'potential_annual_savings': round(annual_savings, 2),
                'active_alerts': len(mortgage_alerts),
                'should_refinance': monthly_savings > 100  # Simple threshold
            })

        return jsonify({
            'status': 'success',
            'data': {
                'user': {
                    'name': current_user.name,
                    'email': current_user.email
                },
                'current_rates': current_rates,
                'primary_rate': primary_rate,
                'mortgages': mortgage_summaries,
                'total_mortgages': len(mortgages),
                'total_active_alerts': len(alerts),
                'total_potential_annual_savings': round(total_potential_savings, 2),
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
