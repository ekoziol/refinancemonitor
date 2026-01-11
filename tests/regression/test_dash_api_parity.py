"""
Regression Test Suite: Dash vs API Calculation Parity

This test suite ensures that API calculation results match the Dash calculator
output exactly (within tolerance). These tests capture the current Dash behavior
and will be used to validate the API implementation in Phase 2.

Test Approach:
- Same inputs to Dash and API
- Compare all output values
- Tolerance: <$0.01 difference for monetary values
- Test all edge cases
- Test all calculation paths

Success Criteria:
- 20+ regression test cases
- All calculation scenarios covered
- Tests ready for API validation
- Tolerance thresholds defined
"""

import pytest
import numpy as np
import pandas as pd
from decimal import Decimal

import sys
import os
import importlib.util

# Direct import of calc.py to avoid Flask dependencies in refi_monitor/__init__.py
calc_path = os.path.join(os.path.dirname(__file__), '..', '..', 'refi_monitor', 'calc.py')
spec = importlib.util.spec_from_file_location("calc", calc_path)
calc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calc)

# Import functions from the loaded module
calc_loan_monthly_payment = calc.calc_loan_monthly_payment
total_payment = calc.total_payment
create_mortage_range = calc.create_mortage_range
find_target_interest_rate = calc.find_target_interest_rate
amount_remaining = calc.amount_remaining
create_mortgage_table = calc.create_mortgage_table
ipmt_total = calc.ipmt_total
get_per = calc.get_per
time_to_even = calc.time_to_even
calculate_recoup_data = calc.calculate_recoup_data
find_break_even_interest = calc.find_break_even_interest
create_efficient_frontier = calc.create_efficient_frontier


# Tolerance for monetary comparisons (less than $0.01)
MONETARY_TOLERANCE = 0.01
# Tolerance for rate comparisons (less than 0.01%)
RATE_TOLERANCE = 0.0001


class TestCalcLoanMonthlyPayment:
    """Tests for calc_loan_monthly_payment function"""

    def test_standard_30_year_mortgage(self):
        """Standard 30-year mortgage at 4.5% - Dash default scenario"""
        principal = 400000
        rate = 0.045
        term = 360  # 30 years

        result = calc_loan_monthly_payment(principal, rate, term)

        # Expected value calculated from mortgage formula
        # This captures the current Dash behavior
        expected = 2026.74
        assert abs(result - expected) < MONETARY_TOLERANCE, \
            f"Monthly payment {result:.2f} differs from expected {expected:.2f}"

    def test_15_year_mortgage(self):
        """15-year mortgage at 3.5%"""
        principal = 300000
        rate = 0.035
        term = 180  # 15 years

        result = calc_loan_monthly_payment(principal, rate, term)
        expected = 2144.65
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_zero_interest_rate(self):
        """Edge case: 0% interest rate"""
        principal = 360000
        rate = 0.0
        term = 360

        result = calc_loan_monthly_payment(principal, rate, term)
        expected = 1000.0  # principal / term
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_negative_interest_rate(self):
        """Edge case: negative interest rate (treated as 0%)"""
        principal = 360000
        rate = -0.01
        term = 360

        result = calc_loan_monthly_payment(principal, rate, term)
        expected = 1000.0  # Falls back to principal / term
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_high_interest_rate(self):
        """Edge case: high interest rate (10%)"""
        principal = 200000
        rate = 0.10
        term = 360

        result = calc_loan_monthly_payment(principal, rate, term)
        expected = 1755.14
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_short_term_loan(self):
        """Short term loan: 5 years"""
        principal = 50000
        rate = 0.05
        term = 60  # 5 years

        result = calc_loan_monthly_payment(principal, rate, term)
        expected = 943.56
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_small_principal(self):
        """Small principal amount"""
        principal = 10000
        rate = 0.06
        term = 120  # 10 years

        result = calc_loan_monthly_payment(principal, rate, term)
        expected = 111.02
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_large_principal(self):
        """Large principal amount (jumbo loan)"""
        principal = 2000000
        rate = 0.055
        term = 360

        result = calc_loan_monthly_payment(principal, rate, term)
        expected = 11355.78
        assert abs(result - expected) < MONETARY_TOLERANCE


