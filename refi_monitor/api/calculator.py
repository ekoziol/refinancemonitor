"""Calculator API endpoints - mirrors Dash calculator functionality."""
from flask import jsonify, request
from . import api_bp
from ..calc import (
    calc_loan_monthly_payment,
    ipmt_total,
    time_to_even,
    find_target_interest_rate,
    create_mortage_range,
    create_efficient_frontier,
    get_per,
)
import numpy as np
import pandas as pd


def calculate_recoup_data_extended(
    original_monthly_payment,
    refi_monthly_payment,
    target_term,
    refi_cost,
    target_rate,
    remaining_principal,
    current_term,
    current_rate,
    current_principal,
    months_paid,
):
    """
    Extended recoup data calculation matching Dash behavior.

    Calculates both simple monthly savings and interest-based savings
    over the life of the refinanced loan.
    """
    df = pd.DataFrame({"month": range(0, target_term + 1)})

    # Simple monthly savings (difference in payments minus refi cost)
    df['monthly_savings'] = (original_monthly_payment - refi_monthly_payment) * df['month'] - refi_cost

    # Calculate interest savings over time
    # Original total interest over full loan
    original_total_interest = ipmt_total(current_rate, current_term, current_principal)

    # Interest already paid on original loan
    if months_paid > 0:
        original_interest_to_date = ipmt_total(
            current_rate,
            current_term,
            current_principal,
            per=np.arange(1, months_paid + 1)
        )
    else:
        original_interest_to_date = 0

    # For each month of the refi loan, calculate cumulative interest savings
    def calc_interest_savings_at_month(month):
        if month == 0:
            return -refi_cost - original_interest_to_date

        # Interest paid on refi loan up to this month
        refi_interest_to_month = ipmt_total(
            target_rate,
            target_term,
            remaining_principal,
            per=np.arange(1, min(month + 1, target_term + 1))
        )

        # Interest that would have been paid on original loan for same period
        # (from months_paid to months_paid + month)
        if months_paid + month <= current_term:
            original_interest_for_period = ipmt_total(
                current_rate,
                current_term,
                current_principal,
                per=np.arange(months_paid + 1, months_paid + month + 1)
            )
        else:
            original_interest_for_period = ipmt_total(
                current_rate,
                current_term,
                current_principal,
                per=np.arange(months_paid + 1, current_term + 1)
            )

        # Net savings = what we would have paid - what we actually paid - refi cost
        return original_interest_for_period - refi_interest_to_month - refi_cost - original_interest_to_date

    df['interest_refi_savings'] = df['month'].apply(calc_interest_savings_at_month)

    return df


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'calculator-api'})


