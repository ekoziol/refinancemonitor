"""Test configuration and fixtures."""
import sys
from unittest.mock import MagicMock

# Mock Flask and related modules before importing application code
sys.modules['flask'] = MagicMock()
sys.modules['flask_sqlalchemy'] = MagicMock()
sys.modules['flask_login'] = MagicMock()
sys.modules['flask_mail'] = MagicMock()
sys.modules['flask_assets'] = MagicMock()
sys.modules['werkzeug'] = MagicMock()
sys.modules['werkzeug.security'] = MagicMock()
sys.modules['apscheduler'] = MagicMock()
sys.modules['apscheduler.schedulers'] = MagicMock()
sys.modules['apscheduler.schedulers.background'] = MagicMock()
sys.modules['apscheduler.triggers'] = MagicMock()
sys.modules['apscheduler.triggers.cron'] = MagicMock()

# Mock the refi_monitor package init
mock_db = MagicMock()
mock_mail = MagicMock()

sys.modules['refi_monitor'] = MagicMock()
sys.modules['refi_monitor'].db = mock_db
sys.modules['refi_monitor'].mail = mock_mail
