"""Calculator API endpoints."""
from flask import jsonify, request, abort
from . import api_bp
from ..calc import (
    calc_loan_monthly_payment,
    create_efficient_frontier,
    find_break_even_interest,
    calculate_recoup_data,
    create_mortage_range,
    amount_remaining,
    time_to_even,
)


@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'refi_alert_api'})


@api_bp.route('/calculator/monthly-payment', methods=['POST'])
def monthly_payment():
    """Calculate monthly payment for a loan.

    Request body:
        principal: float - Loan principal amount
        rate: float - Annual interest rate (e.g., 0.065 for 6.5%)
        term: int - Loan term in months

    Returns:
        monthly_payment: float - Monthly payment amount
    """
    data = request.get_json()
    if not data:
        abort(400, description='Request body required')

    required = ['principal', 'rate', 'term']
    for field in required:
        if field not in data:
            abort(400, description=f'Missing required field: {field}')

    try:
        principal = float(data['principal'])
        rate = float(data['rate'])
        term = int(data['term'])
    except (ValueError, TypeError) as e:
        abort(422, description=f'Invalid data type: {e}')

    if principal <= 0:
        abort(422, description='Principal must be positive')
    if rate < 0:
        abort(422, description='Rate cannot be negative')
    if term <= 0:
        abort(422, description='Term must be positive')

    payment = calc_loan_monthly_payment(principal, rate, term)

    return jsonify({
        'monthly_payment': round(payment, 2),
        'input': {
            'principal': principal,
            'rate': rate,
            'term': term
        }
    })


@api_bp.route('/calculator/efficient-frontier', methods=['POST'])
def efficient_frontier():
    """Calculate the efficient frontier for refinancing.

    Request body:
        original_principal: float - Original loan principal
        original_rate: float - Original interest rate
        original_term: int - Original term in months
        current_principal: float - Current remaining principal
        term_remaining: int - Months remaining on current loan
        new_term: int - New loan term in months
        refi_cost: float - Cost of refinancing

    Returns:
        data: list - Efficient frontier data points
    """
    data = request.get_json()
    if not data:
        abort(400, description='Request body required')

    required = [
        'original_principal', 'original_rate', 'original_term',
        'current_principal', 'term_remaining', 'new_term', 'refi_cost'
    ]
    for field in required:
        if field not in data:
            abort(400, description=f'Missing required field: {field}')

    try:
        original_principal = float(data['original_principal'])
        original_rate = float(data['original_rate'])
        original_term = int(data['original_term'])
        current_principal = float(data['current_principal'])
        term_remaining = int(data['term_remaining'])
        new_term = int(data['new_term'])
        refi_cost = float(data['refi_cost'])
    except (ValueError, TypeError) as e:
        abort(422, description=f'Invalid data type: {e}')

    df = create_efficient_frontier(
        original_principal,
        original_rate,
        original_term,
        current_principal,
        term_remaining,
        new_term,
        refi_cost
    )

    result = df.to_dict(orient='records')

    return jsonify({
        'data': result,
        'input': {
            'original_principal': original_principal,
            'original_rate': original_rate,
            'original_term': original_term,
            'current_principal': current_principal,
            'term_remaining': term_remaining,
            'new_term': new_term,
            'refi_cost': refi_cost
        }
    })


@api_bp.route('/calculator/break-even-rate', methods=['POST'])
def break_even_rate():
    """Find the break-even interest rate.

    Request body:
        principal: float - Loan principal
        new_term: int - New term in months
        target: float - Target total interest
        current_rate: float - Current interest rate

    Returns:
        break_even_rate: float - Break-even interest rate
    """
    data = request.get_json()
    if not data:
        abort(400, description='Request body required')

    required = ['principal', 'new_term', 'target', 'current_rate']
    for field in required:
        if field not in data:
            abort(400, description=f'Missing required field: {field}')

    try:
        principal = float(data['principal'])
        new_term = int(data['new_term'])
        target = float(data['target'])
        current_rate = float(data['current_rate'])
    except (ValueError, TypeError) as e:
        abort(422, description=f'Invalid data type: {e}')

    rate = find_break_even_interest(principal, new_term, target, current_rate)

    return jsonify({
        'break_even_rate': rate,
        'input': {
            'principal': principal,
            'new_term': new_term,
            'target': target,
            'current_rate': current_rate
        }
    })


@api_bp.route('/calculator/recoup', methods=['POST'])
def recoup_data():
    """Calculate time to recoup refinancing costs.

    Request body:
        original_monthly_payment: float - Current monthly payment
        refi_monthly_payment: float - New monthly payment after refi
        target_term: int - Term to analyze in months
        refi_cost: float - Cost of refinancing

    Returns:
        data: list - Recoup data over time
        months_to_recoup: int - Months to break even on refi costs
    """
    data = request.get_json()
    if not data:
        abort(400, description='Request body required')

    required = ['original_monthly_payment', 'refi_monthly_payment', 'target_term', 'refi_cost']
    for field in required:
        if field not in data:
            abort(400, description=f'Missing required field: {field}')

    try:
        original_monthly_payment = float(data['original_monthly_payment'])
        refi_monthly_payment = float(data['refi_monthly_payment'])
        target_term = int(data['target_term'])
        refi_cost = float(data['refi_cost'])
    except (ValueError, TypeError) as e:
        abort(422, description=f'Invalid data type: {e}')

    monthly_savings = original_monthly_payment - refi_monthly_payment
    if monthly_savings <= 0:
        return jsonify({
            'data': [],
            'months_to_recoup': None,
            'message': 'No savings from refinancing',
            'input': {
                'original_monthly_payment': original_monthly_payment,
                'refi_monthly_payment': refi_monthly_payment,
                'target_term': target_term,
                'refi_cost': refi_cost
            }
        })

    df = calculate_recoup_data(
        original_monthly_payment,
        refi_monthly_payment,
        target_term,
        refi_cost
    )

    months_to_recoup = int(time_to_even(refi_cost, monthly_savings))

    return jsonify({
        'data': df.to_dict(orient='records'),
        'months_to_recoup': months_to_recoup,
        'monthly_savings': round(monthly_savings, 2),
        'input': {
            'original_monthly_payment': original_monthly_payment,
            'refi_monthly_payment': refi_monthly_payment,
            'target_term': target_term,
            'refi_cost': refi_cost
        }
    })


@api_bp.route('/calculator/amount-remaining', methods=['POST'])
def calc_amount_remaining():
    """Calculate remaining loan balance.

    Request body:
        principal: float - Original principal
        monthly_payment: float - Monthly payment amount
        rate: float - Annual interest rate
        months_remaining: int - Months remaining on loan

    Returns:
        amount_remaining: float - Remaining balance
    """
    data = request.get_json()
    if not data:
        abort(400, description='Request body required')

    required = ['principal', 'monthly_payment', 'rate', 'months_remaining']
    for field in required:
        if field not in data:
            abort(400, description=f'Missing required field: {field}')

    try:
        principal = float(data['principal'])
        monthly_payment = float(data['monthly_payment'])
        rate = float(data['rate'])
        months_remaining = int(data['months_remaining'])
    except (ValueError, TypeError) as e:
        abort(422, description=f'Invalid data type: {e}')

    remaining = amount_remaining(principal, monthly_payment, rate, months_remaining)

    return jsonify({
        'amount_remaining': round(remaining, 2),
        'input': {
            'principal': principal,
            'monthly_payment': monthly_payment,
            'rate': rate,
            'months_remaining': months_remaining
        }
    })