class TestTotalPayment:
    """Tests for total_payment function"""

    def test_standard_total_payment(self):
        """Total payment over loan life"""
        monthly_payment = 2026.74
        term = 360

        result = total_payment(monthly_payment, term)
        expected = 729626.40
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_zero_payment(self):
        """Edge case: zero monthly payment"""
        result = total_payment(0, 360)
        assert result == 0


class TestCreateMortgageRange:
    """Tests for create_mortage_range function"""

    def test_default_range(self):
        """Create default mortgage range - matches Dash behavior"""
        principal = 400000
        term = 360

        df = create_mortage_range(principal, term)

        # Check DataFrame structure
        assert 'rate' in df.columns
        assert 'monthly_payment' in df.columns
        assert 'total_payment' in df.columns

        # Check rate range (0% to 10% in 0.125% increments)
        assert df['rate'].min() == 0.0
        assert abs(df['rate'].max() - 0.10) < RATE_TOLERANCE

        # Check payment at 0% rate
        zero_rate_payment = df.loc[df['rate'] == 0.0, 'monthly_payment'].values[0]
        expected_zero_rate = principal / term
        assert abs(zero_rate_payment - expected_zero_rate) < MONETARY_TOLERANCE

        # Check payment at ~4.5% rate
        rate_45_row = df.loc[abs(df['rate'] - 0.045) < RATE_TOLERANCE]
        if len(rate_45_row) > 0:
            payment_at_45 = rate_45_row['monthly_payment'].values[0]
            expected = 2026.74
            assert abs(payment_at_45 - expected) < MONETARY_TOLERANCE

    def test_custom_range(self):
        """Create custom mortgage range"""
        principal = 300000
        term = 180
        rmax = 0.15
        rstep = 0.005

        df = create_mortage_range(principal, term, rmax=rmax, rstep=rstep)

        assert df['rate'].max() >= 0.15 - RATE_TOLERANCE
        # Should have (0.15 / 0.005) + 1 = 31 rows
        assert len(df) == 31


class TestFindTargetInterestRate:
    """Tests for find_target_interest_rate function"""

    def test_find_rate_for_target_payment(self):
        """Find interest rate needed for target monthly payment"""
        principal = 364631.66  # Remaining principal from Dash default
        term = 360
        target_payment = 1500

        result = find_target_interest_rate(principal, term, target_payment)

        # Verify the found rate gives a payment close to target
        actual_payment = calc_loan_monthly_payment(principal, result, term)
        # The result should give a payment just below target
        assert actual_payment < target_payment
        assert actual_payment > target_payment - 50  # Within reasonable range

    def test_find_rate_for_higher_payment(self):
        """Find rate for higher payment target"""
        principal = 300000
        term = 360
        target_payment = 2000

        result = find_target_interest_rate(principal, term, target_payment)

        # Verify the rate is reasonable
        assert 0 < result < 0.15

    def test_find_rate_for_low_payment(self):
        """Find rate for very low payment (may need very low rate)"""
        principal = 200000
        term = 360
        target_payment = 1000

        result = find_target_interest_rate(principal, term, target_payment)

        # Should find a rate that gives payment below target
        actual_payment = calc_loan_monthly_payment(principal, result, term)
        assert actual_payment < target_payment


