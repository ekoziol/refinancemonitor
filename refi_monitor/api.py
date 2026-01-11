"""REST API endpoints for calculator."""
from flask import Blueprint, request, jsonify
import numpy as np
from .calc import (
    calc_loan_monthly_payment,
    ipmt_total,
    time_to_even,
    find_target_interest_rate,
    calculate_recoup_data,
)

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')


@api_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    Calculate refinance savings.

    Request body:
    {
        "mortgage": {
            "originalPrincipal": number,
            "originalTerm": number (years),
            "originalInterestRate": number (percentage, e.g. 4.5 for 4.5%),
            "remainingPrincipal": number,
            "remainingTerm": number (months)
        },
        "refinance": {
            "targetTerm": number (years),
            "targetMonthlyPayment": number (optional),
            "targetInterestRate": number (percentage, optional),
            "estimatedRefinanceCost": number
        }
    }

    Response:
    {
        "originalMonthlyPayment": number,
        "minimumMonthlyPayment": number,
        "refiMonthlyPayment": number,
        "monthlySavings": number,
        "targetInterestRate": number (decimal),
        "originalInterest": number,
        "refiInterest": number,
        "totalLoanSavings": number,
        "monthsToBreakevenSimple": number,
        "monthsToBreakevenInterest": number | null,
        "additionalMonths": number,
        "cashRequired": number
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        mortgage = data.get('mortgage', {})
        refinance = data.get('refinance', {})

        # Extract and validate mortgage data
        original_principal = mortgage.get('originalPrincipal')
        original_term_years = mortgage.get('originalTerm')
        original_rate_pct = mortgage.get('originalInterestRate')
        remaining_principal = mortgage.get('remainingPrincipal')
        remaining_term_months = mortgage.get('remainingTerm')

        # Extract refinance data
        target_term_years = refinance.get('targetTerm')
        target_monthly_payment = refinance.get('targetMonthlyPayment')
        target_rate_pct = refinance.get('targetInterestRate')
        refi_cost = refinance.get('estimatedRefinanceCost', 0)

        # Validate required fields
        required = [
            ('originalPrincipal', original_principal),
            ('originalTerm', original_term_years),
            ('originalInterestRate', original_rate_pct),
            ('remainingPrincipal', remaining_principal),
            ('remainingTerm', remaining_term_months),
            ('targetTerm', target_term_years),
        ]

        missing = [name for name, value in required if value is None]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        # Convert to calculation units
        original_term = original_term_years * 12  # months
        original_rate = original_rate_pct / 100  # decimal
        target_term = target_term_years * 12  # months

        # Calculate target rate if payment specified, or vice versa
        if target_monthly_payment and not target_rate_pct:
            target_rate = find_target_interest_rate(
                remaining_principal, target_term, target_monthly_payment
            )
        elif target_rate_pct:
            target_rate = target_rate_pct / 100
        else:
            # Default to finding rate for a reasonable payment reduction
            original_payment = calc_loan_monthly_payment(
                original_principal, original_rate, original_term
            )
            target_rate = find_target_interest_rate(
                remaining_principal, target_term, original_payment * 0.9
            )

        # Calculate original monthly payment
        original_monthly_payment = calc_loan_monthly_payment(
            original_principal, original_rate, original_term
        )

        # Minimum monthly payment (0% interest)
        minimum_monthly_payment = calc_loan_monthly_payment(
            original_principal, 0.0, original_term
        )

        # Months already paid
        months_paid = original_term - remaining_term_months

        # Interest calculations
        original_interest = ipmt_total(original_rate, original_term, original_principal)
        refi_interest = ipmt_total(target_rate, target_term, remaining_principal)
        original_interest_to_date = ipmt_total(
            original_rate,
            original_term,
            original_principal,
            per=np.arange(0, months_paid) if months_paid > 0 else None
        )

        total_loan_savings = (
            original_interest
            - refi_interest
            - refi_cost
            - (original_interest_to_date if months_paid > 0 else 0)
        )

        # Refi monthly payment
        refi_monthly_payment = calc_loan_monthly_payment(
            remaining_principal, target_rate, target_term
        )

        # Monthly savings
        monthly_savings = original_monthly_payment - refi_monthly_payment

        # Months to break even (simple method)
        if monthly_savings > 0:
            months_to_breakeven_simple = int(time_to_even(refi_cost, monthly_savings))
        else:
            months_to_breakeven_simple = None

        # Calculate recoup data for interest-based breakeven
        recoup_data = calculate_recoup_data(
            original_monthly_payment,
            refi_monthly_payment,
            target_term,
            refi_cost,
            target_rate,
            remaining_principal,
            original_term,
            original_rate,
            original_principal,
            months_paid,
        )

        # Find interest-based breakeven month
        positive_savings = recoup_data.loc[recoup_data['interest_refi_savings'] > 0, 'month']
        months_to_breakeven_interest = int(positive_savings.min()) if not positive_savings.empty else None

        # Additional months beyond original payoff
        additional_months = target_term - remaining_term_months

        response = {
            'originalMonthlyPayment': round(original_monthly_payment, 2),
            'minimumMonthlyPayment': round(minimum_monthly_payment, 2),
            'refiMonthlyPayment': round(refi_monthly_payment, 2),
            'monthlySavings': round(monthly_savings, 2),
            'targetInterestRate': round(target_rate * 100, 3),  # Return as percentage
            'originalInterest': round(original_interest, 2),
            'refiInterest': round(refi_interest, 2),
            'totalLoanSavings': round(total_loan_savings, 2),
            'monthsToBreakevenSimple': months_to_breakeven_simple,
            'monthsToBreakevenInterest': months_to_breakeven_interest,
            'additionalMonths': additional_months,
            'cashRequired': round(refi_cost, 2),
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
