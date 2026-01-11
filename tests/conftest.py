"""Pytest configuration and fixtures."""
import pytest
from datetime import datetime


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    from flask import Flask
    from refi_monitor import db, login_manager, csrf, mail

    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.TestConfig')

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    with app.app_context():
        from refi_monitor import routes, auth, mortgage
        from refi_monitor.models import User, Mortgage, Alert, Trigger, MortgageRate

        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(mortgage.mortgage_bp)

        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a fresh database session for each test."""
    from refi_monitor import db

    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    from refi_monitor.models import User

    user = User(
        name='Test User',
        email='test@example.com',
        credit_score=750,
        created_on=datetime.utcnow()
    )
    user.set_password('testpassword123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_mortgage(db_session, sample_user):
    """Create a sample mortgage for testing."""
    from refi_monitor.models import Mortgage

    mortgage = Mortgage(
        user_id=sample_user.id,
        name='Test Mortgage',
        zip_code='12345',
        original_principal=300000.0,
        original_term=360,
        original_interest_rate=4.5,
        remaining_principal=280000.0,
        remaining_term=340,
        credit_score=750,
        created_on=datetime.utcnow()
    )
    db_session.add(mortgage)
    db_session.commit()
    return mortgage


@pytest.fixture
def sample_alert(db_session, sample_user, sample_mortgage):
    """Create a sample alert for testing."""
    from refi_monitor.models import Alert

    alert = Alert(
        user_id=sample_user.id,
        mortgage_id=sample_mortgage.id,
        alert_type='rate_drop',
        target_monthly_payment=1500.0,
        target_interest_rate=3.5,
        target_term=360,
        estimate_refinance_cost=3000.0,
        created_on=datetime.utcnow()
    )
    db_session.add(alert)
    db_session.commit()
    return alert


@pytest.fixture
def authenticated_client(client, sample_user):
    """Create an authenticated test client."""
    with client.session_transaction() as session:
        session['_user_id'] = sample_user.id
        session['_fresh'] = True
    return client