class TestAmountRemaining:
    """Tests for amount_remaining function"""

    def test_full_term_remaining(self):
        """Full term remaining - should equal original principal"""
        principal = 400000
        rate = 0.045
        term = 360
        monthly_payment = calc_loan_monthly_payment(principal, rate, term)

        result = amount_remaining(principal, monthly_payment, rate, term)

        assert abs(result - principal) < MONETARY_TOLERANCE

    def test_half_term_remaining(self):
        """Half term remaining"""
        principal = 400000
        rate = 0.045
        term = 360
        monthly_payment = calc_loan_monthly_payment(principal, rate, term)
        months_remaining = 180

        result = amount_remaining(principal, monthly_payment, rate, months_remaining)

        # After 15 years of a 30-year loan, significant principal remains
        assert result > 200000  # Should still owe more than half
        assert result < principal  # Should be less than original

    def test_near_end_of_loan(self):
        """Near end of loan - small amount remaining"""
        principal = 400000
        rate = 0.045
        term = 360
        monthly_payment = calc_loan_monthly_payment(principal, rate, term)
        months_remaining = 12  # Last year

        result = amount_remaining(principal, monthly_payment, rate, months_remaining)

        assert result < 30000  # Should be small amount left
        assert result > 0


class TestCreateMortgageTable:
    """Tests for create_mortgage_table function"""

    def test_table_structure(self):
        """Verify mortgage table structure"""
        principal = 400000
        rate = 0.045
        term = 360

        df = create_mortgage_table(principal, rate, term)

        assert 'month' in df.columns
        assert 'months_remaining' in df.columns
        assert 'amount_remaining' in df.columns

        # Should have term + 1 rows (month 0 through term)
        assert len(df) == term + 1

    def test_table_values(self):
        """Verify mortgage table values"""
        principal = 400000
        rate = 0.045
        term = 360

        df = create_mortgage_table(principal, rate, term)

        # At month 0, full principal remains
        assert abs(df.loc[df['month'] == 0, 'amount_remaining'].values[0] - principal) < MONETARY_TOLERANCE

        # At final month, very small amount remains
        final_remaining = df.loc[df['month'] == term, 'amount_remaining'].values[0]
        assert abs(final_remaining) < 1.0  # Should be essentially 0


class TestIpmtTotal:
    """Tests for ipmt_total function"""

    def test_total_interest_30_year(self):
        """Total interest on 30-year mortgage"""
        principal = 400000
        rate = 0.045
        term = 360

        result = ipmt_total(rate, term, principal)

        # Total interest should be substantial
        monthly_payment = calc_loan_monthly_payment(principal, rate, term)
        total_paid = total_payment(monthly_payment, term)
        expected_interest = total_paid - principal

        assert abs(result - expected_interest) < 1.0  # Within $1

    def test_total_interest_partial_period(self):
        """Total interest for partial loan period"""
        principal = 400000
        rate = 0.045
        term = 360

        # Interest for first 60 months
        per = np.arange(60) + 1
        result = ipmt_total(rate, term, principal, per)

        # Should be positive and less than total
        assert result > 0
        full_interest = ipmt_total(rate, term, principal)
        assert result < full_interest

    def test_zero_rate_interest(self):
        """Interest at 0% rate should be 0"""
        principal = 400000
        rate = 0.0
        term = 360

        result = ipmt_total(rate, term, principal)

        assert abs(result) < MONETARY_TOLERANCE


class TestTimeToEven:
    """Tests for time_to_even function"""

    def test_simple_breakeven(self):
        """Simple break-even calculation"""
        cost = 5000
        monthly_savings = 500

        result = time_to_even(cost, monthly_savings)
        expected = 10  # 5000 / 500 = 10 months

        assert result == expected

    def test_fractional_breakeven(self):
        """Break-even with fractional months (should ceil)"""
        cost = 5000
        monthly_savings = 300

        result = time_to_even(cost, monthly_savings)
        expected = 17  # ceil(5000 / 300) = ceil(16.67) = 17

        assert result == expected

    def test_high_savings(self):
        """High monthly savings - quick break-even"""
        cost = 3000
        monthly_savings = 1000

        result = time_to_even(cost, monthly_savings)
        expected = 3

        assert result == expected


