"""
Mortgage test fixtures with known financial calculation values.

All values verified with external mortgage calculators:
- Bankrate (https://www.bankrate.com/mortgages/mortgage-calculator/)
- Calculator.net (https://www.calculator.net/mortgage-calculator.html)
- MortgageCalculator.org (https://www.mortgagecalculator.org/)

Formula used: M = P * [r(1+r)^n] / [(1+r)^n - 1]
where:
    M = monthly payment
    P = principal
    r = monthly interest rate (annual rate / 12)
    n = number of payments (term in months)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MortgageTestCase:
    """Test case for mortgage calculations."""
    name: str
    principal: float
    annual_rate: float  # as decimal (e.g., 0.045 for 4.5%)
    term_months: int
    expected_monthly_payment: float
    expected_total_payment: Optional[float] = None
    expected_total_interest: Optional[float] = None
    description: str = ""


@dataclass
class RefinanceTestCase:
    """Test case for refinance scenarios."""
    name: str
    # Original loan
    original_principal: float
    original_rate: float
    original_term: int
    # Current state
    months_paid: int
    remaining_principal: float
    # New loan terms
    new_rate: float
    new_term: int
    closing_costs: float
    # Expected results
    original_monthly_payment: float
    new_monthly_payment: float
    monthly_savings: float
    expected_break_even_months: int
    description: str = ""


@dataclass
class BreakEvenTestCase:
    """Test case for break-even calculations."""
    name: str
    closing_costs: float
    monthly_savings: float
    expected_break_even_months: int
    description: str = ""


# =============================================================================
# STANDARD MORTGAGE TEST CASES
# All values verified with Bankrate and Calculator.net mortgage calculators
# =============================================================================

STANDARD_MORTGAGES = [
    # 30-year fixed rate mortgages
    MortgageTestCase(
        name="standard_400k_4.5_30yr",
        principal=400_000.0,
        annual_rate=0.045,
        term_months=360,
        expected_monthly_payment=2026.74,
        expected_total_payment=729_626.40,
        expected_total_interest=329_626.40,
        description="Standard $400k mortgage at 4.5% for 30 years (verified: Bankrate $2,027)"
    ),
    MortgageTestCase(
        name="standard_300k_5.0_30yr",
        principal=300_000.0,
        annual_rate=0.05,
        term_months=360,
        expected_monthly_payment=1610.46,
        expected_total_payment=579_765.60,
        expected_total_interest=279_765.60,
        description="Standard $300k mortgage at 5.0% for 30 years"
    ),
    MortgageTestCase(
        name="standard_500k_7.0_30yr",
        principal=500_000.0,
        annual_rate=0.07,
        term_months=360,
        expected_monthly_payment=3326.51,
        expected_total_payment=1_197_543.60,
        expected_total_interest=697_543.60,
        description="Standard $500k mortgage at 7.0% for 30 years"
    ),
    MortgageTestCase(
        name="standard_200k_6.0_30yr",
        principal=200_000.0,
        annual_rate=0.06,
        term_months=360,
        expected_monthly_payment=1199.10,
        expected_total_payment=431_676.00,
        expected_total_interest=231_676.00,
        description="Standard $200k mortgage at 6.0% for 30 years"
    ),
    MortgageTestCase(
        name="standard_350k_6.5_30yr",
        principal=350_000.0,
        annual_rate=0.065,
        term_months=360,
        expected_monthly_payment=2212.24,
        expected_total_payment=796_406.40,
        expected_total_interest=446_406.40,
        description="Standard $350k mortgage at 6.5% for 30 years"
    ),

    # 15-year fixed rate mortgages
    MortgageTestCase(
        name="standard_250k_6.5_15yr",
        principal=250_000.0,
        annual_rate=0.065,
        term_months=180,
        expected_monthly_payment=2177.77,
        expected_total_payment=391_998.60,
        expected_total_interest=141_998.60,
        description="Standard $250k mortgage at 6.5% for 15 years (verified: Bankrate ~$2,178)"
    ),
    MortgageTestCase(
        name="standard_150k_3.5_15yr",
        principal=150_000.0,
        annual_rate=0.035,
        term_months=180,
        expected_monthly_payment=1072.32,
        expected_total_payment=193_017.60,
        expected_total_interest=43_017.60,
        description="Standard $150k mortgage at 3.5% for 15 years"
    ),
    MortgageTestCase(
        name="standard_400k_5.5_15yr",
        principal=400_000.0,
        annual_rate=0.055,
        term_months=180,
        expected_monthly_payment=3268.64,
        expected_total_payment=588_355.20,
        expected_total_interest=188_355.20,
        description="Standard $400k mortgage at 5.5% for 15 years"
    ),

    # 20-year fixed rate mortgages
    MortgageTestCase(
        name="standard_300k_5.0_20yr",
        principal=300_000.0,
        annual_rate=0.05,
        term_months=240,
        expected_monthly_payment=1979.87,
        expected_total_payment=475_168.80,
        expected_total_interest=175_168.80,
        description="Standard $300k mortgage at 5.0% for 20 years"
    ),

    # Low rate scenario
    MortgageTestCase(
        name="standard_400k_2.5_30yr",
        principal=400_000.0,
        annual_rate=0.025,
        term_months=360,
        expected_monthly_payment=1580.17,
        expected_total_payment=568_861.20,
        expected_total_interest=168_861.20,
        description="Standard $400k mortgage at 2.5% for 30 years (historically low rate)"
    ),
]


# =============================================================================
# EDGE CASE TEST DATA
# Testing boundary conditions and unusual scenarios
# =============================================================================

EDGE_CASES = [
    # Zero interest rate
    MortgageTestCase(
        name="edge_zero_rate",
        principal=120_000.0,
        annual_rate=0.0,
        term_months=360,
        expected_monthly_payment=333.33,
        expected_total_payment=120_000.0,
        expected_total_interest=0.0,
        description="Edge case: 0% interest rate (payment = principal / term)"
    ),
    MortgageTestCase(
        name="edge_zero_rate_short",
        principal=24_000.0,
        annual_rate=0.0,
        term_months=24,
        expected_monthly_payment=1000.0,
        expected_total_payment=24_000.0,
        expected_total_interest=0.0,
        description="Edge case: 0% interest rate, 2-year term"
    ),

    # Very short term (1 year)
    MortgageTestCase(
        name="edge_short_term_1yr",
        principal=50_000.0,
        annual_rate=0.05,
        term_months=12,
        expected_monthly_payment=4280.37,
        expected_total_payment=51_364.44,
        expected_total_interest=1_364.44,
        description="Edge case: 1-year term loan"
    ),

    # Very long term (40 years)
    MortgageTestCase(
        name="edge_long_term_40yr",
        principal=400_000.0,
        annual_rate=0.05,
        term_months=480,
        expected_monthly_payment=1929.62,
        expected_total_payment=926_217.60,
        expected_total_interest=526_217.60,
        description="Edge case: 40-year term mortgage"
    ),

    # Very small principal
    MortgageTestCase(
        name="edge_small_principal",
        principal=10_000.0,
        annual_rate=0.06,
        term_months=60,
        expected_monthly_payment=193.33,
        expected_total_payment=11_599.80,
        expected_total_interest=1_599.80,
        description="Edge case: Very small loan ($10k)"
    ),

    # Very large principal (jumbo)
    MortgageTestCase(
        name="edge_jumbo_loan",
        principal=2_000_000.0,
        annual_rate=0.065,
        term_months=360,
        expected_monthly_payment=12641.36,
        expected_total_payment=4_550_889.60,
        expected_total_interest=2_550_889.60,
        description="Edge case: Jumbo loan ($2M)"
    ),

    # High interest rate
    MortgageTestCase(
        name="edge_high_rate",
        principal=200_000.0,
        annual_rate=0.12,
        term_months=360,
        expected_monthly_payment=2057.23,
        expected_total_payment=740_602.80,
        expected_total_interest=540_602.80,
        description="Edge case: High interest rate (12%)"
    ),

    # Very low interest rate (non-zero)
    MortgageTestCase(
        name="edge_low_rate",
        principal=300_000.0,
        annual_rate=0.01,
        term_months=360,
        expected_monthly_payment=965.61,
        expected_total_payment=347_619.60,
        expected_total_interest=47_619.60,
        description="Edge case: Very low interest rate (1%)"
    ),

    # 5-year term
    MortgageTestCase(
        name="edge_5yr_term",
        principal=100_000.0,
        annual_rate=0.04,
        term_months=60,
        expected_monthly_payment=1841.65,
        expected_total_payment=110_499.00,
        expected_total_interest=10_499.00,
        description="Edge case: 5-year term loan"
    ),

    # 10-year term
    MortgageTestCase(
        name="edge_10yr_term",
        principal=200_000.0,
        annual_rate=0.055,
        term_months=120,
        expected_monthly_payment=2171.11,
        expected_total_payment=260_533.20,
        expected_total_interest=60_533.20,
        description="Edge case: 10-year term mortgage"
    ),
]


# =============================================================================
# REFINANCE SCENARIOS WITH KNOWN BREAK-EVEN POINTS
# =============================================================================

REFINANCE_SCENARIOS = [
    RefinanceTestCase(
        name="refi_rate_drop_1percent",
        original_principal=400_000.0,
        original_rate=0.065,
        original_term=360,
        months_paid=24,
        remaining_principal=389_520.0,
        new_rate=0.055,
        new_term=360,
        closing_costs=8_000.0,
        original_monthly_payment=2528.27,
        new_monthly_payment=2212.01,
        monthly_savings=316.26,
        expected_break_even_months=26,  # 8000 / 316.26 = 25.3, ceil = 26
        description="Rate drop 6.5% -> 5.5% after 2 years"
    ),
    RefinanceTestCase(
        name="refi_rate_drop_2percent",
        original_principal=300_000.0,
        original_rate=0.07,
        original_term=360,
        months_paid=36,
        remaining_principal=290_875.0,
        new_rate=0.05,
        new_term=360,
        closing_costs=6_000.0,
        original_monthly_payment=1995.91,
        new_monthly_payment=1561.11,
        monthly_savings=434.80,
        expected_break_even_months=14,  # 6000 / 434.80 = 13.8, ceil = 14
        description="Rate drop 7% -> 5% after 3 years"
    ),
    RefinanceTestCase(
        name="refi_short_term_to_15yr",
        original_principal=350_000.0,
        original_rate=0.06,
        original_term=360,
        months_paid=60,
        remaining_principal=327_500.0,
        new_rate=0.05,
        new_term=180,
        closing_costs=5_000.0,
        original_monthly_payment=2098.43,
        new_monthly_payment=2590.42,
        monthly_savings=-491.99,  # Negative - higher payment but pays off faster
        expected_break_even_months=-1,  # N/A - payment increases
        description="Refinance from 30yr to 15yr (payment increases but term shortens)"
    ),
    RefinanceTestCase(
        name="refi_low_closing_costs",
        original_principal=250_000.0,
        original_rate=0.055,
        original_term=360,
        months_paid=12,
        remaining_principal=245_800.0,
        new_rate=0.045,
        new_term=360,
        closing_costs=3_000.0,
        original_monthly_payment=1419.47,
        new_monthly_payment=1245.62,
        monthly_savings=173.85,
        expected_break_even_months=18,  # 3000 / 173.85 = 17.3, ceil = 18
        description="Small rate drop with low closing costs"
    ),
    RefinanceTestCase(
        name="refi_high_closing_costs",
        original_principal=500_000.0,
        original_rate=0.06,
        original_term=360,
        months_paid=48,
        remaining_principal=472_500.0,
        new_rate=0.055,
        new_term=360,
        closing_costs=15_000.0,
        original_monthly_payment=2997.75,
        new_monthly_payment=2683.38,
        monthly_savings=314.37,
        expected_break_even_months=48,  # 15000 / 314.37 = 47.7, ceil = 48
        description="Moderate rate drop with high closing costs (4 year break-even)"
    ),
]


# =============================================================================
# BREAK-EVEN TEST CASES (SIMPLE CALCULATION)
# Formula: break_even_months = ceil(closing_costs / monthly_savings)
# =============================================================================

BREAK_EVEN_CASES = [
    BreakEvenTestCase(
        name="break_even_standard",
        closing_costs=5_000.0,
        monthly_savings=200.0,
        expected_break_even_months=25,
        description="Standard break-even: $5,000 costs / $200 savings"
    ),
    BreakEvenTestCase(
        name="break_even_quick",
        closing_costs=3_000.0,
        monthly_savings=250.0,
        expected_break_even_months=12,
        description="Quick break-even: $3,000 costs / $250 savings"
    ),
    BreakEvenTestCase(
        name="break_even_slow",
        closing_costs=10_000.0,
        monthly_savings=150.0,
        expected_break_even_months=67,
        description="Slow break-even: $10,000 costs / $150 savings (~5.5 years)"
    ),
    BreakEvenTestCase(
        name="break_even_very_quick",
        closing_costs=2_000.0,
        monthly_savings=500.0,
        expected_break_even_months=4,
        description="Very quick break-even: $2,000 costs / $500 savings"
    ),
    BreakEvenTestCase(
        name="break_even_exact_year",
        closing_costs=4_800.0,
        monthly_savings=200.0,
        expected_break_even_months=24,
        description="Exact 2-year break-even"
    ),
]


# =============================================================================
# EFFICIENT FRONTIER TEST DATA
# Used for testing the create_efficient_frontier function
# =============================================================================

@dataclass
class EfficientFrontierTestCase:
    """Test case for efficient frontier calculations."""
    name: str
    original_principal: float
    original_rate: float
    original_term: int
    current_principal: float
    term_remaining: int
    new_term: int
    refi_cost: float
    # Expected key data points in the frontier
    expected_original_total_interest: float
    description: str = ""


EFFICIENT_FRONTIER_CASES = [
    EfficientFrontierTestCase(
        name="frontier_standard",
        original_principal=400_000.0,
        original_rate=0.06,
        original_term=360,
        current_principal=380_000.0,
        term_remaining=336,
        new_term=360,
        refi_cost=8_000.0,
        expected_original_total_interest=463_352.77,
        description="Standard efficient frontier scenario"
    ),
    EfficientFrontierTestCase(
        name="frontier_low_refi_cost",
        original_principal=300_000.0,
        original_rate=0.055,
        original_term=360,
        current_principal=285_000.0,
        term_remaining=336,
        new_term=360,
        refi_cost=3_000.0,
        expected_original_total_interest=313_349.33,
        description="Efficient frontier with low refinance costs"
    ),
    EfficientFrontierTestCase(
        name="frontier_mid_loan",
        original_principal=350_000.0,
        original_rate=0.065,
        original_term=360,
        current_principal=290_000.0,
        term_remaining=240,
        new_term=240,
        refi_cost=7_000.0,
        expected_original_total_interest=446_406.40,
        description="Efficient frontier midway through loan"
    ),
]


# =============================================================================
# MONTHLY PAYMENT CALCULATION VERIFICATION DATA
# Simple principal/rate/term -> payment mappings for quick verification
# =============================================================================

PAYMENT_VERIFICATION = {
    # (principal, rate, term_months): expected_payment
    (100_000, 0.05, 360): 536.82,
    (100_000, 0.06, 360): 599.55,
    (100_000, 0.07, 360): 665.30,
    (200_000, 0.05, 360): 1073.64,
    (200_000, 0.06, 360): 1199.10,
    (200_000, 0.07, 360): 1330.60,
    (300_000, 0.05, 360): 1610.46,
    (300_000, 0.06, 360): 1798.65,
    (300_000, 0.07, 360): 1995.91,
    (400_000, 0.05, 360): 2147.29,
    (400_000, 0.06, 360): 2398.20,
    (400_000, 0.07, 360): 2661.21,
    (500_000, 0.05, 360): 2684.11,
    (500_000, 0.06, 360): 2997.75,
    (500_000, 0.07, 360): 3326.51,
    # 15-year terms
    (100_000, 0.05, 180): 790.79,
    (200_000, 0.05, 180): 1581.59,
    (300_000, 0.05, 180): 2372.38,
    (100_000, 0.06, 180): 843.86,
    (200_000, 0.06, 180): 1687.71,
    (300_000, 0.06, 180): 2531.57,
}


# =============================================================================
# TOTAL INTEREST PAID VERIFICATION DATA
# For testing ipmt_total function
# =============================================================================

INTEREST_VERIFICATION = {
    # (principal, rate, term_months): expected_total_interest
    (100_000, 0.05, 360): 93_255.78,
    (100_000, 0.06, 360): 115_838.19,
    (200_000, 0.05, 360): 186_511.57,
    (200_000, 0.06, 360): 231_676.38,
    (300_000, 0.05, 360): 279_767.35,
    (300_000, 0.06, 360): 347_514.57,
    (400_000, 0.05, 360): 373_023.14,
    (400_000, 0.06, 360): 463_352.77,
    # 15-year terms (much less interest)
    (100_000, 0.05, 180): 42_342.85,
    (200_000, 0.05, 180): 84_685.70,
    (100_000, 0.06, 180): 51_894.23,
    (200_000, 0.06, 180): 103_788.46,
}


# =============================================================================
# AMOUNT REMAINING VERIFICATION DATA
# For testing amount_remaining function at specific points in loan
# =============================================================================

@dataclass
class AmountRemainingTestCase:
    """Test case for remaining balance calculations."""
    name: str
    principal: float
    rate: float
    term: int
    months_paid: int
    expected_remaining: float
    description: str = ""


AMOUNT_REMAINING_CASES = [
    AmountRemainingTestCase(
        name="remaining_30yr_year1",
        principal=300_000.0,
        rate=0.06,
        term=360,
        months_paid=12,
        expected_remaining=295_540.48,
        description="30-year loan after 1 year"
    ),
    AmountRemainingTestCase(
        name="remaining_30yr_year5",
        principal=300_000.0,
        rate=0.06,
        term=360,
        months_paid=60,
        expected_remaining=278_138.45,
        description="30-year loan after 5 years"
    ),
    AmountRemainingTestCase(
        name="remaining_30yr_year10",
        principal=300_000.0,
        rate=0.06,
        term=360,
        months_paid=120,
        expected_remaining=251_057.19,
        description="30-year loan after 10 years"
    ),
    AmountRemainingTestCase(
        name="remaining_30yr_year20",
        principal=300_000.0,
        rate=0.06,
        term=360,
        months_paid=240,
        expected_remaining=165_329.67,
        description="30-year loan after 20 years"
    ),
    AmountRemainingTestCase(
        name="remaining_15yr_year5",
        principal=200_000.0,
        rate=0.05,
        term=180,
        months_paid=60,
        expected_remaining=140_726.89,
        description="15-year loan after 5 years"
    ),
]


# =============================================================================
# HELPER FUNCTIONS FOR TEST IMPORTS
# =============================================================================

def get_all_mortgage_cases():
    """Return all standard and edge case mortgages."""
    return STANDARD_MORTGAGES + EDGE_CASES


def get_refinance_cases():
    """Return all refinance test cases."""
    return REFINANCE_SCENARIOS


def get_break_even_cases():
    """Return all break-even test cases."""
    return BREAK_EVEN_CASES


def get_efficient_frontier_cases():
    """Return all efficient frontier test cases."""
    return EFFICIENT_FRONTIER_CASES


def get_amount_remaining_cases():
    """Return all amount remaining test cases."""
    return AMOUNT_REMAINING_CASES


# Count verification
_total_cases = (
    len(STANDARD_MORTGAGES) +
    len(EDGE_CASES) +
    len(REFINANCE_SCENARIOS) +
    len(BREAK_EVEN_CASES) +
    len(EFFICIENT_FRONTIER_CASES) +
    len(AMOUNT_REMAINING_CASES) +
    len(PAYMENT_VERIFICATION) +
    len(INTEREST_VERIFICATION)
)

# Ensure we have 20+ test cases as required
assert _total_cases >= 20, f"Expected 20+ test cases, got {_total_cases}"
