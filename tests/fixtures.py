"""
Test fixtures with known-good values from current Dash implementation.

These fixtures represent real-world refinance scenarios with varying
characteristics. They serve as the baseline for regression testing.

Expected outputs will be filled in Phase 0.3 by running the current
Dash implementation and capturing the results.
"""

# Fixture 1: Standard 30-Year Refinance (Baseline Scenario)
FIXTURE_STANDARD = {
    "name": "standard_refinance",
    "description": "Typical refinance scenario - 30yr to 30yr with lower rate",
    "inputs": {
        "original_principal": 400000.0,
        "original_rate": 0.045,  # 4.5%
        "original_term": 360,  # 30 years
        "remaining_principal": 364631.66,
        "remaining_term": 300,  # 25 years remaining (5 years paid)
        "target_rate": 0.02,  # 2.0% - significant improvement
        "target_term": 360,  # 30 years
        "refi_cost": 5000.0,
    },
    "expected_outputs": {
        # To be filled by running generate_baseline.py
        "original_monthly_payment": None,
        "minimum_monthly_payment": None,
        "refi_monthly_payment": None,
        "monthly_savings": None,
        "months_paid": None,
        "original_total_interest": None,
        "refi_total_interest": None,
        "total_loan_savings": None,
        "month_to_even_simple": None,
        "month_to_even_interest": None,
        "target_interest_rate": None,
    },
}

# Fixture 2: Zero Interest Rate (Edge Case)
FIXTURE_ZERO_RATE = {
    "name": "zero_rate_refinance",
    "description": "Edge case with 0% interest rate (theoretical minimum)",
    "inputs": {
        "original_principal": 300000.0,
        "original_rate": 0.03,  # 3.0%
        "original_term": 360,
        "remaining_principal": 280000.0,
        "remaining_term": 300,
        "target_rate": 0.0,  # EDGE CASE: 0% interest
        "target_term": 300,
        "refi_cost": 3000.0,
    },
    "expected_outputs": {
        # When rate = 0, payment should be principal / term
        "refi_monthly_payment": 933.33,  # 280000 / 300
        # Rest to be filled by generate_baseline.py
        "original_monthly_payment": None,
        "minimum_monthly_payment": None,
        "monthly_savings": None,
        "months_paid": None,
        "original_total_interest": None,
        "refi_total_interest": None,
        "total_loan_savings": None,
        "month_to_even_simple": None,
        "month_to_even_interest": None,
        "target_interest_rate": None,
    },
}

# Fixture 3: Bad Refinance (Negative Savings)
FIXTURE_BAD_REFI = {
    "name": "bad_refinance",
    "description": "Refinance that costs more money (higher rate + closing costs)",
    "inputs": {
        "original_principal": 200000.0,
        "original_rate": 0.025,  # 2.5% - good rate
        "original_term": 360,
        "remaining_principal": 180000.0,
        "remaining_term": 300,
        "target_rate": 0.04,  # 4.0% - HIGHER than original
        "target_term": 360,
        "refi_cost": 8000.0,  # High closing costs
    },
    "expected_outputs": {
        # Negative savings expected
        "monthly_savings": None,  # Should be negative
        "month_to_even_simple": None,  # Should be None (not possible)
        "total_loan_savings": None,  # Should be negative
        # Rest to be filled
        "original_monthly_payment": None,
        "minimum_monthly_payment": None,
        "refi_monthly_payment": None,
        "months_paid": None,
        "original_total_interest": None,
        "refi_total_interest": None,
        "month_to_even_interest": None,
        "target_interest_rate": None,
    },
}

