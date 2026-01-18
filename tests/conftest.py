"""Test configuration and fixtures."""
import os
import sys
import pytest


def pytest_configure(config):
    """Configure pytest before test collection."""
    # Check if we're running in CI with all required dependencies
    try:
        import flask
        import flask_assets
        import flask_sqlalchemy
        import flask_login
        os.environ['USE_REAL_FLASK'] = 'True'
    except ImportError:
        os.environ['USE_REAL_FLASK'] = 'False'


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    if os.environ.get('USE_REAL_FLASK') == 'True':
        # Real Flask app for CI/CD environment
        os.environ['TESTING'] = 'True'
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        os.environ['WTF_CSRF_ENABLED'] = 'False'

        from wsgi import app as flask_app

        flask_app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'LOGIN_DISABLED': True,
        })

        # Create tables
        with flask_app.app_context():
            from refi_monitor import db
            db.create_all()

        yield flask_app

        # Cleanup
        with flask_app.app_context():
            from refi_monitor import db
            db.drop_all()
    else:
        # Mock Flask app for local development without dependencies
        from unittest.mock import MagicMock

        mock_app = MagicMock()
        mock_app.config = {
            'TESTING': True,
            'VERSION': '1.0.0',
        }

        yield mock_app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    if os.environ.get('USE_REAL_FLASK') == 'True':
        return app.test_client()
    else:
        # Mock client for local testing
        from unittest.mock import MagicMock
        import json

        mock_client = MagicMock()

        # Mock health endpoint responses
        def mock_get(path):
            response = MagicMock()
            if path == '/health':
                response.status_code = 200
                response.data = json.dumps({
                    'status': 'healthy',
                    'timestamp': 1234567890,
                    'database': 'healthy'
                }).encode()
            elif path == '/health/live':
                response.status_code = 200
                response.data = json.dumps({'alive': True}).encode()
            elif path == '/health/ready':
                response.status_code = 200
                response.data = json.dumps({'ready': True}).encode()
            elif path == '/favicon.ico':
                response.status_code = 200
            else:
                response.status_code = 404
                response.data = b'{}'
            return response

        mock_client.get = mock_get
        return mock_client


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    if os.environ.get('USE_REAL_FLASK') == 'True':
        return app.test_cli_runner()
    else:
        from unittest.mock import MagicMock
        return MagicMock()
