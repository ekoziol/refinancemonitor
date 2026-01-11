"""Pytest configuration for Refinance Monitor tests."""
import pytest
import sys
import os

# Add the refi_monitor package to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create application for testing."""
    from refi_monitor import init_app

    app = init_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def standard_30yr_fixture():
    """Standard 30-year mortgage test fixture."""
    return {
        'current_principal': 400000,
        'current_rate': 0.045,
        'current_term': 360,
        'target_rate': 0.035,
        'target_term': 360,
        'refi_cost': 5000,
        'remaining_term': 300,
        'remaining_principal': 364631.66,
    }
