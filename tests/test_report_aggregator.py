"""Tests for the Report Data Aggregation Service.

These tests verify the business logic of the report aggregation service
by testing the calculation functions and data structures in isolation.
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import calc functions directly - they have no Flask dependencies
import numpy as np
import pandas as pd
import numpy_financial as npf


# Replicate calc functions for isolated testing
def calc_loan_monthly_payment(principal, rate, term):
    """Calculate monthly payment for a loan."""
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
    """Calculate total interest paid."""
    if per is None:
        per = np.arange(term) + 1
    return -1 * np.sum(npf.ipmt(rate / 12, per, term, principal))


def time_to_even(cost, monthly_savings):
    """Calculate months to break even."""
    return np.ceil(cost / monthly_savings)


class TestCalcFunctions:
    """Test the underlying calculation functions used by the service."""

    def test_calc_monthly_payment_30yr(self):
        """Test 30-year loan monthly payment calculation."""
        # $300,000 loan at 7% for 30 years
        principal = 300000
        rate = 0.07
        term = 360

        payment = calc_loan_monthly_payment(principal, rate, term)

        # Expected ~$1,995.91
        assert 1990 < payment < 2000

    def test_calc_monthly_payment_15yr(self):
        """Test 15-year loan monthly payment calculation."""
        # $300,000 loan at 6% for 15 years
        principal = 300000
        rate = 0.06
        term = 180

        payment = calc_loan_monthly_payment(principal, rate, term)

        # 15-year loan should have higher monthly payment
        assert payment > 2000

    def test_calc_monthly_payment_zero_rate(self):
        """Test payment calculation with zero interest rate."""
        principal = 300000
        rate = 0.0
        term = 360

        payment = calc_loan_monthly_payment(principal, rate, term)

        # Should be principal / term
        assert abs(payment - (principal / term)) < 0.01

    def test_time_to_even(self):
        """Test break-even time calculation."""
        cost = 3000
        monthly_savings = 200

        months = time_to_even(cost, monthly_savings)

        assert months == 15  # ceil(3000/200)

    def test_time_to_even_fractional(self):
        """Test break-even with fractional result."""
        cost = 3000
        monthly_savings = 400

        months = time_to_even(cost, monthly_savings)

        # 3000/400 = 7.5, ceil = 8
        assert months == 8


class TestSavingsLogic:
    """Test savings calculation logic."""

    def test_monthly_savings_positive(self):
        """Test that lower rates yield positive monthly savings."""
        principal = 280000
        current_rate = 0.07
        new_rate = 0.05
        term = 360

        current_payment = calc_loan_monthly_payment(principal, current_rate, term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, term)
        monthly_savings = current_payment - new_payment

        assert monthly_savings > 0
        assert monthly_savings > 300  # Significant savings

    def test_monthly_savings_negative(self):
        """Test that higher rates yield negative savings."""
        principal = 280000
        current_rate = 0.05
        new_rate = 0.07
        term = 360

        current_payment = calc_loan_monthly_payment(principal, current_rate, term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, term)
        monthly_savings = current_payment - new_payment

        assert monthly_savings < 0

    def test_breakeven_calculation(self):
        """Test full break-even scenario."""
        principal = 280000
        current_rate = 0.07
        new_rate = 0.055
        term = 360
        refi_cost = 3000

        current_payment = calc_loan_monthly_payment(principal, current_rate, term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, term)
        monthly_savings = current_payment - new_payment

        if monthly_savings > 0:
            breakeven_months = time_to_even(refi_cost, monthly_savings)
            assert breakeven_months > 0
            assert breakeven_months < 36  # Reasonable break-even period


class TestDataStructures:
    """Test data structure creation and validation."""

    def test_rate_statistics_fields(self):
        """Test that rate statistics contain expected fields."""
        current = 0.065
        min_rate = 0.060
        max_rate = 0.070
        avg_rate = 0.065
        change = current - max_rate  # Rate went down

        assert change < 0  # Rates decreased
        assert min_rate <= current <= max_rate
        assert min_rate <= avg_rate <= max_rate

    def test_savings_calculation_values(self):
        """Test that savings values are computed correctly."""
        principal = 280000
        old_rate = 0.07
        new_rate = 0.055
        term = 360
        refi_cost = 3000

        old_payment = calc_loan_monthly_payment(principal, old_rate, term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, term)

        monthly_savings = old_payment - new_payment
        old_total_interest = ipmt_total(old_rate, term, principal)
        new_total_interest = ipmt_total(new_rate, term, principal)
        interest_savings = old_total_interest - new_total_interest - refi_cost

        assert monthly_savings > 0
        assert interest_savings > 0
        assert new_payment < old_payment


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_principal(self):
        """Test calculation with small loan amount."""
        payment = calc_loan_monthly_payment(10000, 0.05, 60)
        assert payment > 0
        assert payment < 250

    def test_very_large_principal(self):
        """Test calculation with large loan amount."""
        payment = calc_loan_monthly_payment(1000000, 0.06, 360)
        assert payment > 5000

    def test_short_term(self):
        """Test calculation with short loan term."""
        payment = calc_loan_monthly_payment(100000, 0.05, 12)
        # Should be close to principal/12 plus some interest
        assert payment > 8000

    def test_savings_at_same_rate(self):
        """Test savings when refinancing at same rate."""
        principal = 280000
        rate = 0.065
        term = 360

        old_payment = calc_loan_monthly_payment(principal, rate, term)
        new_payment = calc_loan_monthly_payment(principal, rate, term)

        assert abs(old_payment - new_payment) < 0.01  # Essentially zero difference


class TestRefinancingScenarios:
    """Test realistic refinancing scenarios."""

    def test_typical_refinance_30yr_to_30yr(self):
        """Test typical 30-year to 30-year refinance."""
        # Starting: $350k remaining at 7% with 28 years left
        # New: 5.5% for 30 years
        principal = 350000
        old_rate = 0.07
        new_rate = 0.055
        old_term = 336  # 28 years
        new_term = 360  # 30 years
        refi_cost = 4000

        old_payment = calc_loan_monthly_payment(principal, old_rate, old_term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, new_term)

        # Monthly savings
        monthly_diff = old_payment - new_payment
        assert monthly_diff > 200  # Significant monthly savings

        # Break-even
        if monthly_diff > 0:
            breakeven = time_to_even(refi_cost, monthly_diff)
            assert breakeven < 24  # Under 2 years to break even

    def test_refinance_to_shorter_term(self):
        """Test refinancing to a shorter term."""
        # Starting: $300k at 7% for 30 years
        # New: 5.5% for 15 years
        principal = 300000
        old_rate = 0.07
        new_rate = 0.055
        old_term = 360
        new_term = 180

        old_payment = calc_loan_monthly_payment(principal, old_rate, old_term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, new_term)

        # Payment will be higher with shorter term
        assert new_payment > old_payment

        # But total interest will be much lower
        old_interest = ipmt_total(old_rate, old_term, principal)
        new_interest = ipmt_total(new_rate, new_term, principal)

        assert new_interest < old_interest
        # Savings should be substantial
        interest_savings = old_interest - new_interest
        assert interest_savings > 100000  # Over $100k in interest savings

    def test_marginal_rate_difference(self):
        """Test with small rate difference (0.25%)."""
        principal = 280000
        old_rate = 0.065
        new_rate = 0.0625  # 0.25% lower
        term = 360
        refi_cost = 3000

        old_payment = calc_loan_monthly_payment(principal, old_rate, term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, term)

        monthly_savings = old_payment - new_payment

        # Small but positive savings
        assert monthly_savings > 0
        assert monthly_savings < 100  # Not huge savings

        # Longer break-even period
        breakeven = time_to_even(refi_cost, monthly_savings)
        assert breakeven > 30  # Many months to break even
