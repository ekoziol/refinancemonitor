"""Pytest fixtures for refi_alert tests."""
import pytest
from flask import Flask

from refi_monitor import init_app, db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    from config import TestConfig

    # Create a minimal Flask app for testing
    test_app = Flask(__name__, instance_relative_config=False)
    test_app.config.from_object(TestConfig)

    # Override the secret key for testing
    test_app.config['SECRET_KEY'] = 'test-secret-key'

    from refi_monitor import db, login_manager, csrf, mail

    db.init_app(test_app)
    login_manager.init_app(test_app)
    csrf.init_app(test_app)
    mail.init_app(test_app)

    with test_app.app_context():
        from refi_monitor import routes, auth, mortgage
        from refi_monitor.models import User, Mortgage, Mortgage_Tracking, Alert, Trigger

        test_app.register_blueprint(routes.main_bp)
        test_app.register_blueprint(auth.auth_bp)
        test_app.register_blueprint(mortgage.mortgage_bp)

        db.create_all()

        yield test_app

        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def session(app):
    """Create a new database session for a test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        yield db.session

        transaction.rollback()
        connection.close()