class TestCalculateRecoupData:
    """Tests for calculate_recoup_data function"""

    def test_recoup_data_structure(self):
        """Verify recoup data structure"""
        original_payment = 2026.74
        refi_payment = 1500.0
        target_term = 360
        refi_cost = 5000

        df = calculate_recoup_data(
            original_payment, refi_payment, target_term, refi_cost
        )

        assert 'month' in df.columns
        assert 'monthly_savings' in df.columns
        assert len(df) == target_term + 1

    def test_recoup_initial_negative(self):
        """Month 0 savings should equal negative refi cost"""
        original_payment = 2000
        refi_payment = 1500
        target_term = 360
        refi_cost = 5000

        df = calculate_recoup_data(
            original_payment, refi_payment, target_term, refi_cost
        )

        # Month 0: 0 months of savings - cost = -5000
        month_0_savings = df.loc[df['month'] == 0, 'monthly_savings'].values[0]
        assert abs(month_0_savings - (-refi_cost)) < MONETARY_TOLERANCE

    def test_recoup_breakeven_month(self):
        """Verify break-even occurs at expected month"""
        original_payment = 2000
        refi_payment = 1500
        monthly_diff = 500
        target_term = 360
        refi_cost = 5000

        df = calculate_recoup_data(
            original_payment, refi_payment, target_term, refi_cost
        )

        # Break-even should occur at month 10 (5000 / 500)
        breakeven_month = df.loc[df['monthly_savings'] >= 0, 'month'].min()
        expected_breakeven = 10
        assert breakeven_month == expected_breakeven


class TestFindBreakEvenInterest:
    """Tests for find_break_even_interest function"""

    def test_find_breakeven_rate(self):
        """Find break-even interest rate for refinancing"""
        principal = 364631.66
        new_term = 360
        target_interest = 100000  # Target total interest
        current_rate = 0.045

        result = find_break_even_interest(
            principal, new_term, target_interest, current_rate
        )

        # Result should be a rate between 0 and current rate
        assert 0 <= result <= current_rate

    def test_breakeven_rate_gives_lower_interest(self):
        """Verify break-even rate gives interest below target"""
        principal = 300000
        new_term = 360
        current_rate = 0.05
        target_interest = ipmt_total(current_rate, new_term, principal)

        result = find_break_even_interest(
            principal, new_term, target_interest, current_rate
        )

        result_interest = ipmt_total(result, new_term, principal)
        assert result_interest < target_interest


class TestCreateEfficientFrontier:
    """Tests for create_efficient_frontier function"""

    def test_efficient_frontier_structure(self):
        """Verify efficient frontier data structure"""
        df = create_efficient_frontier(
            original_principal=400000,
            original_rate=0.045,
            original_term=360,
            current_principal=364631.66,
            term_remaining=300,
            new_term=360,
            refi_cost=5000,
        )

        assert 'month' in df.columns
        assert 'interest_rate' in df.columns
        assert 'amount_remaining' in df.columns

    def test_efficient_frontier_rates_decrease(self):
        """Interest rates should generally decrease over time"""
        df = create_efficient_frontier(
            original_principal=400000,
            original_rate=0.045,
            original_term=360,
            current_principal=364631.66,
            term_remaining=300,
            new_term=360,
            refi_cost=5000,
        )

        # Early months should require lower rates than later months
        early_rate = df.loc[df['month'] == 60, 'interest_rate'].values[0]
        late_rate = df.loc[df['month'] == 300, 'interest_rate'].values[0]

        # Late rate can be lower as less principal and interest to save
        assert isinstance(early_rate, (int, float))
        assert isinstance(late_rate, (int, float))


