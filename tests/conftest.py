"""
Pytest configuration and shared fixtures for RefiAlert tests.

This file is automatically loaded by pytest.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "contract: API contract tests (TDD - may fail before implementation)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring database/external services"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than 1 second"
    )


@pytest.fixture(scope="session")
def app():
    """
    Create application for testing.
    Will be implemented in Phase 2.
    """
    # TODO: Import and create Flask app
    # from refi_monitor import create_app
    # app = create_app(config_name='testing')
    # return app
    pytest.skip("App not configured for testing yet - Phase 2")


@pytest.fixture(scope="session")
def api_client(app):
    """
    Create test client for API testing.
    Will be implemented in Phase 2.
    """
    # return app.test_client()
    pytest.skip("API client not available yet - Phase 2")


@pytest.fixture
def sample_mortgage_data():
    """Standard mortgage data for testing calculations"""
    return {
        "original_principal": 400000.00,
        "original_rate": 0.045,
        "original_term": 360,
        "remaining_principal": 364631.66,
        "remaining_term": 300,
    }


@pytest.fixture
def sample_refinance_data():
    """Standard refinance scenario for testing"""
    return {
        "target_rate": 0.035,
        "target_term": 360,
        "refi_cost": 5000.00,
    }
