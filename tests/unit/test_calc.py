"""
Comprehensive unit tests for calc.py

Test Coverage Required:
- calc_loan_monthly_payment() - 10 tests
- amount_remaining (calc_amount_remaining) - 8 tests
- create_efficient_frontier() - 15 tests
- find_break_even_interest() - 12 tests
- calculate_recoup_data() - 5 tests
- create_mortage_range() - 5 tests
- Helper functions - 5+ tests

All tests use known values. Tolerance: ±$0.01
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os
import importlib.util

# Load calc.py directly to avoid Flask dependencies in refi_monitor.__init__
# This allows running tests without full Flask stack
calc_path = os.path.join(os.path.dirname(__file__), '..', '..', 'refi_monitor', 'calc.py')
spec = importlib.util.spec_from_file_location('refi_monitor.calc', calc_path)
calc = importlib.util.module_from_spec(spec)
sys.modules['refi_monitor.calc'] = calc  # Register for coverage
spec.loader.exec_module(calc)

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


# Tolerance for floating point comparisons
TOLERANCE = 0.01


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def standard_30yr_loan():
    """Standard 30-year mortgage at 6% on $300,000"""
    return {
        'principal': 300000,
        'rate': 0.06,
        'term': 360,  # 30 years in months
        'expected_monthly': 1798.65,  # Known value
    }


@pytest.fixture
def standard_15yr_loan():
    """Standard 15-year mortgage at 5.5% on $250,000"""
    return {
        'principal': 250000,
        'rate': 0.055,
        'term': 180,  # 15 years in months
        'expected_monthly': 2042.71,  # Known value
    }


@pytest.fixture
def high_rate_loan():
    """High interest rate loan at 8% on $400,000"""
    return {
        'principal': 400000,
        'rate': 0.08,
        'term': 360,
        'expected_monthly': 2935.06,  # Known value
    }


@pytest.fixture
def low_rate_loan():
    """Low interest rate loan at 3% on $200,000"""
    return {
        'principal': 200000,
        'rate': 0.03,
        'term': 360,
        'expected_monthly': 843.21,  # Known value
    }


@pytest.fixture
def refi_scenario():
    """Refinancing scenario for efficient frontier tests"""
    return {
        'original_principal': 300000,
        'original_rate': 0.065,
        'original_term': 360,
        'current_principal': 280000,
        'term_remaining': 324,  # 27 years remaining
        'new_term': 360,
        'refi_cost': 5000,
    }


# =============================================================================
# calc_loan_monthly_payment() - 10 tests
# =============================================================================

class TestCalcLoanMonthlyPayment:
    """Tests for calc_loan_monthly_payment function"""

    def test_standard_30yr_mortgage(self, standard_30yr_loan):
        """Test standard 30-year mortgage calculation"""
        result = calc_loan_monthly_payment(
            standard_30yr_loan['principal'],
            standard_30yr_loan['rate'],
            standard_30yr_loan['term']
        )
        assert abs(result - standard_30yr_loan['expected_monthly']) < TOLERANCE

    def test_standard_15yr_mortgage(self, standard_15yr_loan):
        """Test standard 15-year mortgage calculation"""
        result = calc_loan_monthly_payment(
            standard_15yr_loan['principal'],
            standard_15yr_loan['rate'],
            standard_15yr_loan['term']
        )
        assert abs(result - standard_15yr_loan['expected_monthly']) < TOLERANCE

    def test_high_rate_mortgage(self, high_rate_loan):
        """Test high interest rate mortgage"""
        result = calc_loan_monthly_payment(
            high_rate_loan['principal'],
            high_rate_loan['rate'],
            high_rate_loan['term']
        )
        assert abs(result - high_rate_loan['expected_monthly']) < TOLERANCE

    def test_low_rate_mortgage(self, low_rate_loan):
        """Test low interest rate mortgage"""
        result = calc_loan_monthly_payment(
            low_rate_loan['principal'],
            low_rate_loan['rate'],
            low_rate_loan['term']
        )
        assert abs(result - low_rate_loan['expected_monthly']) < TOLERANCE

    def test_zero_rate_loan(self):
        """Test zero interest rate - should be simple division"""
        principal = 120000
        term = 120  # 10 years
        result = calc_loan_monthly_payment(principal, 0, term)
        expected = principal / term  # 1000
        assert abs(result - expected) < TOLERANCE

    def test_negative_rate_handled(self):
        """Test negative rate is handled (treated as zero rate)"""
        principal = 120000
        term = 120
        result = calc_loan_monthly_payment(principal, -0.01, term)
        expected = principal / term
        assert abs(result - expected) < TOLERANCE

    def test_small_loan_amount(self):
        """Test small loan amount ($10,000)"""
        # $10,000 at 5% for 60 months = ~$188.71/month
        result = calc_loan_monthly_payment(10000, 0.05, 60)
        expected = 188.71
        assert abs(result - expected) < TOLERANCE

    def test_large_loan_amount(self):
        """Test large loan amount ($1,000,000)"""
        # $1M at 6% for 360 months = ~$5995.51/month
        result = calc_loan_monthly_payment(1000000, 0.06, 360)
        expected = 5995.51
        assert abs(result - expected) < TOLERANCE

    def test_short_term_loan(self):
        """Test short term loan (12 months)"""
        # $12,000 at 4% for 12 months
        result = calc_loan_monthly_payment(12000, 0.04, 12)
        expected = 1021.80  # Verified with amortization formula
        assert abs(result - expected) < TOLERANCE

    def test_very_high_rate(self):
        """Test very high interest rate (15%)"""
        # $100,000 at 15% for 360 months = ~$1264.44/month
        result = calc_loan_monthly_payment(100000, 0.15, 360)
        expected = 1264.44
        assert abs(result - expected) < TOLERANCE

    def test_exception_handling(self):
        """Test that exception handler returns 0 on invalid input"""
        # Passing None triggers exception path, returns 0
        result = calc_loan_monthly_payment(None, 0.05, 360)
        assert result == 0


# =============================================================================
# amount_remaining() - 8 tests
# =============================================================================

class TestAmountRemaining:
    """Tests for amount_remaining function"""

    def test_full_term_remaining(self, standard_30yr_loan):
        """Test balance at start of loan (full term remaining)"""
        monthly = calc_loan_monthly_payment(
            standard_30yr_loan['principal'],
            standard_30yr_loan['rate'],
            standard_30yr_loan['term']
        )
        result = amount_remaining(
            standard_30yr_loan['principal'],
            monthly,
            standard_30yr_loan['rate'],
            standard_30yr_loan['term']
        )
        assert abs(result - standard_30yr_loan['principal']) < TOLERANCE

    def test_half_term_remaining(self):
        """Test balance at midpoint of 30-year loan"""
        principal = 300000
        rate = 0.06
        term = 360
        monthly = calc_loan_monthly_payment(principal, rate, term)
        # After 15 years (180 payments remaining)
        result = amount_remaining(principal, monthly, rate, 180)
        expected = 213146.53  # Verified with present value of annuity formula
        assert abs(result - expected) < TOLERANCE

    def test_near_end_of_term(self):
        """Test balance near end of loan (12 months remaining)"""
        principal = 300000
        rate = 0.06
        term = 360
        monthly = calc_loan_monthly_payment(principal, rate, term)
        result = amount_remaining(principal, monthly, rate, 12)
        expected = 20898.41  # Present value of 12 remaining payments
        assert abs(result - expected) < TOLERANCE

    def test_one_payment_remaining(self):
        """Test balance with one payment remaining"""
        principal = 300000
        rate = 0.06
        term = 360
        monthly = calc_loan_monthly_payment(principal, rate, term)
        result = amount_remaining(principal, monthly, rate, 1)
        # Should be close to one monthly payment minus small interest
        assert result > 0
        assert result < monthly * 1.1

    def test_low_rate_balance(self, low_rate_loan):
        """Test balance calculation with low rate"""
        monthly = calc_loan_monthly_payment(
            low_rate_loan['principal'],
            low_rate_loan['rate'],
            low_rate_loan['term']
        )
        # After 5 years (60 payments), 300 remaining
        result = amount_remaining(
            low_rate_loan['principal'],
            monthly,
            low_rate_loan['rate'],
            300
        )
        expected = 177812.73  # Present value of 300 remaining payments at 3%
        assert abs(result - expected) < TOLERANCE

    def test_high_rate_balance(self, high_rate_loan):
        """Test balance calculation with high rate"""
        monthly = calc_loan_monthly_payment(
            high_rate_loan['principal'],
            high_rate_loan['rate'],
            high_rate_loan['term']
        )
        # After 10 years (120 payments), 240 remaining
        result = amount_remaining(
            high_rate_loan['principal'],
            monthly,
            high_rate_loan['rate'],
            240
        )
        expected = 350898.82  # Present value of 240 remaining payments at 8%
        assert abs(result - expected) < TOLERANCE

    def test_15yr_mortgage_balance(self, standard_15yr_loan):
        """Test balance on 15-year mortgage"""
        monthly = calc_loan_monthly_payment(
            standard_15yr_loan['principal'],
            standard_15yr_loan['rate'],
            standard_15yr_loan['term']
        )
        # After 7 years, 96 months remaining
        result = amount_remaining(
            standard_15yr_loan['principal'],
            monthly,
            standard_15yr_loan['rate'],
            96
        )
        expected = 158357.83  # Present value of 96 remaining payments at 5.5%
        assert abs(result - expected) < TOLERANCE

    def test_quarter_term_remaining(self):
        """Test balance at 75% through the loan"""
        principal = 200000
        rate = 0.05
        term = 360
        monthly = calc_loan_monthly_payment(principal, rate, term)
        # 90 months remaining (25% of term left)
        result = amount_remaining(principal, monthly, rate, 90)
        expected = 80439.51  # Present value of 90 remaining payments at 5%
        assert abs(result - expected) < TOLERANCE


# =============================================================================
# create_efficient_frontier() - 15 tests
# =============================================================================

class TestCreateEfficientFrontier:
    """Tests for create_efficient_frontier - the core IP"""

    def test_returns_dataframe(self, refi_scenario):
        """Test that function returns a DataFrame"""
        result = create_efficient_frontier(
            refi_scenario['original_principal'],
            refi_scenario['original_rate'],
            refi_scenario['original_term'],
            refi_scenario['current_principal'],
            refi_scenario['term_remaining'],
            refi_scenario['new_term'],
            refi_scenario['refi_cost'],
        )
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self, refi_scenario):
        """Test that result has all required columns"""
        result = create_efficient_frontier(
            refi_scenario['original_principal'],
            refi_scenario['original_rate'],
            refi_scenario['original_term'],
            refi_scenario['current_principal'],
            refi_scenario['term_remaining'],
            refi_scenario['new_term'],
            refi_scenario['refi_cost'],
        )
        expected_columns = ['month', 'months_remaining', 'amount_remaining',
                          'total_interest_paid', 'new_target_total',
                          'interest_rate', 'total_new_interest']
        for col in expected_columns:
            assert col in result.columns

    def test_correct_row_count(self, refi_scenario):
        """Test that result has correct number of rows (term + 1)"""
        result = create_efficient_frontier(
            refi_scenario['original_principal'],
            refi_scenario['original_rate'],
            refi_scenario['original_term'],
            refi_scenario['current_principal'],
            refi_scenario['term_remaining'],
            refi_scenario['new_term'],
            refi_scenario['refi_cost'],
        )
        assert len(result) == refi_scenario['original_term'] + 1

    def test_month_column_sequential(self, refi_scenario):
        """Test that month column is sequential from 0"""
        result = create_efficient_frontier(
            refi_scenario['original_principal'],
            refi_scenario['original_rate'],
            refi_scenario['original_term'],
            refi_scenario['current_principal'],
            refi_scenario['term_remaining'],
            refi_scenario['new_term'],
            refi_scenario['refi_cost'],
        )
        expected = list(range(refi_scenario['original_term'] + 1))
        assert result['month'].tolist() == expected

    def test_months_remaining_decreases(self, refi_scenario):
        """Test that months_remaining decreases as month increases"""
        result = create_efficient_frontier(
            refi_scenario['original_principal'],
            refi_scenario['original_rate'],
            refi_scenario['original_term'],
            refi_scenario['current_principal'],
            refi_scenario['term_remaining'],
            refi_scenario['new_term'],
            refi_scenario['refi_cost'],
        )
        assert result['months_remaining'].iloc[0] == refi_scenario['original_term']
        assert result['months_remaining'].iloc[-1] == 0
        assert all(result['months_remaining'].diff().dropna() == -1)

    def test_amount_remaining_decreases(self, refi_scenario):
        """Test that amount_remaining generally decreases"""
        result = create_efficient_frontier(
            refi_scenario['original_principal'],
            refi_scenario['original_rate'],
            refi_scenario['original_term'],
            refi_scenario['current_principal'],
            refi_scenario['term_remaining'],
            refi_scenario['new_term'],
            refi_scenario['refi_cost'],
        )
        # Skip first row (month 0), amounts should decrease
        amounts = result['amount_remaining'].iloc[1:-1].values
        assert all(np.diff(amounts) <= 0)

    def test_interest_rate_decreases_over_time(self, refi_scenario):
        """Test break-even rates decrease as loan matures"""
        result = create_efficient_frontier(
            refi_scenario['original_principal'],
            refi_scenario['original_rate'],
            refi_scenario['original_term'],
            refi_scenario['current_principal'],
            refi_scenario['term_remaining'],
            refi_scenario['new_term'],
            refi_scenario['refi_cost'],
        )
        # Early in loan, rate should be higher than later
        early_rate = result['interest_rate'].iloc[12]
        late_rate = result['interest_rate'].iloc[240]
        assert early_rate >= late_rate

    def test_total_interest_paid_increases(self, refi_scenario):
        """Test that total_interest_paid increases over time"""
        result = create_efficient_frontier(
            refi_scenario['original_principal'],
            refi_scenario['original_rate'],
            refi_scenario['original_term'],
            refi_scenario['current_principal'],
            refi_scenario['term_remaining'],
            refi_scenario['new_term'],
            refi_scenario['refi_cost'],
        )
        interest_paid = result['total_interest_paid'].iloc[1:].values
        # Should be non-decreasing
        assert all(np.diff(interest_paid) >= -TOLERANCE)

    def test_with_zero_refi_cost(self):
        """Test frontier with zero refinancing cost"""
        result = create_efficient_frontier(
            300000, 0.06, 360, 280000, 324, 360, 0
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 361

    def test_with_high_refi_cost(self):
        """Test frontier with high refinancing cost"""
        result = create_efficient_frontier(
            300000, 0.06, 360, 280000, 324, 360, 15000
        )
        assert isinstance(result, pd.DataFrame)
        # Higher cost should push break-even rates lower
        result_low = create_efficient_frontier(
            300000, 0.06, 360, 280000, 324, 360, 5000
        )
        # At month 60, high cost scenario needs lower rate
        assert result['interest_rate'].iloc[60] <= result_low['interest_rate'].iloc[60]

    def test_shorter_new_term(self):
        """Test frontier with shorter new term (15 years)"""
        result = create_efficient_frontier(
            300000, 0.06, 360, 280000, 324, 180, 5000
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 361

    def test_high_rate_scenario(self):
        """Test frontier with high original rate"""
        result = create_efficient_frontier(
            300000, 0.08, 360, 290000, 348, 360, 5000
        )
        assert isinstance(result, pd.DataFrame)
        # Higher original rate means more room for savings
        # Break-even rates should be reasonable
        assert result['interest_rate'].iloc[60] > 0

    def test_low_rate_scenario(self):
        """Test frontier with low original rate"""
        result = create_efficient_frontier(
            300000, 0.035, 360, 280000, 324, 360, 5000
        )
        assert isinstance(result, pd.DataFrame)
        # Low original rate means break-even may go below zero

    def test_small_loan_frontier(self):
        """Test frontier with small loan amount"""
        result = create_efficient_frontier(
            100000, 0.06, 360, 95000, 348, 360, 3000
        )
        assert isinstance(result, pd.DataFrame)
        assert 'interest_rate' in result.columns

    def test_large_loan_frontier(self):
        """Test frontier with large loan amount"""
        result = create_efficient_frontier(
            1000000, 0.06, 360, 950000, 348, 360, 10000
        )
        assert isinstance(result, pd.DataFrame)
        assert result['amount_remaining'].iloc[0] > 900000


# =============================================================================
# find_break_even_interest() - 12 tests
# =============================================================================

class TestFindBreakEvenInterest:
    """Tests for find_break_even_interest function"""

    def test_returns_float(self):
        """Test that function returns a float"""
        result = find_break_even_interest(250000, 360, 150000, 0.06)
        assert isinstance(result, float)

    def test_rate_below_current(self):
        """Test that break-even rate is below current rate"""
        current_rate = 0.06
        result = find_break_even_interest(250000, 360, 150000, current_rate)
        assert result <= current_rate

    def test_standard_scenario(self):
        """Test standard break-even scenario"""
        # $250k loan, 30-year term, target $150k total interest, starting at 6%
        result = find_break_even_interest(250000, 360, 150000, 0.06)
        # Result should be a reasonable rate
        assert 0 <= result <= 0.06

    def test_high_target_interest(self):
        """Test with high target (easy to achieve)"""
        # High target = break-even happens at higher rate
        result = find_break_even_interest(250000, 360, 300000, 0.07)
        # Should find rate close to starting rate
        assert result > 0.05

    def test_low_target_interest(self):
        """Test with low target (hard to achieve)"""
        # Low target = need very low rate
        result = find_break_even_interest(250000, 360, 50000, 0.06)
        # Should find low rate or go below zero
        assert result <= 0.03

    def test_short_term_break_even(self):
        """Test break-even with 15-year term"""
        result = find_break_even_interest(200000, 180, 50000, 0.06)
        assert isinstance(result, float)
        assert result < 0.06

    def test_different_increment(self):
        """Test with different increment value"""
        result_fine = find_break_even_interest(250000, 360, 150000, 0.06, 0.0005)
        result_coarse = find_break_even_interest(250000, 360, 150000, 0.06, 0.005)
        # Fine increment should be more precise
        assert abs(result_fine - result_coarse) < 0.005

    def test_small_principal(self):
        """Test with small principal"""
        result = find_break_even_interest(50000, 360, 30000, 0.06)
        assert isinstance(result, float)

    def test_large_principal(self):
        """Test with large principal"""
        result = find_break_even_interest(800000, 360, 400000, 0.06)
        assert isinstance(result, float)
        assert 0 <= result <= 0.06

    def test_exact_target_match(self):
        """Test when target matches current rate total interest"""
        principal = 250000
        term = 360
        rate = 0.05
        # Calculate exact total interest at current rate
        target = ipmt_total(rate, term, principal)
        result = find_break_even_interest(principal, term, target, rate)
        # Should return rate close to current
        assert abs(result - rate) < 0.01

    def test_impossible_target(self):
        """Test with impossible target (negative)"""
        # Target is zero or negative - should hit zero rate
        result = find_break_even_interest(250000, 360, 0, 0.06)
        assert result <= 0

    def test_edge_case_small_difference(self):
        """Test edge case with small rate difference needed"""
        principal = 300000
        term = 360
        current_rate = 0.06
        # Target slightly below current interest
        target = ipmt_total(current_rate, term, principal) * 0.95
        result = find_break_even_interest(principal, term, target, current_rate)
        # Should find rate slightly below current
        assert current_rate - 0.02 < result < current_rate


# =============================================================================
# calculate_recoup_data() - 5 tests
# =============================================================================

class TestCalculateRecoupData:
    """Tests for calculate_recoup_data function"""

    def test_returns_dataframe(self):
        """Test that function returns a DataFrame"""
        result = calculate_recoup_data(2000, 1800, 360, 5000)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self):
        """Test that result has required columns"""
        result = calculate_recoup_data(2000, 1800, 360, 5000)
        assert 'month' in result.columns
        assert 'monthly_savings' in result.columns

    def test_correct_row_count(self):
        """Test correct number of rows"""
        term = 360
        result = calculate_recoup_data(2000, 1800, term, 5000)
        assert len(result) == term + 1

    def test_break_even_month(self):
        """Test that break-even occurs at expected month"""
        original = 2000
        refi = 1800
        cost = 5000
        monthly_savings = original - refi  # $200
        expected_break_even = np.ceil(cost / monthly_savings)  # 25 months

        result = calculate_recoup_data(original, refi, 360, cost)
        # Find first month where savings >= 0
        break_even_idx = (result['monthly_savings'] >= 0).idxmax()
        assert break_even_idx == expected_break_even

    def test_savings_progression(self):
        """Test that savings increase over time"""
        result = calculate_recoup_data(2000, 1800, 360, 5000)
        # Savings should be increasing (linear)
        diffs = result['monthly_savings'].diff().dropna()
        # All differences should be equal (constant monthly savings)
        assert all(abs(diffs - diffs.iloc[0]) < TOLERANCE)


# =============================================================================
# create_mortage_range() - 5 tests
# =============================================================================

class TestCreateMortgageRange:
    """Tests for create_mortage_range function"""

    def test_returns_dataframe(self):
        """Test that function returns a DataFrame"""
        result = create_mortage_range(300000, 360)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self):
        """Test that result has required columns"""
        result = create_mortage_range(300000, 360)
        assert 'rate' in result.columns
        assert 'monthly_payment' in result.columns
        assert 'total_payment' in result.columns

    def test_rate_range(self):
        """Test that rates span correct range"""
        rmax = 0.1
        rstep = 0.00125
        result = create_mortage_range(300000, 360, rmax, rstep)
        assert result['rate'].min() == 0
        assert result['rate'].max() <= rmax + rstep

    def test_custom_rate_params(self):
        """Test with custom rate parameters"""
        result = create_mortage_range(300000, 360, rmax=0.15, rstep=0.005)
        assert result['rate'].max() <= 0.155
        # Step should be 0.005
        rate_diffs = result['rate'].diff().dropna()
        assert all(abs(rate_diffs - 0.005) < 0.0001)

    def test_payment_increases_with_rate(self):
        """Test that payments increase with rate"""
        result = create_mortage_range(300000, 360)
        # Skip first row (rate=0), payments should increase
        payments = result['monthly_payment'].iloc[1:].values
        assert all(np.diff(payments) > 0)


# =============================================================================
# Helper Functions - 8 tests
# =============================================================================

class TestTotalPayment:
    """Tests for total_payment function"""

    def test_basic_calculation(self):
        """Test basic total payment calculation"""
        result = total_payment(1000, 360)
        assert result == 360000

    def test_with_cents(self):
        """Test with payment including cents"""
        result = total_payment(1798.65, 360)
        expected = 1798.65 * 360
        assert abs(result - expected) < TOLERANCE


class TestIpmtTotal:
    """Tests for ipmt_total function"""

    def test_basic_interest_calculation(self):
        """Test basic total interest calculation"""
        # $300k at 6% for 30 years
        result = ipmt_total(0.06, 360, 300000)
        # Total interest should be significant
        expected = 347514.57  # Known value
        assert abs(result - expected) < 1  # Within $1

    def test_with_custom_per(self):
        """Test with custom period array"""
        per = np.arange(60) + 1  # First 5 years
        result = ipmt_total(0.06, 360, 300000, per)
        # Should be less than full term interest
        full_result = ipmt_total(0.06, 360, 300000)
        assert result < full_result


class TestGetPer:
    """Tests for get_per function"""

    def test_basic_per_array(self):
        """Test basic period array generation"""
        result = get_per(12)
        expected = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        assert np.array_equal(result, expected)

    def test_per_length(self):
        """Test period array length"""
        result = get_per(360)
        assert len(result) == 360
        assert result[0] == 1
        assert result[-1] == 360


class TestTimeToEven:
    """Tests for time_to_even function"""

    def test_basic_calculation(self):
        """Test basic break-even time calculation"""
        result = time_to_even(5000, 200)
        assert result == 25

    def test_rounds_up(self):
        """Test that result rounds up"""
        result = time_to_even(5100, 200)
        assert result == 26  # 25.5 rounds up to 26


# =============================================================================
# Additional Edge Case Tests
# =============================================================================

class TestFindTargetInterestRate:
    """Tests for find_target_interest_rate function"""

    def test_basic_target_rate(self):
        """Test finding target interest rate"""
        # Want monthly payment under $1500 for $300k, 30yr
        result = find_target_interest_rate(300000, 360, 1500)
        # At ~4.5%, payment is ~$1520, at 4.375% it's ~$1498
        assert result <= 0.045

    def test_returns_valid_rate(self):
        """Test that returned rate is valid"""
        result = find_target_interest_rate(250000, 360, 1800)
        assert 0 <= result <= 0.185


class TestCreateMortgageTable:
    """Tests for create_mortgage_table function"""

    def test_returns_dataframe(self):
        """Test that function returns a DataFrame"""
        result = create_mortgage_table(300000, 0.06, 360)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self):
        """Test that result has required columns"""
        result = create_mortgage_table(300000, 0.06, 360)
        assert 'month' in result.columns
        assert 'months_remaining' in result.columns
        assert 'amount_remaining' in result.columns

    def test_balance_at_end_near_zero(self):
        """Test that balance at end of term is near zero"""
        result = create_mortgage_table(300000, 0.06, 360)
        final_balance = result['amount_remaining'].iloc[-1]
        assert abs(final_balance) < 1  # Within $1 of zero
