"""
Integration tests for Dash Calculator.

These tests capture the current behavior of the Dash refinance calculator
by testing the calculation functions and data structures used by callbacks.
"""
import pytest
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import sys
import os

# Add refi_monitor to path for direct import without triggering __init__.py Flask imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'refi_monitor'))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "calc",
    os.path.join(os.path.dirname(__file__), '..', '..', 'refi_monitor', 'calc.py')
)
calc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calc)

# Import calc functions used by Dash callbacks
calc_loan_monthly_payment = calc.calc_loan_monthly_payment
total_payment = calc.total_payment
create_mortage_range = calc.create_mortage_range
find_target_interest_rate = calc.find_target_interest_rate
amount_remaining = calc.amount_remaining
create_mortgage_table = calc.create_mortgage_table
find_break_even_interest = calc.find_break_even_interest
create_efficient_frontier = calc.create_efficient_frontier
ipmt_total = calc.ipmt_total
get_per = calc.get_per
time_to_even = calc.time_to_even
calculate_recoup_data = calc.calculate_recoup_data


class TestMonthlyPaymentCalculations:
    """Tests for monthly payment calculations used by Dash callbacks."""

    def test_calc_loan_monthly_payment_default_values(self, default_mortgage_inputs):
        """Test monthly payment calculation with default Dash values."""
        result = calc_loan_monthly_payment(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        # Expected: ~$2,026.74 for $400k at 4.5% for 30 years
        assert result == pytest.approx(2026.74, rel=0.01)

    def test_calc_loan_monthly_payment_high_rate(self, high_rate_mortgage_inputs):
        """Test monthly payment with high interest rate."""
        result = calc_loan_monthly_payment(
            high_rate_mortgage_inputs['current_principal'],
            high_rate_mortgage_inputs['current_rate'],
            high_rate_mortgage_inputs['current_term'],
        )
        # Higher rate should result in higher payment
        assert result > 3000
        assert result == pytest.approx(3668.82, rel=0.01)

    def test_calc_loan_monthly_payment_zero_rate(self, zero_rate_mortgage_inputs):
        """Test monthly payment with zero interest rate."""
        result = calc_loan_monthly_payment(
            zero_rate_mortgage_inputs['current_principal'],
            zero_rate_mortgage_inputs['current_rate'],
            zero_rate_mortgage_inputs['current_term'],
        )
        # At 0% interest, payment should be principal / term
        expected = 300000 / 360
        assert result == pytest.approx(expected, rel=0.001)

    def test_calc_loan_monthly_payment_short_term(self, short_term_mortgage_inputs):
        """Test monthly payment for 15-year mortgage."""
        result = calc_loan_monthly_payment(
            short_term_mortgage_inputs['current_principal'],
            short_term_mortgage_inputs['current_rate'],
            short_term_mortgage_inputs['current_term'],
        )
        # 15-year should have higher payment than 30-year
        assert result > 1500
        assert result == pytest.approx(1787.21, rel=0.01)

    def test_calc_loan_monthly_payment_returns_positive(self):
        """Verify monthly payment is always positive for valid inputs."""
        # Various valid combinations
        test_cases = [
            (100000, 0.03, 360),
            (500000, 0.07, 180),
            (250000, 0.045, 240),
            (1000000, 0.05, 360),
        ]
        for principal, rate, term in test_cases:
            result = calc_loan_monthly_payment(principal, rate, term)
            assert result > 0, f"Failed for {principal}, {rate}, {term}"


class TestTotalPaymentCalculations:
    """Tests for total payment calculations."""

    def test_total_payment_calculation(self):
        """Test total payment over loan term."""
        monthly = 2000
        term = 360
        result = total_payment(monthly, term)
        assert result == 720000

    def test_total_payment_short_term(self):
        """Test total payment for short term loan."""
        monthly = 2500
        term = 180
        result = total_payment(monthly, term)
        assert result == 450000


class TestMortgageRangeGeneration:
    """Tests for mortgage range DataFrame generation used by charts."""

    def test_create_mortgage_range_structure(self, default_mortgage_inputs):
        """Test mortgage range DataFrame has correct structure."""
        df = create_mortage_range(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_term'],
        )
        # Check DataFrame has required columns
        assert 'rate' in df.columns
        assert 'monthly_payment' in df.columns
        assert 'total_payment' in df.columns

    def test_create_mortgage_range_rate_bounds(self, default_mortgage_inputs):
        """Test mortgage range has correct rate bounds."""
        df = create_mortage_range(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_term'],
        )
        # Default rmax=0.1, rstep=0.00125
        assert df['rate'].min() == 0.0
        assert df['rate'].max() == pytest.approx(0.1, rel=0.001)

    def test_create_mortgage_range_custom_bounds(self):
        """Test mortgage range with custom rate bounds."""
        df = create_mortage_range(300000, 360, rmax=0.15, rstep=0.005)
        assert df['rate'].max() == pytest.approx(0.15, rel=0.001)

    def test_create_mortgage_range_payment_monotonic(self, default_mortgage_inputs):
        """Test that payments increase monotonically with rate."""
        df = create_mortage_range(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_term'],
        )
        payments = df['monthly_payment'].values
        # All subsequent payments should be >= previous (monotonic increase)
        assert all(payments[i] <= payments[i + 1] for i in range(len(payments) - 1))

    def test_create_mortgage_range_total_payment_consistent(self, default_mortgage_inputs):
        """Test total payment equals monthly payment * term."""
        df = create_mortage_range(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_term'],
        )
        for _, row in df.iterrows():
            expected_total = row['monthly_payment'] * default_mortgage_inputs['current_term']
            assert row['total_payment'] == pytest.approx(expected_total, rel=0.001)


class TestTargetInterestRateFinder:
    """Tests for finding target interest rate from target payment."""

    def test_find_target_interest_rate_basic(self, default_mortgage_inputs):
        """Test finding interest rate for target payment."""
        target_payment = 1500
        rate = find_target_interest_rate(
            default_mortgage_inputs['remaining_principal'],
            default_mortgage_inputs['target_term'],
            target_payment,
        )
        # Rate should be positive and less than max
        assert rate >= 0
        assert rate < 0.185

    def test_find_target_interest_rate_inverse_relationship(self):
        """Test that lower target payment requires lower rate."""
        principal = 300000
        term = 360

        rate_low = find_target_interest_rate(principal, term, 1200)
        rate_high = find_target_interest_rate(principal, term, 1800)

        # Lower payment needs lower rate
        assert rate_low < rate_high

    def test_find_target_interest_rate_high_payment(self, high_rate_mortgage_inputs):
        """Test finding rate for high target payment."""
        target_payment = 3000
        rate = find_target_interest_rate(
            high_rate_mortgage_inputs['remaining_principal'],
            high_rate_mortgage_inputs['target_term'],
            target_payment,
        )
        assert rate > 0


class TestMortgageTableGeneration:
    """Tests for mortgage amortization table generation."""

    def test_create_mortgage_table_structure(self, default_mortgage_inputs):
        """Test mortgage table has correct structure."""
        df = create_mortgage_table(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        assert 'month' in df.columns
        assert 'months_remaining' in df.columns
        assert 'amount_remaining' in df.columns

    def test_create_mortgage_table_month_range(self, default_mortgage_inputs):
        """Test month column spans full term."""
        df = create_mortgage_table(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        assert df['month'].min() == 0
        assert df['month'].max() == default_mortgage_inputs['current_term']

    def test_create_mortgage_table_declining_balance(self, default_mortgage_inputs):
        """Test that amount remaining decreases over time."""
        df = create_mortgage_table(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        # Filter out month 0 and the last month
        amounts = df[df['months_remaining'] > 0]['amount_remaining'].values
        # Balance should decrease (or stay same at boundaries)
        for i in range(1, len(amounts)):
            assert amounts[i] <= amounts[i - 1]

    def test_create_mortgage_table_ends_at_zero(self, default_mortgage_inputs):
        """Test mortgage ends with zero balance."""
        df = create_mortgage_table(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        final_balance = df[df['months_remaining'] == 0]['amount_remaining'].values[0]
        assert final_balance == pytest.approx(0, abs=1)


class TestInterestCalculations:
    """Tests for interest payment calculations."""

    def test_ipmt_total_positive_rate(self, default_mortgage_inputs):
        """Test total interest calculation with positive rate."""
        result = ipmt_total(
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
            default_mortgage_inputs['current_principal'],
        )
        # Total interest should be positive
        assert result > 0
        # Should be significant for 30-year loan at 4.5%
        assert result > 200000

    def test_ipmt_total_higher_rate_more_interest(self):
        """Test that higher rates produce more interest."""
        principal = 300000
        term = 360

        interest_low = ipmt_total(0.03, term, principal)
        interest_high = ipmt_total(0.06, term, principal)

        assert interest_high > interest_low

    def test_ipmt_total_with_per_parameter(self, default_mortgage_inputs):
        """Test interest calculation for specific periods."""
        per = np.arange(12) + 1  # First year
        result = ipmt_total(
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
            default_mortgage_inputs['current_principal'],
            per=per,
        )
        # First year interest should be less than total
        total_interest = ipmt_total(
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
            default_mortgage_inputs['current_principal'],
        )
        assert result < total_interest

    def test_get_per_generates_correct_array(self):
        """Test period array generation."""
        per = get_per(12)
        expected = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        np.testing.assert_array_equal(per, expected)


class TestBreakEvenCalculations:
    """Tests for break-even calculations used by Dash."""

    def test_time_to_even_basic(self):
        """Test basic time to even calculation."""
        cost = 5000
        monthly_savings = 200
        result = time_to_even(cost, monthly_savings)
        assert result == 25  # 5000 / 200 = 25 months

    def test_time_to_even_rounds_up(self):
        """Test that time to even rounds up to whole months."""
        cost = 5000
        monthly_savings = 300
        result = time_to_even(cost, monthly_savings)
        # 5000/300 = 16.67, should round up to 17
        assert result == 17

    def test_time_to_even_with_high_savings(self):
        """Test quick break-even with high savings."""
        cost = 3000
        monthly_savings = 500
        result = time_to_even(cost, monthly_savings)
        assert result == 6

    def test_calculate_recoup_data_structure(self):
        """Test recoup data DataFrame structure."""
        df = calculate_recoup_data(
            original_monthly_payment=2000,
            refi_monthly_payment=1700,
            target_term=360,
            refi_cost=5000,
        )
        assert 'month' in df.columns
        assert 'monthly_savings' in df.columns
        assert len(df) == 361  # 0 to 360 inclusive

    def test_calculate_recoup_data_starts_negative(self):
        """Test recoup data starts negative due to refi cost."""
        df = calculate_recoup_data(
            original_monthly_payment=2000,
            refi_monthly_payment=1700,
            target_term=360,
            refi_cost=5000,
        )
        # At month 0, savings should equal -refi_cost
        assert df[df['month'] == 0]['monthly_savings'].values[0] == -5000

    def test_calculate_recoup_data_becomes_positive(self):
        """Test recoup data eventually becomes positive with savings."""
        df = calculate_recoup_data(
            original_monthly_payment=2000,
            refi_monthly_payment=1700,
            target_term=360,
            refi_cost=5000,
        )
        # With $300/month savings, should be positive after ~17 months
        positive_months = df[df['monthly_savings'] > 0]
        assert len(positive_months) > 0
        assert positive_months['month'].min() < 20


class TestEfficientFrontierCalculations:
    """Tests for efficient frontier calculations."""

    def test_create_efficient_frontier_structure(self, default_mortgage_inputs):
        """Test efficient frontier DataFrame structure."""
        df = create_efficient_frontier(
            original_principal=default_mortgage_inputs['current_principal'],
            original_rate=default_mortgage_inputs['current_rate'],
            original_term=default_mortgage_inputs['current_term'],
            current_principal=default_mortgage_inputs['remaining_principal'],
            term_remaining=default_mortgage_inputs['remaining_term'],
            new_term=default_mortgage_inputs['target_term'],
            refi_cost=default_mortgage_inputs['refi_cost'],
        )
        assert 'month' in df.columns
        assert 'interest_rate' in df.columns
        assert 'amount_remaining' in df.columns

    def test_create_efficient_frontier_rate_decreases(self, default_mortgage_inputs):
        """Test that efficient frontier rate generally decreases over time."""
        df = create_efficient_frontier(
            original_principal=default_mortgage_inputs['current_principal'],
            original_rate=default_mortgage_inputs['current_rate'],
            original_term=default_mortgage_inputs['current_term'],
            current_principal=default_mortgage_inputs['remaining_principal'],
            term_remaining=default_mortgage_inputs['remaining_term'],
            new_term=default_mortgage_inputs['target_term'],
            refi_cost=default_mortgage_inputs['refi_cost'],
        )
        # Generally, as more payments are made, required rate should decrease
        # to maintain efficiency
        early_rates = df[df['month'] < 60]['interest_rate'].mean()
        late_rates = df[(df['month'] > 240) & (df['month'] < 300)]['interest_rate'].mean()
        # Early rates should generally be higher or equal to late rates
        assert early_rates >= late_rates or np.isclose(early_rates, late_rates, atol=0.01)


class TestBreakEvenInterestFinder:
    """Tests for finding break-even interest rate."""

    def test_find_break_even_interest_basic(self):
        """Test finding break-even interest rate."""
        rate = find_break_even_interest(
            principal=300000,
            new_term=360,
            target=100000,
            current_rate=0.05,
        )
        # Should return a rate less than current rate
        assert rate < 0.05
        assert rate >= 0

    def test_find_break_even_interest_returns_lower_rate(self):
        """Test that break-even rate is lower than current when target is reasonable."""
        current_rate = 0.06
        rate = find_break_even_interest(
            principal=250000,
            new_term=360,
            target=150000,
            current_rate=current_rate,
        )
        assert rate < current_rate


class TestAmountRemainingCalculations:
    """Tests for remaining principal calculations."""

    def test_amount_remaining_at_start(self, default_mortgage_inputs):
        """Test amount remaining at start of loan."""
        monthly_payment = calc_loan_monthly_payment(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        result = amount_remaining(
            default_mortgage_inputs['current_principal'],
            monthly_payment,
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        # At start, remaining should equal principal
        assert result == pytest.approx(default_mortgage_inputs['current_principal'], rel=0.01)

    def test_amount_remaining_decreases(self, default_mortgage_inputs):
        """Test amount remaining decreases as months pass."""
        monthly_payment = calc_loan_monthly_payment(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )

        remaining_full = amount_remaining(
            default_mortgage_inputs['current_principal'],
            monthly_payment,
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )

        remaining_partial = amount_remaining(
            default_mortgage_inputs['current_principal'],
            monthly_payment,
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['remaining_term'],
        )

        assert remaining_partial < remaining_full


class TestDashDataStoreCalculations:
    """Tests simulating the main Dash data store callback calculations."""

    def test_data_store_monthly_payment_calculation(self, default_mortgage_inputs):
        """Test original monthly payment calculation as done in update_data_stores."""
        s_original_monthly_payment = calc_loan_monthly_payment(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        assert s_original_monthly_payment > 0
        assert s_original_monthly_payment == pytest.approx(2026.74, rel=0.01)

    def test_data_store_minimum_payment_calculation(self, default_mortgage_inputs):
        """Test minimum payment (0% rate) calculation."""
        s_minimum_monthly_payment = calc_loan_monthly_payment(
            default_mortgage_inputs['current_principal'],
            0.0,
            default_mortgage_inputs['current_term'],
        )
        # Should equal principal / term
        expected = default_mortgage_inputs['current_principal'] / default_mortgage_inputs['current_term']
        assert s_minimum_monthly_payment == pytest.approx(expected, rel=0.001)

    def test_data_store_months_paid_calculation(self, default_mortgage_inputs):
        """Test months paid calculation."""
        s_months_paid = default_mortgage_inputs['target_term'] - default_mortgage_inputs['remaining_term']
        assert s_months_paid == 60  # 360 - 300 = 60 months paid

    def test_data_store_interest_calculations(self, default_mortgage_inputs):
        """Test interest calculations for original and refi loans."""
        s_original_interest = ipmt_total(
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
            default_mortgage_inputs['current_principal'],
        )
        s_refi_interest = ipmt_total(
            default_mortgage_inputs['target_rate'],
            default_mortgage_inputs['target_term'],
            default_mortgage_inputs['remaining_principal'],
        )
        # Original interest at 4.5% should be more than refi at 2%
        assert s_original_interest > s_refi_interest

    def test_data_store_refi_monthly_payment(self, default_mortgage_inputs):
        """Test refinanced monthly payment calculation."""
        s_refi_monthly_payment = calc_loan_monthly_payment(
            default_mortgage_inputs['remaining_principal'],
            default_mortgage_inputs['target_rate'],
            default_mortgage_inputs['target_term'],
        )
        # At 2% rate should be lower than original at 4.5%
        original_payment = calc_loan_monthly_payment(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        assert s_refi_monthly_payment < original_payment

    def test_data_store_monthly_savings(self, default_mortgage_inputs):
        """Test monthly savings calculation."""
        original_payment = calc_loan_monthly_payment(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        refi_payment = calc_loan_monthly_payment(
            default_mortgage_inputs['remaining_principal'],
            default_mortgage_inputs['target_rate'],
            default_mortgage_inputs['target_term'],
        )
        monthly_savings = original_payment - refi_payment
        # With significantly lower rate, should have positive savings
        assert monthly_savings > 0

    def test_data_store_mortgage_range_dataframes(self, default_mortgage_inputs):
        """Test mortgage range DataFrame generation for charts."""
        sdf_original_mortgage_range = create_mortage_range(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_term'],
        )
        sdf_refi_mortgage_range = create_mortage_range(
            default_mortgage_inputs['remaining_principal'],
            default_mortgage_inputs['target_term'],
        )

        # Both should have same structure
        assert list(sdf_original_mortgage_range.columns) == list(sdf_refi_mortgage_range.columns)
        # Refi range should have lower payments at same rate (lower principal)
        rate_to_check = 0.04
        orig_payment = sdf_original_mortgage_range[
            sdf_original_mortgage_range['rate'] == rate_to_check
        ]['monthly_payment'].values[0]
        refi_payment = sdf_refi_mortgage_range[
            sdf_refi_mortgage_range['rate'] == rate_to_check
        ]['monthly_payment'].values[0]
        assert refi_payment < orig_payment


class TestChartDataValidation:
    """Tests validating chart data structures."""

    def test_mortgage_range_chart_data_valid(self, default_mortgage_inputs):
        """Test mortgage range produces valid chart data."""
        df = create_mortage_range(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_term'],
        )
        # No NaN values
        assert not df['rate'].isna().any()
        assert not df['monthly_payment'].isna().any()
        assert not df['total_payment'].isna().any()
        # No infinite values
        assert not np.isinf(df['monthly_payment']).any()
        assert not np.isinf(df['total_payment']).any()

    def test_mortgage_table_chart_data_valid(self, default_mortgage_inputs):
        """Test mortgage table produces valid chart data."""
        df = create_mortgage_table(
            default_mortgage_inputs['current_principal'],
            default_mortgage_inputs['current_rate'],
            default_mortgage_inputs['current_term'],
        )
        # No NaN values in key columns
        assert not df['month'].isna().any()
        assert not df['months_remaining'].isna().any()
        # Amount remaining should be finite
        valid_rows = df[df['months_remaining'] > 0]
        assert not np.isinf(valid_rows['amount_remaining']).any()

    def test_efficient_frontier_chart_data_valid(self, default_mortgage_inputs):
        """Test efficient frontier produces valid chart data."""
        df = create_efficient_frontier(
            original_principal=default_mortgage_inputs['current_principal'],
            original_rate=default_mortgage_inputs['current_rate'],
            original_term=default_mortgage_inputs['current_term'],
            current_principal=default_mortgage_inputs['remaining_principal'],
            term_remaining=default_mortgage_inputs['remaining_term'],
            new_term=default_mortgage_inputs['target_term'],
            refi_cost=default_mortgage_inputs['refi_cost'],
        )
        # Month column should be valid
        assert not df['month'].isna().any()
        # Interest rates should exist (may be negative in some cases)
        assert not df['interest_rate'].isna().any()

    def test_recoup_data_chart_valid(self):
        """Test recoup data produces valid chart data."""
        df = calculate_recoup_data(
            original_monthly_payment=2000,
            refi_monthly_payment=1700,
            target_term=360,
            refi_cost=5000,
        )
        # No NaN values
        assert not df['month'].isna().any()
        assert not df['monthly_savings'].isna().any()
        # No infinite values
        assert not np.isinf(df['monthly_savings']).any()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_principal(self):
        """Test calculations with very small principal."""
        result = calc_loan_monthly_payment(1000, 0.05, 360)
        assert result > 0
        assert result < 10  # Very small payment for $1000 loan

    def test_very_large_principal(self):
        """Test calculations with very large principal."""
        result = calc_loan_monthly_payment(10000000, 0.04, 360)
        assert result > 0
        assert result == pytest.approx(47742.64, rel=0.01)

    def test_very_short_term(self):
        """Test calculations with very short term."""
        result = calc_loan_monthly_payment(100000, 0.05, 12)
        assert result > 0
        # Should be high payment for 1-year term
        assert result > 8000

    def test_negative_savings_scenario(self, negative_savings_mortgage_inputs):
        """Test scenario where refinancing has negative savings."""
        original_payment = calc_loan_monthly_payment(
            negative_savings_mortgage_inputs['current_principal'],
            negative_savings_mortgage_inputs['current_rate'],
            negative_savings_mortgage_inputs['current_term'],
        )
        refi_payment = calc_loan_monthly_payment(
            negative_savings_mortgage_inputs['remaining_principal'],
            negative_savings_mortgage_inputs['target_rate'],
            negative_savings_mortgage_inputs['target_term'],
        )
        # Higher rate refinance should have higher payment
        assert refi_payment > original_payment

    def test_nearly_paid_mortgage(self, nearly_paid_mortgage_inputs):
        """Test scenario with nearly paid mortgage."""
        original_payment = calc_loan_monthly_payment(
            nearly_paid_mortgage_inputs['current_principal'],
            nearly_paid_mortgage_inputs['current_rate'],
            nearly_paid_mortgage_inputs['current_term'],
        )
        refi_payment = calc_loan_monthly_payment(
            nearly_paid_mortgage_inputs['remaining_principal'],
            nearly_paid_mortgage_inputs['target_rate'],
            nearly_paid_mortgage_inputs['target_term'],
        )
        # With much lower remaining principal, refi should be much lower
        assert refi_payment < original_payment * 0.5


class TestInputValidation:
    """Tests for input validation and error handling."""

    def test_calc_handles_zero_principal(self):
        """Test calculation handles zero principal."""
        result = calc_loan_monthly_payment(0, 0.05, 360)
        assert result == 0

    def test_calc_handles_zero_term_gracefully(self):
        """Test calculation handles zero term."""
        # This may raise an exception or return special value
        try:
            result = calc_loan_monthly_payment(100000, 0.05, 0)
            # If it doesn't raise, it should handle gracefully
            assert result == 0 or np.isinf(result) or np.isnan(result)
        except (ZeroDivisionError, ValueError):
            # Exception is acceptable behavior
            pass

    def test_calc_handles_negative_rate(self):
        """Test calculation handles negative rate (treated as zero)."""
        result = calc_loan_monthly_payment(100000, -0.05, 360)
        # Negative rate should be treated as zero or handled gracefully
        assert result > 0 or result == 0

    def test_mortgage_range_handles_zero_principal(self):
        """Test mortgage range handles zero principal."""
        df = create_mortage_range(0, 360)
        assert len(df) > 0
        assert (df['monthly_payment'] == 0).all()

    def test_time_to_even_handles_zero_savings(self):
        """Test time to even with zero savings."""
        # This will cause division by zero
        try:
            result = time_to_even(5000, 0)
            assert np.isinf(result)
        except (ZeroDivisionError, FloatingPointError):
            # Exception is acceptable
            pass

    def test_time_to_even_handles_negative_savings(self):
        """Test time to even with negative savings (impossible break-even)."""
        result = time_to_even(5000, -100)
        # Should return negative value indicating impossible break-even
        assert result < 0