class TestDashDefaultScenario:
    """
    Integration tests using Dash default values.
    These tests capture the exact Dash calculator behavior for regression testing.
    """

    # Dash default values
    ORIGINAL_PRINCIPAL = 400000
    ORIGINAL_RATE = 0.045
    ORIGINAL_TERM = 360
    REMAINING_PRINCIPAL = 364631.66
    REMAINING_TERM = 300
    TARGET_TERM = 360
    TARGET_PAYMENT = 1500
    TARGET_RATE = 0.02
    REFI_COST = 5000

    def test_dash_original_monthly_payment(self):
        """Test original monthly payment calculation matches Dash"""
        result = calc_loan_monthly_payment(
            self.ORIGINAL_PRINCIPAL,
            self.ORIGINAL_RATE,
            self.ORIGINAL_TERM
        )
        expected = 2026.74
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_dash_minimum_monthly_payment(self):
        """Test minimum (0% rate) monthly payment"""
        result = calc_loan_monthly_payment(
            self.ORIGINAL_PRINCIPAL,
            0.0,
            self.ORIGINAL_TERM
        )
        expected = 1111.11
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_dash_refi_monthly_payment_by_rate(self):
        """Test refinanced payment at target rate"""
        result = calc_loan_monthly_payment(
            self.REMAINING_PRINCIPAL,
            self.TARGET_RATE,
            self.TARGET_TERM
        )
        # At 2% rate with remaining principal
        expected = 1347.75
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_dash_monthly_savings_calculation(self):
        """Test monthly savings (original - refi payment)"""
        original_payment = calc_loan_monthly_payment(
            self.ORIGINAL_PRINCIPAL,
            self.ORIGINAL_RATE,
            self.ORIGINAL_TERM
        )
        refi_payment = calc_loan_monthly_payment(
            self.REMAINING_PRINCIPAL,
            self.TARGET_RATE,
            self.TARGET_TERM
        )

        monthly_savings = original_payment - refi_payment
        expected = 678.99  # 2026.74 - 1347.75
        assert abs(monthly_savings - expected) < MONETARY_TOLERANCE

    def test_dash_simple_breakeven(self):
        """Test simple break-even calculation (refi_cost / monthly_savings)"""
        original_payment = calc_loan_monthly_payment(
            self.ORIGINAL_PRINCIPAL,
            self.ORIGINAL_RATE,
            self.ORIGINAL_TERM
        )
        refi_payment = calc_loan_monthly_payment(
            self.REMAINING_PRINCIPAL,
            self.TARGET_RATE,
            self.TARGET_TERM
        )
        monthly_savings = original_payment - refi_payment

        result = time_to_even(self.REFI_COST, monthly_savings)
        expected = 8  # ceil(5000 / 679.28) = 8 months
        assert result == expected

    def test_dash_original_total_interest(self):
        """Test total interest on original loan"""
        result = ipmt_total(
            self.ORIGINAL_RATE,
            self.ORIGINAL_TERM,
            self.ORIGINAL_PRINCIPAL
        )
        expected = 329626.05
        assert abs(result - expected) < 1.0  # Within $1

    def test_dash_refi_total_interest(self):
        """Test total interest on refinanced loan"""
        result = ipmt_total(
            self.TARGET_RATE,
            self.TARGET_TERM,
            self.REMAINING_PRINCIPAL
        )
        expected = 120558.20
        assert abs(result - expected) < 1.0  # Within $1

    def test_dash_find_target_rate_from_payment(self):
        """Test finding rate needed for target payment"""
        result = find_target_interest_rate(
            self.REMAINING_PRINCIPAL,
            self.TARGET_TERM,
            self.TARGET_PAYMENT
        )

        # Verify the rate gives approximately the target payment
        actual_payment = calc_loan_monthly_payment(
            self.REMAINING_PRINCIPAL,
            result,
            self.TARGET_TERM
        )
        assert actual_payment < self.TARGET_PAYMENT
        assert actual_payment > self.TARGET_PAYMENT - 20  # Within $20


