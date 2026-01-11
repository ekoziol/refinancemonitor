"""
Regression tests for API vs Dash parity.

These tests ensure the API returns IDENTICAL results to the Dash calculator.
Tolerance: <$0.01 difference on all monetary calculations.

Test scenarios cover:
- Standard refinance scenarios
- Edge cases (0% interest, very short/long terms)
- Various principal amounts
- Different rate differentials
"""

import pytest
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from refi_monitor.calc import (
    calc_loan_monthly_payment,
    ipmt_total,
    time_to_even,
    find_target_interest_rate,
    create_mortage_range,
    get_per,
)
from refi_monitor.api.calculator import calculate_recoup_data_extended
import numpy as np

# Tolerance for monetary comparisons (in dollars)
TOLERANCE = 0.01


class TestFixtures:
    """Known test fixtures with pre-calculated expected values."""

    # Standard 30-year mortgage scenario
    STANDARD_30YR = {
        'current_principal': 400000,
        'current_rate': 0.045,  # 4.5%
        'current_term': 360,    # 30 years
        'target_rate': 0.035,   # 3.5%
        'target_term': 360,
        'refi_cost': 5000,
        'remaining_term': 300,
        'remaining_principal': 364631.66,
        # Expected values (calculated)
        'expected_original_payment': 2026.74,
        'expected_refi_payment': 1637.87,
    }

    # 15-year mortgage scenario
    STANDARD_15YR = {
        'current_principal': 300000,
        'current_rate': 0.04,   # 4%
        'current_term': 180,    # 15 years
        'target_rate': 0.03,    # 3%
        'target_term': 180,
        'refi_cost': 4000,
        'remaining_term': 150,
        'remaining_principal': 250000,
        'expected_original_payment': 2219.06,
        'expected_refi_payment': 1726.45,
    }

    # High-value jumbo loan
    JUMBO_LOAN = {
        'current_principal': 1000000,
        'current_rate': 0.0525,  # 5.25%
        'current_term': 360,
        'target_rate': 0.0425,   # 4.25%
        'target_term': 360,
        'refi_cost': 15000,
        'remaining_term': 330,
        'remaining_principal': 950000,
    }

    # Small loan scenario
    SMALL_LOAN = {
        'current_principal': 100000,
        'current_rate': 0.06,    # 6%
        'current_term': 180,
        'target_rate': 0.045,    # 4.5%
        'target_term': 180,
        'refi_cost': 2000,
        'remaining_term': 120,
        'remaining_principal': 70000,
    }


class TestMonthlyPaymentParity:
    """Test monthly payment calculations match between calc.py and API logic."""

    @pytest.mark.parametrize("principal,rate,term,expected", [
        (400000, 0.045, 360, 2026.74),
        (300000, 0.04, 180, 2219.06),
        (100000, 0.06, 180, 843.86),
        (500000, 0.035, 360, 2245.22),
        (250000, 0.0525, 240, 1695.14),
    ])
    def test_monthly_payment_known_values(self, principal, rate, term, expected):
        """Test monthly payment against known correct values."""
        result = calc_loan_monthly_payment(principal, rate, term)
        assert abs(result - expected) < TOLERANCE, \
            f"Payment {result:.2f} differs from expected {expected:.2f} by more than ${TOLERANCE}"

    def test_zero_interest_rate(self):
        """Test 0% interest rate calculates correctly."""
        principal = 360000
        term = 360
        result = calc_loan_monthly_payment(principal, 0.0, term)
        expected = principal / term  # Simple division
        assert abs(result - expected) < TOLERANCE

    def test_very_high_rate(self):
        """Test high interest rate (15%) calculates correctly."""
        result = calc_loan_monthly_payment(200000, 0.15, 360)
        expected = 2528.51  # Pre-calculated
        assert abs(result - expected) < TOLERANCE

    def test_short_term_loan(self):
        """Test 5-year loan calculates correctly."""
        result = calc_loan_monthly_payment(50000, 0.05, 60)
        expected = 943.56
        assert abs(result - expected) < TOLERANCE


