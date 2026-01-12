"""
Shared pytest fixtures for all tests.

This file is automatically loaded by pytest and makes fixtures
available to all test files without needing to import them.
"""
import pytest
from refi_monitor import init_app


@pytest.fixture(scope='session')
def app():
    """
    Create Flask application for testing.

    Scope: session - created once per test session
    """
    app = init_app()
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    return app


@pytest.fixture(scope='function')
def client(app):
    """
    Create Flask test client.

    Scope: function - new client for each test function
    """
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """
    Create Flask CLI test runner.

    Scope: function - new runner for each test function
    """
    return app.test_cli_runner()


@pytest.fixture(scope='session')
def _db(app):
    """
    Create database for testing.

    Note: Prefixed with _ to avoid conflict with pytest-flask-sqlalchemy
    Scope: session - created once per test session
    """
    from refi_monitor.models import db

    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()


@pytest.fixture(scope='function')
def db_session(_db, app):
    """
    Create a new database session for a test.

    Scope: function - new session for each test, rolled back after
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Bind session to connection
        session = _db.create_scoped_session(
            options={"bind": connection, "binds": {}}
        )
        _db.session = session

        yield session

        # Rollback transaction and close connection
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def sample_user_data():
    """
    Sample user data for testing.

    Returns a dictionary with valid user attributes.
    """
    return {
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'securepassword123',
        'credit_score': 750,
    }


@pytest.fixture
def sample_mortgage_data():
    """
    Sample mortgage data for testing.

    Returns a dictionary with valid mortgage attributes.
    """
    return {
        'original_principal': 400000.0,
        'original_rate': 0.045,
        'original_term': 360,
        'remaining_principal': 364631.66,
        'remaining_term': 300,
        'credit_score': 750,
        'zip_code': '12345',
    }


@pytest.fixture
def sample_calculation_inputs():
    """
    Sample calculation inputs for testing calculator.

    Returns a dictionary matching the standard test fixture.
    """
    return {
        'original_principal': 400000.0,
        'original_rate': 0.045,
        'original_term': 360,
        'remaining_principal': 364631.66,
        'remaining_term': 300,
        'target_rate': 0.02,
        'target_term': 360,
        'refi_cost': 5000.0,
    }