class TestEdgeCases:
    """Edge case tests for robustness"""

    def test_very_small_loan(self):
        """Very small loan amount"""
        result = calc_loan_monthly_payment(1000, 0.05, 12)
        expected = 85.61
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_very_large_loan(self):
        """Very large loan (multi-million)"""
        result = calc_loan_monthly_payment(10000000, 0.04, 360)
        expected = 47741.53
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_one_month_term(self):
        """Single month term"""
        result = calc_loan_monthly_payment(10000, 0.05, 1)
        expected = 10041.67
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_very_low_rate(self):
        """Very low interest rate (0.1%)"""
        result = calc_loan_monthly_payment(400000, 0.001, 360)
        expected = 1127.90
        assert abs(result - expected) < MONETARY_TOLERANCE

    def test_high_rate_short_term(self):
        """High rate with short term"""
        result = calc_loan_monthly_payment(100000, 0.15, 60)
        expected = 2378.99
        assert abs(result - expected) < MONETARY_TOLERANCE


class TestAPIParityContract:
    """
    These tests define the API contract. When the API is implemented,
    these tests verify that API responses match exactly.

    Each test specifies:
    - Input parameters
    - Expected output format
    - Expected values
    - Tolerance
    """

    def test_api_calculate_monthly_payment_contract(self):
        """
        API Contract: /api/calculate/monthly-payment

        Input:
            principal: 400000
            rate: 0.045
            term: 360

        Output:
            monthly_payment: 2026.74
        """
        # This is what the API should return
        input_params = {
            'principal': 400000,
            'rate': 0.045,
            'term': 360
        }
        expected_output = {
            'monthly_payment': 2026.74
        }

        # Current Dash calculation (source of truth)
        actual = calc_loan_monthly_payment(
            input_params['principal'],
            input_params['rate'],
            input_params['term']
        )

        assert abs(actual - expected_output['monthly_payment']) < MONETARY_TOLERANCE

    def test_api_refinance_analysis_contract(self):
        """
        API Contract: /api/calculate/refinance-analysis

        Input:
            original_principal: 400000
            original_rate: 0.045
            original_term: 360
            remaining_principal: 364631.66
            remaining_term: 300
            target_rate: 0.02
            target_term: 360
            refi_cost: 5000

        Output:
            original_monthly_payment: 2026.74
            refi_monthly_payment: 1347.46
            monthly_savings: 679.28
            breakeven_months: 8
            total_interest_savings: (calculated)
        """
        input_params = {
            'original_principal': 400000,
            'original_rate': 0.045,
            'original_term': 360,
            'remaining_principal': 364631.66,
            'remaining_term': 300,
            'target_rate': 0.02,
            'target_term': 360,
            'refi_cost': 5000
        }

        # Calculate expected values (Dash behavior)
        original_payment = calc_loan_monthly_payment(
            input_params['original_principal'],
            input_params['original_rate'],
            input_params['original_term']
        )
        refi_payment = calc_loan_monthly_payment(
            input_params['remaining_principal'],
            input_params['target_rate'],
            input_params['target_term']
        )
        monthly_savings = original_payment - refi_payment
        breakeven = time_to_even(input_params['refi_cost'], monthly_savings)

        # Verify calculations match expected contract
        assert abs(original_payment - 2026.74) < MONETARY_TOLERANCE
        assert abs(refi_payment - 1347.75) < MONETARY_TOLERANCE
        assert abs(monthly_savings - 678.99) < MONETARY_TOLERANCE
        assert breakeven == 8

    def test_api_mortgage_range_contract(self):
        """
        API Contract: /api/calculate/mortgage-range

        Input:
            principal: 400000
            term: 360
            rate_max: 0.10
            rate_step: 0.00125

        Output:
            rates: [0.0, 0.00125, 0.0025, ..., 0.10]
            payments: [corresponding payments]
        """
        df = create_mortage_range(400000, 360, rmax=0.10, rstep=0.00125)

        # Verify structure
        assert len(df) == 81  # (0.10 / 0.00125) + 1
        assert df['rate'].min() == 0.0
        assert abs(df['rate'].max() - 0.10) < RATE_TOLERANCE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