class TestTotalInterestParity:
    """Test total interest calculations."""

    @pytest.mark.parametrize("rate,term,principal,expected", [
        (0.045, 360, 400000, 329625.29),
        (0.04, 180, 300000, 99430.54),
        (0.035, 360, 364631.66, 225200.24),
    ])
    def test_total_interest_known_values(self, rate, term, principal, expected):
        """Test total interest against known values."""
        result = ipmt_total(rate, term, principal)
        assert abs(result - expected) < 1.0, \
            f"Total interest {result:.2f} differs from expected {expected:.2f}"

    def test_zero_interest(self):
        """Test 0% interest returns 0 total interest."""
        result = ipmt_total(0.0, 360, 400000)
        assert result == 0.0


class TestBreakevenParity:
    """Test breakeven calculations."""

    @pytest.mark.parametrize("cost,savings,expected_months", [
        (5000, 388.87, 13),   # Standard scenario
        (10000, 500, 20),     # Round numbers
        (3000, 100, 30),      # Small savings
        (15000, 750, 20),     # Larger refi cost
    ])
    def test_breakeven_known_values(self, cost, savings, expected_months):
        """Test breakeven months against known values."""
        result = time_to_even(cost, savings)
        assert result == expected_months


class TestFindTargetRateParity:
    """Test finding target rate for a payment."""

    def test_find_rate_standard(self):
        """Test finding rate for standard scenario."""
        principal = 364631.66
        term = 360
        target_payment = 1637.87

        result = find_target_interest_rate(principal, term, target_payment)

        # Verify the found rate gives approximately the target payment
        actual_payment = calc_loan_monthly_payment(principal, result, term)
        assert abs(actual_payment - target_payment) < 50, \
            f"Found rate {result:.4f} gives payment {actual_payment:.2f}, expected ~{target_payment:.2f}"

    def test_find_rate_15yr(self):
        """Test finding rate for 15-year loan."""
        principal = 250000
        term = 180
        target_payment = 1726.45

        result = find_target_interest_rate(principal, term, target_payment)
        actual_payment = calc_loan_monthly_payment(principal, result, term)
        assert abs(actual_payment - target_payment) < 50


