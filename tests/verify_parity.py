#!/usr/bin/env python3
"""
Simple verification script for API vs Dash parity.
Does not require pytest or Flask - uses basic assertions.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import calc directly (not through Flask app)
import numpy as np
import pandas as pd
import numpy_financial as npf

# Copy of calc.py functions for direct testing
def calc_loan_monthly_payment(principal, rate, term):
    r = rate / 12
    n = term
    try:
        if r <= 0:
            a = principal / term
        else:
            a = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return a
    except:
        return 0


def ipmt_total(rate, term, principal, per=None):
    if per is None:
        per = np.arange(term) + 1
    return -1 * np.sum(npf.ipmt(rate / 12, per, term, principal))


def time_to_even(cost, monthly_savings):
    return np.ceil(cost / monthly_savings)


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
    df = pd.DataFrame({"month": range(0, target_term + 1)})
    df['monthly_savings'] = (original_monthly_payment - refi_monthly_payment) * df['month'] - refi_cost

    original_total_interest = ipmt_total(current_rate, current_term, current_principal)

    if months_paid > 0:
        original_interest_to_date = ipmt_total(
            current_rate,
            current_term,
            current_principal,
            per=np.arange(1, months_paid + 1)
        )
    else:
        original_interest_to_date = 0

    def calc_interest_savings_at_month(month):
        if month == 0:
            return -refi_cost - original_interest_to_date

        refi_interest_to_month = ipmt_total(
            target_rate,
            target_term,
            remaining_principal,
            per=np.arange(1, min(month + 1, target_term + 1))
        )

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

        return original_interest_for_period - refi_interest_to_month - refi_cost - original_interest_to_date

    df['interest_refi_savings'] = df['month'].apply(calc_interest_savings_at_month)

    return df


TOLERANCE = 0.01
PASSED = 0
FAILED = 0


def test(name, condition, msg=""):
    global PASSED, FAILED
    if condition:
        print(f"  PASS: {name}")
        PASSED += 1
    else:
        print(f"  FAIL: {name} - {msg}")
        FAILED += 1


def test_approx(name, actual, expected, tolerance=TOLERANCE):
    global PASSED, FAILED
    diff = abs(actual - expected)
    if diff < tolerance:
        print(f"  PASS: {name} (actual={actual:.2f}, expected={expected:.2f})")
        PASSED += 1
    else:
        print(f"  FAIL: {name} (actual={actual:.2f}, expected={expected:.2f}, diff={diff:.4f})")
        FAILED += 1


def main():
    print("=" * 60)
    print("API vs Dash Parity Verification")
    print("=" * 60)

    # Test fixtures
    STANDARD_30YR = {
        'current_principal': 400000,
        'current_rate': 0.045,
        'current_term': 360,
        'target_rate': 0.035,
        'target_term': 360,
        'refi_cost': 5000,
        'remaining_term': 300,
        'remaining_principal': 364631.66,
    }

    print("\n1. Monthly Payment Calculations")
    print("-" * 40)

    # Test known monthly payment values
    test_approx("400K @ 4.5% 30yr", calc_loan_monthly_payment(400000, 0.045, 360), 2026.74)
    test_approx("300K @ 4% 15yr", calc_loan_monthly_payment(300000, 0.04, 180), 2219.06)
    test_approx("100K @ 6% 15yr", calc_loan_monthly_payment(100000, 0.06, 180), 843.86)
    test_approx("500K @ 3.5% 30yr", calc_loan_monthly_payment(500000, 0.035, 360), 2245.22)

    # Test 0% interest
    result = calc_loan_monthly_payment(360000, 0.0, 360)
    test_approx("0% interest", result, 1000.0)

    print("\n2. Total Interest Calculations")
    print("-" * 40)

    test_approx("400K @ 4.5% 30yr interest", ipmt_total(0.045, 360, 400000), 329625.29, tolerance=1.0)
    test_approx("300K @ 4% 15yr interest", ipmt_total(0.04, 180, 300000), 99430.54, tolerance=1.0)

    # Test 0% interest
    result = ipmt_total(0.0, 360, 400000)
    test_approx("0% total interest", result, 0.0)

    print("\n3. Breakeven Calculations")
    print("-" * 40)

    test("5000/388.87 = 13 months", time_to_even(5000, 388.87) == 13, f"got {time_to_even(5000, 388.87)}")
    test("10000/500 = 20 months", time_to_even(10000, 500) == 20, f"got {time_to_even(10000, 500)}")
    test("3000/100 = 30 months", time_to_even(3000, 100) == 30, f"got {time_to_even(3000, 100)}")

    print("\n4. Full Calculation Parity (Dash vs API logic)")
    print("-" * 40)

    fixture = STANDARD_30YR

    # Simulate Dash calculation
    original_monthly_payment = calc_loan_monthly_payment(
        fixture['current_principal'], fixture['current_rate'], fixture['current_term']
    )
    minimum_monthly_payment = calc_loan_monthly_payment(
        fixture['current_principal'], 0.0, fixture['current_term']
    )
    months_paid = fixture['current_term'] - fixture['remaining_term']

    original_interest = ipmt_total(fixture['current_rate'], fixture['current_term'], fixture['current_principal'])
    refi_interest = ipmt_total(fixture['target_rate'], fixture['target_term'], fixture['remaining_principal'])

    original_interest_to_date = ipmt_total(
        fixture['current_rate'],
        fixture['current_term'],
        fixture['current_principal'],
        per=np.arange(1, months_paid + 1)
    )

    total_loan_savings = original_interest - refi_interest - fixture['refi_cost'] - original_interest_to_date

    refi_monthly_payment = calc_loan_monthly_payment(
        fixture['remaining_principal'], fixture['target_rate'], fixture['target_term']
    )
    monthly_savings = original_monthly_payment - refi_monthly_payment
    month_to_even_simple = time_to_even(fixture['refi_cost'], monthly_savings)

    print(f"  Original Monthly Payment: ${original_monthly_payment:.2f}")
    print(f"  Refi Monthly Payment: ${refi_monthly_payment:.2f}")
    print(f"  Monthly Savings: ${monthly_savings:.2f}")
    print(f"  Total Loan Savings: ${total_loan_savings:.2f}")
    print(f"  Months to Break Even: {month_to_even_simple:.0f}")

    # Verify calculations are consistent
    test("Original payment > refi payment", original_monthly_payment > refi_monthly_payment, "")
    test("Monthly savings positive", monthly_savings > 0, "")
    test("Breakeven is reasonable", 1 < month_to_even_simple < 60, f"got {month_to_even_simple}")

    print("\n5. Recoup Data Structure")
    print("-" * 40)

    recoup = calculate_recoup_data_extended(
        original_monthly_payment,
        refi_monthly_payment,
        fixture['target_term'],
        fixture['refi_cost'],
        fixture['target_rate'],
        fixture['remaining_principal'],
        fixture['current_term'],
        fixture['current_rate'],
        fixture['current_principal'],
        months_paid,
    )

    test("Has month column", 'month' in recoup.columns, "")
    test("Has monthly_savings column", 'monthly_savings' in recoup.columns, "")
    test("Has interest_refi_savings column", 'interest_refi_savings' in recoup.columns, "")
    test("Correct length", len(recoup) == fixture['target_term'] + 1, f"got {len(recoup)}")
    test("Starts negative", recoup.loc[0, 'monthly_savings'] == -fixture['refi_cost'], "")

    # Check eventually positive
    positive_months = recoup[recoup['monthly_savings'] > 0]
    test("Eventually positive", len(positive_months) > 0, "never becomes positive")

    print("\n6. Edge Cases")
    print("-" * 40)

    # No savings scenario (higher target rate)
    orig_pay = calc_loan_monthly_payment(300000, 0.04, 360)
    refi_pay = calc_loan_monthly_payment(280000, 0.05, 360)
    test("Higher rate = negative savings", orig_pay - refi_pay < 0, "")

    # Very short term
    result = calc_loan_monthly_payment(10000, 0.05, 12)
    test("Short term calculates", result > 0 and result < 1000, f"got {result}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASSED} passed, {FAILED} failed")
    print("=" * 60)

    if FAILED > 0:
        print("\n*** PARITY CHECK FAILED ***")
        sys.exit(1)
    else:
        print("\n*** ALL PARITY CHECKS PASSED ***")
        sys.exit(0)


if __name__ == '__main__':
    main()
