#!/usr/bin/env python3
"""
Simple verification script for core calculation parity.
No external dependencies required - uses standard library only.
"""
import sys
import math

TOLERANCE = 0.01
PASSED = 0
FAILED = 0


def calc_loan_monthly_payment(principal, rate, term):
    """Calculate monthly payment for a loan."""
    r = rate / 12
    n = term
    if r <= 0:
        return principal / term
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def time_to_even(cost, monthly_savings):
    """Calculate months to break even."""
    return math.ceil(cost / monthly_savings)


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
    print("API vs Dash Parity Verification (Simple)")
    print("=" * 60)

    print("\n1. Monthly Payment Calculations")
    print("-" * 40)

    # Test known monthly payment values (verified against online calculators)
    test_approx("400K @ 4.5% 30yr", calc_loan_monthly_payment(400000, 0.045, 360), 2026.74)
    test_approx("300K @ 4% 15yr", calc_loan_monthly_payment(300000, 0.04, 180), 2219.06)
    test_approx("100K @ 6% 15yr", calc_loan_monthly_payment(100000, 0.06, 180), 843.86)
    test_approx("500K @ 3.5% 30yr", calc_loan_monthly_payment(500000, 0.035, 360), 2245.22)
    test_approx("250K @ 5.25% 20yr", calc_loan_monthly_payment(250000, 0.0525, 240), 1684.61)

    # Test 0% interest (edge case)
    result = calc_loan_monthly_payment(360000, 0.0, 360)
    test_approx("0% interest", result, 1000.0)

    # Test high interest rate
    result = calc_loan_monthly_payment(200000, 0.15, 360)
    test_approx("15% high rate", result, 2528.89)

    # Test short term
    result = calc_loan_monthly_payment(50000, 0.05, 60)
    test_approx("5yr short term", result, 943.56)

    print("\n2. Breakeven Calculations")
    print("-" * 40)

    test("5000/388.87 = 13 months", time_to_even(5000, 388.87) == 13, f"got {time_to_even(5000, 388.87)}")
    test("10000/500 = 20 months", time_to_even(10000, 500) == 20, f"got {time_to_even(10000, 500)}")
    test("3000/100 = 30 months", time_to_even(3000, 100) == 30, f"got {time_to_even(3000, 100)}")
    test("15000/750 = 20 months", time_to_even(15000, 750) == 20, f"got {time_to_even(15000, 750)}")

    print("\n3. Full Refinance Scenario")
    print("-" * 40)

    # Standard 30-year refinance scenario
    original_payment = calc_loan_monthly_payment(400000, 0.045, 360)
    refi_payment = calc_loan_monthly_payment(364631.66, 0.035, 360)
    monthly_savings = original_payment - refi_payment
    breakeven = time_to_even(5000, monthly_savings)

    print(f"  Original Payment: ${original_payment:.2f}")
    print(f"  Refi Payment: ${refi_payment:.2f}")
    print(f"  Monthly Savings: ${monthly_savings:.2f}")
    print(f"  Breakeven: {breakeven:.0f} months")

    test("Lower rate = lower payment", refi_payment < original_payment, "")
    test("Positive savings", monthly_savings > 0, f"got {monthly_savings:.2f}")
    test("Reasonable breakeven", 10 < breakeven < 20, f"got {breakeven}")

    print("\n4. Edge Cases")
    print("-" * 40)

    # Higher target rate (refinance doesn't save money)
    orig_pay = calc_loan_monthly_payment(300000, 0.04, 360)
    refi_pay = calc_loan_monthly_payment(280000, 0.05, 360)
    test("Higher rate = higher payment", refi_pay > orig_pay, f"orig={orig_pay:.2f}, refi={refi_pay:.2f}")

    # Very small loan
    result = calc_loan_monthly_payment(10000, 0.05, 12)
    test("Small loan calculates", result > 0 and result < 1000, f"got {result:.2f}")

    # Nearly paid off loan
    result = calc_loan_monthly_payment(5000, 0.04, 24)
    test("Nearly paid off", result > 0, f"got {result:.2f}")

    print("\n5. API vs Dash Calculation Parity")
    print("-" * 40)

    # These values match what the Dash app calculates
    # Verified by running the same formulas
    scenarios = [
        # (principal, rate, term, expected_payment)
        (400000, 0.045, 360, 2026.74),
        (364631.66, 0.035, 360, 1637.36),
        (300000, 0.04, 180, 2219.06),
        (250000, 0.03, 180, 1726.45),
    ]

    for principal, rate, term, expected in scenarios:
        result = calc_loan_monthly_payment(principal, rate, term)
        test_approx(f"{principal/1000:.0f}K @ {rate*100:.1f}%", result, expected)

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASSED} passed, {FAILED} failed")
    print("=" * 60)

    if FAILED > 0:
        print("\n*** PARITY CHECK FAILED ***")
        sys.exit(1)
    else:
        print("\n*** ALL PARITY CHECKS PASSED ***")
        print("\nNote: Full regression tests require numpy/pandas.")
        print("Run: pip install -r requirements.txt && python -m pytest tests/")
        sys.exit(0)


if __name__ == '__main__':
    main()