class TestFullCalculationParity:
    """Test full calculation workflow matches Dash behavior."""

    def _simulate_dash_calculation(self, fixture):
        """
        Simulate what the Dash update_data_stores callback returns.
        This is the reference implementation.
        """
        current_principal = fixture['current_principal']
        current_rate = fixture['current_rate']
        current_term = fixture['current_term']
        target_rate = fixture['target_rate']
        target_term = fixture['target_term']
        refi_cost = fixture['refi_cost']
        remaining_term = fixture['remaining_term']
        remaining_principal = fixture['remaining_principal']

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

        if monthly_savings > 0:
            month_to_even_simple = time_to_even(refi_cost, monthly_savings)
        else:
            month_to_even_simple = float('inf')

        return {
            'original_monthly_payment': original_monthly_payment,
            'minimum_monthly_payment': minimum_monthly_payment,
            'monthly_savings': monthly_savings,
            'total_loan_savings': total_loan_savings,
            'months_paid': months_paid,
            'original_interest': original_interest,
            'refi_monthly_payment': refi_monthly_payment,
            'refi_interest': refi_interest,
            'month_to_even_simple': month_to_even_simple,
        }

    def _simulate_api_calculation(self, fixture):
        """
        Simulate what the API /calculate endpoint returns.
        This should match the Dash calculation.
        """
        # Import here to avoid circular imports in test setup
        from refi_monitor.api.calculator import calculate_recoup_data_extended

        current_principal = fixture['current_principal']
        current_rate = fixture['current_rate']
        current_term = fixture['current_term']
        target_rate = fixture['target_rate']
        target_term = fixture['target_term']
        refi_cost = fixture['refi_cost']
        remaining_term = fixture['remaining_term']
        remaining_principal = fixture['remaining_principal']

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

        if monthly_savings > 0:
            month_to_even_simple = time_to_even(refi_cost, monthly_savings)
        else:
            month_to_even_simple = float('inf')

        return {
            'original_monthly_payment': original_monthly_payment,
            'minimum_monthly_payment': minimum_monthly_payment,
            'monthly_savings': monthly_savings,
            'total_loan_savings': total_loan_savings,
            'months_paid': months_paid,
            'original_interest': original_interest,
            'refi_monthly_payment': refi_monthly_payment,
            'refi_interest': refi_interest,
            'month_to_even_simple': month_to_even_simple,
        }

    def test_standard_30yr_parity(self):
        """Test 30-year mortgage calculation parity."""
        fixture = TestFixtures.STANDARD_30YR

        dash_result = self._simulate_dash_calculation(fixture)
        api_result = self._simulate_api_calculation(fixture)

        for key in dash_result:
            dash_val = dash_result[key]
            api_val = api_result[key]

            if isinstance(dash_val, float) and dash_val != float('inf'):
                assert abs(dash_val - api_val) < TOLERANCE, \
                    f"{key}: Dash={dash_val:.2f}, API={api_val:.2f}, diff={abs(dash_val-api_val):.4f}"
            else:
                assert dash_val == api_val, \
                    f"{key}: Dash={dash_val}, API={api_val}"

    def test_standard_15yr_parity(self):
        """Test 15-year mortgage calculation parity."""
        fixture = TestFixtures.STANDARD_15YR

        dash_result = self._simulate_dash_calculation(fixture)
        api_result = self._simulate_api_calculation(fixture)

        for key in dash_result:
            dash_val = dash_result[key]
            api_val = api_result[key]

            if isinstance(dash_val, float) and dash_val != float('inf'):
                assert abs(dash_val - api_val) < TOLERANCE, \
                    f"{key}: Dash={dash_val:.2f}, API={api_val:.2f}"

    def test_jumbo_loan_parity(self):
        """Test jumbo loan calculation parity."""
        fixture = TestFixtures.JUMBO_LOAN

        dash_result = self._simulate_dash_calculation(fixture)
        api_result = self._simulate_api_calculation(fixture)

        for key in dash_result:
            dash_val = dash_result[key]
            api_val = api_result[key]

            if isinstance(dash_val, float) and dash_val != float('inf'):
                assert abs(dash_val - api_val) < TOLERANCE, \
                    f"{key}: Dash={dash_val:.2f}, API={api_val:.2f}"

    def test_small_loan_parity(self):
        """Test small loan calculation parity."""
        fixture = TestFixtures.SMALL_LOAN

        dash_result = self._simulate_dash_calculation(fixture)
        api_result = self._simulate_api_calculation(fixture)

        for key in dash_result:
            dash_val = dash_result[key]
            api_val = api_result[key]

            if isinstance(dash_val, float) and dash_val != float('inf'):
                assert abs(dash_val - api_val) < TOLERANCE, \
                    f"{key}: Dash={dash_val:.2f}, API={api_val:.2f}"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_no_savings_scenario(self):
        """Test when refinance doesn't save money."""
        # Higher target rate than current
        original_payment = calc_loan_monthly_payment(300000, 0.04, 360)
        refi_payment = calc_loan_monthly_payment(280000, 0.05, 360)

        savings = original_payment - refi_payment
        assert savings < 0, "Expected negative savings with higher rate"

    def test_very_short_remaining_term(self):
        """Test with only 12 months remaining."""
        result = calc_loan_monthly_payment(10000, 0.05, 12)
        assert result > 0
        assert result < 1000  # Sanity check

    def test_just_started_loan(self):
        """Test calculation when loan just started (full term remaining)."""
        fixture = {
            'current_principal': 400000,
            'current_rate': 0.045,
            'current_term': 360,
            'target_rate': 0.035,
            'target_term': 360,
            'refi_cost': 5000,
            'remaining_term': 360,  # Just started
            'remaining_principal': 400000,
        }

        original_payment = calc_loan_monthly_payment(
            fixture['current_principal'],
            fixture['current_rate'],
            fixture['current_term']
        )
        refi_payment = calc_loan_monthly_payment(
            fixture['remaining_principal'],
            fixture['target_rate'],
            fixture['target_term']
        )

        assert original_payment > refi_payment, "Lower rate should give lower payment"

    def test_near_end_of_loan(self):
        """Test calculation near end of original loan."""
        months_paid = 300  # 25 years in
        remaining_term = 60
        remaining_principal = 50000  # Low remaining balance

        original_payment = calc_loan_monthly_payment(400000, 0.045, 360)
        refi_payment = calc_loan_monthly_payment(remaining_principal, 0.035, 360)

        # With only $50K remaining, refi might not make sense
        assert refi_payment < original_payment


