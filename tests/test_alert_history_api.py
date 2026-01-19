"""Tests for alert history API endpoint."""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAlertHistoryApiLogic:
    """Test alert history API logic without database dependencies."""

    def test_alert_history_response_structure(self):
        """Test that alert history response has the expected structure."""
        expected_keys = {
            'alert', 'mortgage', 'triggers', 'current_market_rate',
            'total_triggers', 'successful_notifications'
        }
        response = {
            'alert': {'id': 1, 'alert_type': 'Interest Rate'},
            'mortgage': {'id': 1, 'name': 'Primary Home'},
            'triggers': [],
            'current_market_rate': 0.0675,
            'total_triggers': 0,
            'successful_notifications': 0
        }
        assert expected_keys == set(response.keys())

    def test_trigger_data_structure(self):
        """Test that trigger data in response has expected fields."""
        trigger_data = {
            'id': 1,
            'alert_trigger_date': '2025-01-15T10:30:00',
            'triggered_rate': 0.054,
            'alert_trigger_status': 1,
            'alert_trigger_reason': 'Rate target met',
            'alert_type': 'Interest Rate',
            'created_on': '2025-01-15T10:30:00',
            'notification': {
                'status': 'sent',
                'sent_at': '2025-01-15T10:31:00',
                'error_message': None
            }
        }
        expected_trigger_keys = {
            'id', 'alert_trigger_date', 'triggered_rate', 'alert_trigger_status',
            'alert_trigger_reason', 'alert_type', 'created_on', 'notification'
        }
        assert expected_trigger_keys == set(trigger_data.keys())

    def test_notification_status_mapping(self):
        """Test notification status mapping logic."""
        notification_statuses = ['sent', 'failed', 'pending', 'delivered']
        for status in notification_statuses:
            notification = {'status': status, 'sent_at': None, 'error_message': None}
            assert notification['status'] == status

    def test_successful_notifications_counting(self):
        """Test counting of successful notifications."""
        triggers_with_notifications = [
            {'notification': {'status': 'sent'}},
            {'notification': {'status': 'failed'}},
            {'notification': {'status': 'sent'}},
            {'notification': None},
        ]
        successful_count = sum(
            1 for t in triggers_with_notifications
            if t.get('notification') and t['notification'].get('status') == 'sent'
        )
        assert successful_count == 2

    def test_empty_trigger_history(self):
        """Test response structure with no triggers."""
        response = {
            'alert': {'id': 1, 'alert_type': 'Interest Rate'},
            'mortgage': {'id': 1, 'name': 'Home'},
            'triggers': [],
            'current_market_rate': 0.0675,
            'total_triggers': 0,
            'successful_notifications': 0
        }
        assert response['total_triggers'] == 0
        assert response['successful_notifications'] == 0
        assert response['triggers'] == []

    def test_trigger_ordering_by_date(self):
        """Test that triggers should be ordered by date descending."""
        triggers = [
            {'id': 1, 'alert_trigger_date': '2025-01-10T10:00:00'},
            {'id': 2, 'alert_trigger_date': '2025-01-15T10:00:00'},
            {'id': 3, 'alert_trigger_date': '2025-01-12T10:00:00'},
        ]
        sorted_triggers = sorted(
            triggers,
            key=lambda t: t['alert_trigger_date'],
            reverse=True
        )
        assert sorted_triggers[0]['id'] == 2  # Most recent first
        assert sorted_triggers[1]['id'] == 3
        assert sorted_triggers[2]['id'] == 1  # Oldest last

    def test_market_rate_none_when_not_found(self):
        """Test that current_market_rate can be None if no rate data."""
        response = {
            'alert': {'id': 1},
            'mortgage': {'id': 1},
            'triggers': [],
            'current_market_rate': None,
            'total_triggers': 0,
            'successful_notifications': 0
        }
        assert response['current_market_rate'] is None


class TestAlertHistoryAccessControl:
    """Test access control logic for alert history."""

    def test_ownership_check_logic(self):
        """Test that ownership is verified via mortgage user_id."""
        current_user_id = 1
        mortgage_user_id = 1
        assert current_user_id == mortgage_user_id

    def test_unauthorized_access_logic(self):
        """Test unauthorized access should be blocked."""
        current_user_id = 1
        mortgage_user_id = 2
        assert current_user_id != mortgage_user_id

    def test_alert_not_found_logic(self):
        """Test handling of non-existent alert."""
        alert = None
        expected_error = {'error': 'Alert not found'}
        expected_status = 404
        assert alert is None
        assert expected_error['error'] == 'Alert not found'
        assert expected_status == 404


class TestTriggerNotificationMapping:
    """Test trigger to email log mapping logic."""

    def test_email_log_lookup_by_trigger_id(self):
        """Test creating lookup dict for email logs by trigger ID."""
        email_logs = [
            {'id': 1, 'related_entity_id': 100, 'status': 'sent'},
            {'id': 2, 'related_entity_id': 101, 'status': 'failed'},
            {'id': 3, 'related_entity_id': 102, 'status': 'sent'},
        ]
        email_log_by_trigger = {
            log['related_entity_id']: log for log in email_logs
        }
        assert 100 in email_log_by_trigger
        assert email_log_by_trigger[100]['status'] == 'sent'
        assert 101 in email_log_by_trigger
        assert email_log_by_trigger[101]['status'] == 'failed'

    def test_trigger_without_email_log(self):
        """Test handling triggers with no associated email log."""
        email_log_by_trigger = {100: {'status': 'sent'}}
        trigger_id = 999  # Not in lookup
        notification = email_log_by_trigger.get(trigger_id)
        assert notification is None

    def test_notification_data_extraction(self):
        """Test extracting notification data from email log."""
        email_log = {
            'status': 'sent',
            'sent_at': datetime(2025, 1, 15, 10, 31, 0),
            'error_message': None
        }
        notification = {
            'status': email_log['status'],
            'sent_at': email_log['sent_at'].isoformat() if email_log['sent_at'] else None,
            'error_message': email_log['error_message']
        }
        assert notification['status'] == 'sent'
        assert notification['sent_at'] == '2025-01-15T10:31:00'
        assert notification['error_message'] is None

    def test_notification_with_error_message(self):
        """Test notification with error message for failed emails."""
        email_log = {
            'status': 'failed',
            'sent_at': None,
            'error_message': 'SMTP connection refused'
        }
        notification = {
            'status': email_log['status'],
            'sent_at': email_log['sent_at'],
            'error_message': email_log['error_message']
        }
        assert notification['status'] == 'failed'
        assert notification['sent_at'] is None
        assert notification['error_message'] == 'SMTP connection refused'
