"""Test configuration and fixtures."""
import pytest
from datetime import datetime
from refi_monitor import init_app, db
from refi_monitor.models import User, Mortgage, Alert, Trigger, EmailLog


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


@pytest.fixture
def app():
    """Create application for testing."""
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager
    from flask_mail import Mail
    from refi_monitor import db as refi_db, mail as refi_mail, login_manager

    app = Flask(__name__)
    app.config.from_object(TestConfig)

    refi_db.init_app(app)
    refi_mail.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # Import and register blueprints
        from refi_monitor.routes import main_bp
        from refi_monitor.auth import auth_bp
        from refi_monitor.mortgage import mortgage_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(mortgage_bp)

        refi_db.create_all()
        yield app
        refi_db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        user = User(
            name='Test User',
            email='test@example.com',
            created_on=datetime.utcnow()
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

        # Refresh to get the id
        db.session.refresh(user)
        yield user


@pytest.fixture
def sample_mortgage(app, sample_user):
    """Create a sample mortgage for testing."""
    with app.app_context():
        # Re-query user within this context
        user = User.query.get(sample_user.id)
        mortgage = Mortgage(
            user_id=user.id,
            name='Test Home Mortgage',
            zip_code='12345',
            original_principal=300000.0,
            original_term=360,
            original_interest_rate=6.5,
            remaining_principal=280000.0,
            remaining_term=340,
            credit_score=750,
            created_on=datetime.utcnow()
        )
        db.session.add(mortgage)
        db.session.commit()
        db.session.refresh(mortgage)
        yield mortgage


@pytest.fixture
def sample_alert(app, sample_user, sample_mortgage):
    """Create a sample alert for testing."""
    with app.app_context():
        # Re-query to get fresh objects
        user = User.query.get(sample_user.id)
        mortgage = Mortgage.query.get(sample_mortgage.id)

        alert = Alert(
            user_id=user.id,
            mortgage_id=mortgage.id,
            alert_type='interest_rate',
            target_interest_rate=5.5,
            target_term=360,
            estimate_refinance_cost=5000.0,
            payment_status='active',
            initial_payment=True,
            created_on=datetime.utcnow()
        )
        db.session.add(alert)
        db.session.commit()
        db.session.refresh(alert)
        yield alert


@pytest.fixture
def sample_trigger(app, sample_alert):
    """Create a sample trigger for testing."""
    with app.app_context():
        alert = Alert.query.get(sample_alert.id)

        trigger = Trigger(
            alert_id=alert.id,
            alert_type='interest_rate',
            alert_trigger_status=1,
            alert_trigger_reason='Market rate dropped to 5.25%, below your target of 5.5%',
            alert_trigger_date=datetime.utcnow(),
            created_on=datetime.utcnow()
        )
        db.session.add(trigger)
        db.session.commit()
        db.session.refresh(trigger)
        yield trigger


@pytest.fixture
def unsubscribed_user(app):
    """Create an unsubscribed user for testing."""
    with app.app_context():
        user = User(
            name='Unsubscribed User',
            email='unsubscribed@example.com',
            email_unsubscribed=True,
            created_on=datetime.utcnow()
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        yield user