# Fixture 4: High Interest Rate Scenario
FIXTURE_HIGH_RATE = {
    "name": "high_rate_refinance",
    "description": "Refinancing from very high rate (8%) to moderate (6%)",
    "inputs": {
        "original_principal": 500000.0,
        "original_rate": 0.08,  # 8.0% - very high
        "original_term": 360,
        "remaining_principal": 480000.0,
        "remaining_term": 330,
        "target_rate": 0.06,  # 6.0% - still high but better
        "target_term": 360,
        "refi_cost": 10000.0,
    },
    "expected_outputs": {
        # Large savings expected due to high rate reduction
        # To be filled by generate_baseline.py
        "original_monthly_payment": None,
        "minimum_monthly_payment": None,
        "refi_monthly_payment": None,
        "monthly_savings": None,
        "months_paid": None,
        "original_total_interest": None,
        "refi_total_interest": None,
        "total_loan_savings": None,
        "month_to_even_simple": None,
        "month_to_even_interest": None,
        "target_interest_rate": None,
    },
}

# Fixture 5: Short Term Loan (15-year)
FIXTURE_SHORT_TERM = {
    "name": "short_term_refinance",
    "description": "15-year mortgage refinance (higher payments, less interest)",
    "inputs": {
        "original_principal": 150000.0,
        "original_rate": 0.035,  # 3.5%
        "original_term": 180,  # 15 years
        "remaining_principal": 100000.0,
        "remaining_term": 120,  # 10 years remaining
        "target_rate": 0.025,  # 2.5%
        "target_term": 120,  # Keep same term
        "refi_cost": 2500.0,
    },
    "expected_outputs": {
        # To be filled by generate_baseline.py
        "original_monthly_payment": None,
        "minimum_monthly_payment": None,
        "refi_monthly_payment": None,
        "monthly_savings": None,
        "months_paid": None,
        "original_total_interest": None,
        "refi_total_interest": None,
        "total_loan_savings": None,
        "month_to_even_simple": None,
        "month_to_even_interest": None,
        "target_interest_rate": None,
    },
}

# List of all fixtures for batch testing
ALL_FIXTURES = [
    FIXTURE_STANDARD,
    FIXTURE_ZERO_RATE,
    FIXTURE_BAD_REFI,
    FIXTURE_HIGH_RATE,
    FIXTURE_SHORT_TERM,
]


def get_fixture_by_name(name):
    """
    Get a fixture by its name.

    Args:
        name: Fixture name (e.g., 'standard_refinance')

    Returns:
        Fixture dictionary or None if not found
    """
    for fixture in ALL_FIXTURES:
        if fixture['name'] == name:
            return fixture
    return None


def get_fixture_inputs(fixture):
    """
    Get just the inputs from a fixture.

    Args:
        fixture: Fixture dictionary

    Returns:
        Dictionary of input parameters
    """
    return fixture['inputs']


def get_fixture_expected_outputs(fixture):
    """
    Get just the expected outputs from a fixture.

    Args:
        fixture: Fixture dictionary

    Returns:
        Dictionary of expected output values
    """
    return fixture['expected_outputs']


def validate_fixture_complete(fixture):
    """
    Check if a fixture has all expected outputs filled in.

    Args:
        fixture: Fixture dictionary

    Returns:
        tuple: (is_complete, missing_fields)
    """
    expected = fixture['expected_outputs']
    missing = [k for k, v in expected.items() if v is None]

    return len(missing) == 0, missing


def print_fixture_summary():
    """Print a summary of all fixtures."""
    print("=" * 80)
    print("TEST FIXTURES SUMMARY")
    print("=" * 80)
    print(f"\nTotal Fixtures: {len(ALL_FIXTURES)}\n")

    for i, fixture in enumerate(ALL_FIXTURES, 1):
        inputs = fixture['inputs']
        is_complete, missing = validate_fixture_complete(fixture)

        print(f"{i}. {fixture['name']}")
        print(f"   Description: {fixture['description']}")
        print(f"   Original Principal: ${inputs['original_principal']:,.2f}")
        print(f"   Original Rate: {inputs['original_rate']:.3%}")
        print(f"   Target Rate: {inputs['target_rate']:.3%}")
        print(f"   Expected Outputs: {'✅ Complete' if is_complete else f'⚠️  {len(missing)} missing'}")
        print()

    print("=" * 80)


if __name__ == '__main__':
    # Print summary when run directly
    print_fixture_summary()
