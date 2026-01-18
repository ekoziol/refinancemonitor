"""Test configuration and fixtures."""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# Mock external dependencies before importing refi_monitor
class MockColumn:
    """Mock SQLAlchemy Column."""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class MockForeignKey:
    """Mock SQLAlchemy ForeignKey."""
    def __init__(self, *args, **kwargs):
        pass


class MockRelationship:
    """Mock SQLAlchemy relationship."""
    def __init__(self, *args, **kwargs):
        pass


class MockIndex:
    """Mock SQLAlchemy Index."""
    def __init__(self, *args, **kwargs):
        pass


class MockModel:
    """Mock SQLAlchemy Model base class."""
    query = MagicMock()


class MockDb:
    """Mock Flask-SQLAlchemy db object."""
    Column = MockColumn
    Integer = int
    String = str
    Float = float
    Boolean = bool
    DateTime = datetime
    Text = str
    ForeignKey = MockForeignKey
    relationship = MockRelationship
    Index = MockIndex
    Model = MockModel
    session = MagicMock()
    backref = MagicMock(return_value=None)

    def __init__(self):
        pass


# Create a mock db
mock_db = MockDb()

# Create mock for flask_login.UserMixin
class MockUserMixin:
    pass


# Create mock for werkzeug.security
def mock_generate_password_hash(password, method='sha256'):
    return f'hashed_{password}'


def mock_check_password_hash(stored_hash, password):
    return stored_hash == f'hashed_{password}'


@pytest.fixture(scope='function')
def app():
    """Create a mock application context for testing models."""

    class MockAppContext:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockApp:
        def app_context(self):
            return MockAppContext()

    return MockApp()


# Patch modules before importing
sys.modules['flask_login'] = MagicMock()
sys.modules['flask_login'].UserMixin = MockUserMixin

sys.modules['werkzeug'] = MagicMock()
sys.modules['werkzeug.security'] = MagicMock()
sys.modules['werkzeug.security'].generate_password_hash = mock_generate_password_hash
sys.modules['werkzeug.security'].check_password_hash = mock_check_password_hash

sys.modules['flask'] = MagicMock()
sys.modules['flask_sqlalchemy'] = MagicMock()
sys.modules['flask_mail'] = MagicMock()
sys.modules['flask_assets'] = MagicMock()
sys.modules['apscheduler'] = MagicMock()
sys.modules['apscheduler.schedulers'] = MagicMock()
sys.modules['apscheduler.schedulers.background'] = MagicMock()
sys.modules['apscheduler.triggers'] = MagicMock()
sys.modules['apscheduler.triggers.cron'] = MagicMock()

# Create a mock refi_monitor module
mock_refi_module = MagicMock()
mock_refi_module.db = mock_db
mock_refi_module.mail = MagicMock()
sys.modules['refi_monitor'] = mock_refi_module