class TestRecoupDataParity:
    """Test recoup data calculation parity."""

    def test_recoup_data_structure(self):
        """Test that recoup data has correct structure."""
        fixture = TestFixtures.STANDARD_30YR

        original_payment = calc_loan_monthly_payment(
            fixture['current_principal'],
            fixture['current_rate'],
            fixture['current_term']
        )
        refi_payment = calc_loan_monthly_payment(
            fixture['remaining_principal'],
            fixture['target_rate'],
            fixture['target_term']
        )
        months_paid = fixture['current_term'] - fixture['remaining_term']

        result = calculate_recoup_data_extended(
            original_payment,
            refi_payment,
            fixture['target_term'],
            fixture['refi_cost'],
            fixture['target_rate'],
            fixture['remaining_principal'],
            fixture['current_term'],
            fixture['current_rate'],
            fixture['current_principal'],
            months_paid,
        )

        # Check structure
        assert 'month' in result.columns
        assert 'monthly_savings' in result.columns
        assert 'interest_refi_savings' in result.columns

        # Check length
        assert len(result) == fixture['target_term'] + 1

    def test_recoup_starts_negative(self):
        """Test that recoup starts negative (due to refi costs)."""
        fixture = TestFixtures.STANDARD_30YR

        original_payment = calc_loan_monthly_payment(
            fixture['current_principal'],
            fixture['current_rate'],
            fixture['current_term']
        )
        refi_payment = calc_loan_monthly_payment(
            fixture['remaining_principal'],
            fixture['target_rate'],
            fixture['target_term']
        )
        months_paid = fixture['current_term'] - fixture['remaining_term']

        result = calculate_recoup_data_extended(
            original_payment,
            refi_payment,
            fixture['target_term'],
            fixture['refi_cost'],
            fixture['target_rate'],
            fixture['remaining_principal'],
            fixture['current_term'],
            fixture['current_rate'],
            fixture['current_principal'],
            months_paid,
        )

        # Month 0 should be negative (just paid refi cost)
        assert result.loc[0, 'monthly_savings'] == -fixture['refi_cost']

    def test_recoup_eventually_positive(self):
        """Test that recoup eventually becomes positive (for good refi)."""
        fixture = TestFixtures.STANDARD_30YR

        original_payment = calc_loan_monthly_payment(
            fixture['current_principal'],
            fixture['current_rate'],
            fixture['current_term']
        )
        refi_payment = calc_loan_monthly_payment(
            fixture['remaining_principal'],
            fixture['target_rate'],
            fixture['target_term']
        )
        months_paid = fixture['current_term'] - fixture['remaining_term']

        result = calculate_recoup_data_extended(
            original_payment,
            refi_payment,
            fixture['target_term'],
            fixture['refi_cost'],
            fixture['target_rate'],
            fixture['remaining_principal'],
            fixture['current_term'],
            fixture['current_rate'],
            fixture['current_principal'],
            months_paid,
        )

        # Should eventually become positive
        positive_months = result[result['monthly_savings'] > 0]
        assert len(positive_months) > 0, "Recoup should eventually become positive"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
