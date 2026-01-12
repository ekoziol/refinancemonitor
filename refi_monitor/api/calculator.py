"""Calculator API endpoints."""
from flask import jsonify, request
from marshmallow import ValidationError
from . import api_bp
from .schemas import (
    MonthlyPaymentRequestSchema,
    EfficientFrontierRequestSchema,
    BreakEvenRateRequestSchema,
    RecoupRequestSchema,
    AmountRemainingRequestSchema,
)
from ..calc import (
    calc_loan_monthly_payment,
    create_efficient_frontier,
    find_break_even_interest,
    calculate_recoup_data,
    amount_remaining,
    time_to_even,
)


def validate_request(schema_class):
    """Validate request JSON against a Marshmallow schema.

    Returns tuple of (validated_data, error_response).
    If validation succeeds, error_response is None.
    If validation fails, validated_data is None.
    """
    data = request.get_json()
    if not data:
        return None, (jsonify({
            'error': 'Bad Request',
            'message': 'Request body required'
        }), 400)

    schema = schema_class()
    try:
        validated = schema.load(data)
        return validated, None
    except ValidationError as err:
        return None, (jsonify({
            'error': 'Validation Error',
            'message': 'Invalid request data',
            'details': err.messages
        }), 400)


@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'refi_alert_api'})


@api_bp.route('/calculator/monthly-payment', methods=['POST'])
def monthly_payment():
    """Calculate monthly payment for a loan.

    Request body:
        principal: float - Loan principal amount (> 0)
        rate: float - Annual interest rate (0-0.99, e.g., 0.065 for 6.5%)
        term: int - Loan term in months (1-480)

    Returns:
        monthly_payment: float - Monthly payment amount
    """
    validated, error = validate_request(MonthlyPaymentRequestSchema)
    if error:
        return error

    principal = validated['principal']
    rate = validated['rate']
    term = validated['term']

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
        original_principal: float - Original loan principal (> 0)
        original_rate: float - Original interest rate (0-0.99)
        original_term: int - Original term in months (1-480)
        current_principal: float - Current remaining principal (> 0)
        term_remaining: int - Months remaining on current loan (1-480)
        new_term: int - New loan term in months (1-480)
        refi_cost: float - Cost of refinancing (>= 0)

    Returns:
        data: list - Efficient frontier data points
    """
    validated, error = validate_request(EfficientFrontierRequestSchema)
    if error:
        return error

    original_principal = validated['original_principal']
    original_rate = validated['original_rate']
    original_term = validated['original_term']
    current_principal = validated['current_principal']
    term_remaining = validated['term_remaining']
    new_term = validated['new_term']
    refi_cost = validated['refi_cost']

    # Business logic validation
    if current_principal > original_principal:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Current principal cannot exceed original principal'
        }), 422

    if term_remaining > original_term:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Term remaining cannot exceed original term'
        }), 422

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
        principal: float - Loan principal (> 0)
        new_term: int - New term in months (1-480)
        target: float - Target total interest (>= 0)
        current_rate: float - Current interest rate (0-0.99)

    Returns:
        break_even_rate: float - Break-even interest rate
    """
    validated, error = validate_request(BreakEvenRateRequestSchema)
    if error:
        return error

    principal = validated['principal']
    new_term = validated['new_term']
    target = validated['target']
    current_rate = validated['current_rate']

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
        original_monthly_payment: float - Current monthly payment (> 0)
        refi_monthly_payment: float - New monthly payment after refi (> 0)
        target_term: int - Term to analyze in months (1-480)
        refi_cost: float - Cost of refinancing (>= 0)

    Returns:
        data: list - Recoup data over time
        months_to_recoup: int - Months to break even on refi costs
        monthly_savings: float - Monthly savings amount
    """
    validated, error = validate_request(RecoupRequestSchema)
    if error:
        return error

    original_monthly_payment = validated['original_monthly_payment']
    refi_monthly_payment = validated['refi_monthly_payment']
    target_term = validated['target_term']
    refi_cost = validated['refi_cost']

    monthly_savings = original_monthly_payment - refi_monthly_payment

    # Business logic: no savings case
    if monthly_savings <= 0:
        return jsonify({
            'data': [],
            'months_to_recoup': None,
            'monthly_savings': round(monthly_savings, 2),
            'message': 'No savings from refinancing - new payment is higher or equal',
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
        principal: float - Original principal (> 0)
        monthly_payment: float - Monthly payment amount (> 0)
        rate: float - Annual interest rate (0.001-0.99)
        months_remaining: int - Months remaining on loan (0-480)

    Returns:
        amount_remaining: float - Remaining balance
    """
    validated, error = validate_request(AmountRemainingRequestSchema)
    if error:
        return error

    principal = validated['principal']
    monthly_payment = validated['monthly_payment']
    rate = validated['rate']
    months_remaining = validated['months_remaining']

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
