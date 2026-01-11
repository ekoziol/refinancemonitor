"""Pytest configuration for refi_alert tests."""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def app():
    """Create application for testing."""
    from refi_monitor import init_app
    from config import Config

    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        ENABLE_SCHEDULER = False
        WTF_CSRF_ENABLED = False

    # Override config
    import config
    original_config = config.Config
    config.Config = TestConfig

    app = init_app()

    yield app

    config.Config = original_config


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Create database tables."""
    from refi_monitor import db as _db

    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture
def sample_rates():
    """Sample rate data for testing."""
    return {
        30: 0.0694,  # 6.94%
        15: 0.0625,  # 6.25%
        5: 0.0580,   # 5.80% (5/1 ARM)
    }


@pytest.fixture
def mock_api_response():
    """Mock API response data."""
    return [
        {
            '30_year_frm': 6.94,
            '15_year_frm': 6.25,
            '5_1_arm': 5.80,
        }
    ]
