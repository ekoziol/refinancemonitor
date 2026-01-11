"""Pytest configuration for refi_alert tests."""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables before importing the app
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['STRIPE_API_KEY'] = 'sk_test_fake_key'
os.environ['STRIPE_WEBHOOK_SECRET'] = 'whsec_test_secret'
os.environ['STRIPE_PRICE_ID'] = 'price_test_id'
os.environ['STRIPE_SUCCESS_URL'] = 'http://localhost:5000/success'
os.environ['STRIPE_CANCEL_URL'] = 'http://localhost:5000/cancel'
os.environ['ENABLE_SCHEDULER'] = 'false'


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


class TestConfig:
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False
    ENABLE_SCHEDULER = False
    MAIL_SUPPRESS_SEND = True
    MAIL_DEFAULT_SENDER = 'test@refialert.com'
    SERVER_NAME = 'localhost'


@pytest.fixture(scope='function')
def app():
    """Create application for testing."""
    # Mock the scheduler to prevent it from starting
    with patch('refi_monitor.scheduler.init_scheduler'):
        from refi_monitor import init_app, db

        application = init_app()
        application.config['TESTING'] = True
        application.config['WTF_CSRF_ENABLED'] = False
        application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        application.config['MAIL_SUPPRESS_SEND'] = True
        application.config['MAIL_DEFAULT_SENDER'] = 'test@refialert.com'

        with application.app_context():
            db.create_all()
            yield application
            db.session.remove()
            db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a database session for testing."""
    from refi_monitor import db
    with app.app_context():
        yield db.session


@pytest.fixture
def mock_stripe():
    """Mock Stripe API calls."""
    with patch('stripe.Webhook.construct_event') as mock_construct, \
         patch('stripe.Subscription.retrieve') as mock_subscription, \
         patch('stripe.checkout.Session.create') as mock_checkout:
        yield {
            'construct_event': mock_construct,
            'subscription_retrieve': mock_subscription,
            'checkout_create': mock_checkout
        }


@pytest.fixture
def sample_user(app, db_session):
    """Create a sample user for testing."""
    from refi_monitor.models import User
    user = User(
        name='Test User',
        email='test@example.com',
        created_on=datetime.utcnow()
    )
    user.set_password('testpassword')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_mortgage(app, db_session, sample_user):
    """Create a sample mortgage for testing."""
    from refi_monitor.models import Mortgage
    mortgage = Mortgage(
        user_id=sample_user.id,
        name='Test Mortgage',
        zip_code='12345',
        original_principal=300000.0,
        original_term=360,
        original_interest_rate=0.045,
        remaining_principal=280000.0,
        remaining_term=300,
        credit_score=750,
        created_on=datetime.utcnow()
    )
    db_session.add(mortgage)
    db_session.commit()
    return mortgage


@pytest.fixture
def sample_alert(app, db_session, sample_user, sample_mortgage):
    """Create a sample alert for testing."""
    from refi_monitor.models import Alert
    alert = Alert(
        user_id=sample_user.id,
        mortgage_id=sample_mortgage.id,
        alert_type='rate_drop',
        target_monthly_payment=1500.0,
        target_interest_rate=0.04,
        target_term=360,
        estimate_refinance_cost=3000.0,
        initial_payment=False,
        payment_status='incomplete',
        created_on=datetime.utcnow()
    )
    db_session.add(alert)
    db_session.commit()
    return alert


@pytest.fixture
def sample_trigger(app, db_session, sample_alert):
    """Create a sample trigger for testing."""
    from refi_monitor.models import Trigger
    trigger = Trigger(
        alert_id=sample_alert.id,
        alert_type='interest_rate',
        alert_trigger_status=1,
        alert_trigger_reason='Market rate dropped to 5.25%, below your target of 5.5%',
        alert_trigger_date=datetime.utcnow(),
        created_on=datetime.utcnow()
    )
    db_session.add(trigger)
    db_session.commit()
    return trigger


@pytest.fixture
def unsubscribed_user(app, db_session):
    """Create an unsubscribed user for testing."""
    from refi_monitor.models import User
    user = User(
        name='Unsubscribed User',
        email='unsubscribed@example.com',
        email_unsubscribed=True,
        created_on=datetime.utcnow()
    )
    user.set_password('testpassword')
    db_session.add(user)
    db_session.commit()
    return user


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