@api_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    Main calculator endpoint - mirrors Dash update_data_stores callback.

    Request body:
    {
        "current_principal": float,      # Original loan principal
        "current_rate": float,           # Original interest rate (decimal, e.g., 0.045 = 4.5%)
        "current_term": int,             # Original term in months
        "target_rate": float,            # Target refinance rate (decimal)
        "target_term": int,              # Target refinance term in months
        "target_monthly_payment": float, # Target monthly payment (optional)
        "refi_cost": float,              # Refinancing costs
        "remaining_term": int,           # Remaining months on current loan
        "remaining_principal": float     # Current remaining principal
    }

    Returns all calculated values matching Dash data stores.
    """
    data = request.get_json()

    # Validate required fields
    required = [
        'current_principal', 'current_rate', 'current_term',
        'target_rate', 'target_term', 'refi_cost',
        'remaining_term', 'remaining_principal'
    ]

    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing required fields: {missing}'}), 400

    # Extract values
    current_principal = float(data['current_principal'])
    current_rate = float(data['current_rate'])
    current_term = int(data['current_term'])
    target_rate = float(data['target_rate'])
    target_term = int(data['target_term'])
    refi_cost = float(data['refi_cost'])
    remaining_term = int(data['remaining_term'])
    remaining_principal = float(data['remaining_principal'])

    # Calculate all values (mirrors Dash update_data_stores)
    original_monthly_payment = calc_loan_monthly_payment(
        current_principal, current_rate, current_term
    )

    minimum_monthly_payment = calc_loan_monthly_payment(
        current_principal, 0.0, current_term
    )

    months_paid = current_term - remaining_term

    original_interest = ipmt_total(current_rate, current_term, current_principal)
    refi_interest = ipmt_total(target_rate, target_term, remaining_principal)

    if months_paid > 0:
        original_interest_to_date = ipmt_total(
            current_rate,
            current_term,
            current_principal,
            per=np.arange(1, months_paid + 1)
        )
    else:
        original_interest_to_date = 0

    total_loan_savings = (
        original_interest
        - refi_interest
        - refi_cost
        - original_interest_to_date
    )

    refi_monthly_payment = calc_loan_monthly_payment(
        remaining_principal, target_rate, target_term
    )

    monthly_savings = original_monthly_payment - refi_monthly_payment

    # Handle edge case where monthly_savings is 0 or negative
    if monthly_savings > 0:
        month_to_even_simple = float(time_to_even(refi_cost, monthly_savings))
    else:
        month_to_even_simple = float('inf')

    # Calculate recoup data with interest savings
    recoup_data = calculate_recoup_data_extended(
        original_monthly_payment,
        refi_monthly_payment,
        target_term,
        refi_cost,
        target_rate,
        remaining_principal,
        current_term,
        current_rate,
        current_principal,
        months_paid,
    )

    # Find month to break even on interest
    positive_months = recoup_data.loc[recoup_data["interest_refi_savings"] > 0, 'month']
    if len(positive_months) > 0:
        month_to_even_interest = int(positive_months.min())
    else:
        month_to_even_interest = None  # Not possible

    # Build response
    response = {
        'original_monthly_payment': round(original_monthly_payment, 2),
        'minimum_monthly_payment': round(minimum_monthly_payment, 2),
        'monthly_savings': round(monthly_savings, 2),
        'total_loan_savings': round(total_loan_savings, 2),
        'months_paid': months_paid,
        'original_interest': round(original_interest, 2),
        'refi_monthly_payment': round(refi_monthly_payment, 2),
        'refi_interest': round(refi_interest, 2),
        'month_to_even_simple': month_to_even_simple if month_to_even_simple != float('inf') else None,
        'month_to_even_interest': month_to_even_interest,
        'target_rate': target_rate,
    }

    return jsonify(response)


@api_bp.route('/monthly-payment', methods=['POST'])
def monthly_payment():
    """
    Calculate monthly payment for a loan.

    Request body:
    {
        "principal": float,
        "rate": float,      # Annual rate as decimal (0.045 = 4.5%)
        "term": int         # Term in months
    }
    """
    data = request.get_json()

    required = ['principal', 'rate', 'term']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing required fields: {missing}'}), 400

    payment = calc_loan_monthly_payment(
        float(data['principal']),
        float(data['rate']),
        int(data['term'])
    )

    return jsonify({
        'monthly_payment': round(payment, 2),
        'principal': float(data['principal']),
        'rate': float(data['rate']),
        'term': int(data['term'])
    })


@api_bp.route('/find-rate', methods=['POST'])
def find_rate():
    """
    Find interest rate needed for target monthly payment.

    Request body:
    {
        "principal": float,
        "term": int,              # Term in months
        "target_payment": float
    }
    """
    data = request.get_json()

    required = ['principal', 'term', 'target_payment']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing required fields: {missing}'}), 400

    rate = find_target_interest_rate(
        float(data['principal']),
        int(data['term']),
        float(data['target_payment'])
    )

    return jsonify({
        'target_rate': round(float(rate), 5),
        'target_rate_percent': round(float(rate) * 100, 3),
        'principal': float(data['principal']),
        'term': int(data['term']),
        'target_payment': float(data['target_payment'])
    })


@api_bp.route('/total-interest', methods=['POST'])
def total_interest():
    """
    Calculate total interest over life of loan.

    Request body:
    {
        "principal": float,
        "rate": float,      # Annual rate as decimal
        "term": int         # Term in months
    }
    """
    data = request.get_json()

    required = ['principal', 'rate', 'term']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing required fields: {missing}'}), 400

    interest = ipmt_total(
        float(data['rate']),
        int(data['term']),
        float(data['principal'])
    )

    return jsonify({
        'total_interest': round(interest, 2),
        'principal': float(data['principal']),
        'rate': float(data['rate']),
        'term': int(data['term'])
    })


@api_bp.route('/breakeven', methods=['POST'])
def breakeven():
    """
    Calculate months to break even on refinance costs.

    Request body:
    {
        "refi_cost": float,
        "monthly_savings": float
    }
    """
    data = request.get_json()

    required = ['refi_cost', 'monthly_savings']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing required fields: {missing}'}), 400

    cost = float(data['refi_cost'])
    savings = float(data['monthly_savings'])

    if savings <= 0:
        return jsonify({
            'months_to_breakeven': None,
            'message': 'No positive savings - breakeven not possible',
            'refi_cost': cost,
            'monthly_savings': savings
        })

    months = time_to_even(cost, savings)

    return jsonify({
        'months_to_breakeven': int(months),
        'refi_cost': cost,
        'monthly_savings': savings
    })
