"""Pytest configuration for refi_alert tests."""
import os
import pytest
from unittest.mock import patch, MagicMock

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
        email='test@example.com'
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
        credit_score=750
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
        payment_status='incomplete'
    )
    db_session.add(alert)
    db_session.commit()
    return alert
