"""Pytest fixtures for Dash calculator integration tests."""
import pytest
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def default_mortgage_inputs():
    """Default mortgage input values matching the Dash app defaults."""
    return {
        'current_principal': 400000,
        'current_rate': 0.045,
        'current_term': 360,
        'target_rate': 0.02,
        'target_term': 360,
        'target_monthly_payment': 1500,
        'refi_cost': 5000,
        'remaining_term': 300,
        'remaining_principal': 364631.66,
    }


@pytest.fixture
def high_rate_mortgage_inputs():
    """High interest rate mortgage scenario."""
    return {
        'current_principal': 500000,
        'current_rate': 0.08,
        'current_term': 360,
        'target_rate': 0.05,
        'target_term': 360,
        'target_monthly_payment': 2500,
        'refi_cost': 8000,
        'remaining_term': 280,
        'remaining_principal': 480000,
    }


@pytest.fixture
def zero_rate_mortgage_inputs():
    """Zero interest rate edge case."""
    return {
        'current_principal': 300000,
        'current_rate': 0.0,
        'current_term': 360,
        'target_rate': 0.0,
        'target_term': 360,
        'target_monthly_payment': 833.33,
        'refi_cost': 3000,
        'remaining_term': 300,
        'remaining_principal': 250000,
    }


@pytest.fixture
def short_term_mortgage_inputs():
    """15-year mortgage scenario."""
    return {
        'current_principal': 250000,
        'current_rate': 0.035,
        'current_term': 180,
        'target_rate': 0.025,
        'target_term': 180,
        'target_monthly_payment': 1600,
        'refi_cost': 4000,
        'remaining_term': 150,
        'remaining_principal': 210000,
    }


@pytest.fixture
def nearly_paid_mortgage_inputs():
    """Mortgage near end of term."""
    return {
        'current_principal': 400000,
        'current_rate': 0.045,
        'current_term': 360,
        'target_rate': 0.03,
        'target_term': 120,
        'target_monthly_payment': 1000,
        'refi_cost': 2000,
        'remaining_term': 60,
        'remaining_principal': 50000,
    }


@pytest.fixture
def negative_savings_mortgage_inputs():
    """Scenario where refinancing results in negative savings."""
    return {
        'current_principal': 200000,
        'current_rate': 0.03,
        'current_term': 360,
        'target_rate': 0.05,
        'target_term': 360,
        'target_monthly_payment': 1100,
        'refi_cost': 10000,
        'remaining_term': 340,
        'remaining_principal': 195000,
    }
