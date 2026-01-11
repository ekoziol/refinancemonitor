"""Tests for notification service."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from refi_monitor import db
from refi_monitor.models import User, Alert, Mortgage, Trigger, EmailLog
from refi_monitor.notifications import (
    send_welcome_email,
    send_alert_created_confirmation,
    send_alert_notification,
    send_payment_confirmation,
    send_unsubscribe_confirmation,
    _log_email,
    _update_email_log,
    _get_unsubscribe_url,
)


class TestEmailLogging:
    """Tests for email logging functionality."""

    def test_log_email_creates_record(self, app, sample_user):
        """Test that _log_email creates a pending EmailLog record."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            log = _log_email(
                user_id=user.id,
                email_type='welcome',
                recipient_email=user.email,
                subject='Test Subject'
            )

            assert log.id is not None
            assert log.user_id == user.id
            assert log.email_type == 'welcome'
            assert log.status == 'pending'
            assert log.sent_at is None

    def test_log_email_with_alert_and_trigger(self, app, sample_user, sample_alert, sample_trigger):
        """Test email logging with alert and trigger references."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            alert = Alert.query.get(sample_alert.id)
            trigger = Trigger.query.get(sample_trigger.id)

            log = _log_email(
                user_id=user.id,
                email_type='alert_triggered',
                recipient_email=user.email,
                subject='Alert Triggered',
                alert_id=alert.id,
                trigger_id=trigger.id
            )

            assert log.alert_id == alert.id
            assert log.trigger_id == trigger.id

    def test_update_email_log_sent(self, app, sample_user):
        """Test updating email log status to sent."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            log = _log_email(user.id, 'welcome', user.email, 'Test')

            _update_email_log(log, 'sent')

            assert log.status == 'sent'
            assert log.sent_at is not None
            assert log.error_message is None

    def test_update_email_log_failed(self, app, sample_user):
        """Test updating email log status to failed with error message."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            log = _log_email(user.id, 'welcome', user.email, 'Test')

            _update_email_log(log, 'failed', 'SMTP connection failed')

            assert log.status == 'failed'
            assert log.sent_at is None
            assert log.error_message == 'SMTP connection failed'


class TestUnsubscribeToken:
    """Tests for unsubscribe token functionality."""

    def test_generate_unsubscribe_token(self, app, sample_user):
        """Test that unsubscribe token is generated correctly."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            token = user.generate_unsubscribe_token()

            assert token is not None
            assert len(token) > 20
            assert user.unsubscribe_token == token

    def test_generate_unsubscribe_token_idempotent(self, app, sample_user):
        """Test that calling generate twice returns same token."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            token1 = user.generate_unsubscribe_token()
            token2 = user.generate_unsubscribe_token()

            assert token1 == token2

    def test_get_unsubscribe_url(self, app, sample_user):
        """Test that unsubscribe URL is generated correctly."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            url = _get_unsubscribe_url(user)

            assert 'unsubscribe' in url
            assert user.unsubscribe_token in url


class TestWelcomeEmail:
    """Tests for welcome email functionality."""

    @patch('refi_monitor.notifications.mail')
    def test_send_welcome_email_success(self, mock_mail, app, sample_user):
        """Test successful welcome email sending."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            result = send_welcome_email(user.id)

            assert result is True
            mock_mail.send.assert_called_once()

            # Check email log was created
            log = EmailLog.query.filter_by(user_id=user.id, email_type='welcome').first()
            assert log is not None
            assert log.status == 'sent'

    @patch('refi_monitor.notifications.mail')
    def test_send_welcome_email_skips_unsubscribed(self, mock_mail, app, unsubscribed_user):
        """Test that welcome email is not sent to unsubscribed users."""
        with app.app_context():
            user = User.query.get(unsubscribed_user.id)
            result = send_welcome_email(user.id)

            assert result is False
            mock_mail.send.assert_not_called()

    def test_send_welcome_email_invalid_user(self, app):
        """Test welcome email with invalid user ID."""
        with app.app_context():
            result = send_welcome_email(99999)
            assert result is False

    @patch('refi_monitor.notifications.mail')
    def test_send_welcome_email_failure(self, mock_mail, app, sample_user):
        """Test handling of email sending failure."""
        mock_mail.send.side_effect = Exception('SMTP error')

        with app.app_context():
            user = User.query.get(sample_user.id)
            result = send_welcome_email(user.id)

            assert result is False

            log = EmailLog.query.filter_by(user_id=user.id, email_type='welcome').first()
            assert log.status == 'failed'
            assert 'SMTP error' in log.error_message


class TestAlertCreatedEmail:
    """Tests for alert created confirmation email."""

    @patch('refi_monitor.notifications.mail')
    def test_send_alert_created_confirmation_success(self, mock_mail, app, sample_alert):
        """Test successful alert created email sending."""
        with app.app_context():
            alert = Alert.query.get(sample_alert.id)
            result = send_alert_created_confirmation(alert.id)

            assert result is True
            mock_mail.send.assert_called_once()

            log = EmailLog.query.filter_by(alert_id=alert.id, email_type='alert_created').first()
            assert log is not None
            assert log.status == 'sent'

    def test_send_alert_created_invalid_alert(self, app):
        """Test alert created email with invalid alert ID."""
        with app.app_context():
            result = send_alert_created_confirmation(99999)
            assert result is False


class TestAlertNotification:
    """Tests for alert trigger notification email."""

    @patch('refi_monitor.notifications.mail')
    def test_send_alert_notification_success(self, mock_mail, app, sample_trigger):
        """Test successful alert notification sending."""
        with app.app_context():
            trigger = Trigger.query.get(sample_trigger.id)
            result = send_alert_notification(trigger.id)

            assert result is True
            mock_mail.send.assert_called_once()

            log = EmailLog.query.filter_by(trigger_id=trigger.id, email_type='alert_triggered').first()
            assert log is not None
            assert log.status == 'sent'

    def test_send_alert_notification_invalid_trigger(self, app):
        """Test notification with invalid trigger ID."""
        with app.app_context():
            result = send_alert_notification(99999)
            assert result is False

    @patch('refi_monitor.notifications.mail')
    def test_send_alert_notification_inactive_alert(self, mock_mail, app, sample_user, sample_mortgage):
        """Test that notification is not sent for inactive alerts."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            mortgage = Mortgage.query.get(sample_mortgage.id)

            # Create inactive alert
            alert = Alert(
                user_id=user.id,
                mortgage_id=mortgage.id,
                alert_type='interest_rate',
                target_interest_rate=5.5,
                target_term=360,
                estimate_refinance_cost=5000.0,
                payment_status='incomplete',  # Not active
                created_on=datetime.utcnow()
            )
            db.session.add(alert)
            db.session.commit()

            trigger = Trigger(
                alert_id=alert.id,
                alert_type='interest_rate',
                alert_trigger_status=1,
                alert_trigger_reason='Test',
                alert_trigger_date=datetime.utcnow(),
                created_on=datetime.utcnow()
            )
            db.session.add(trigger)
            db.session.commit()

            result = send_alert_notification(trigger.id)

            assert result is False
            mock_mail.send.assert_not_called()


class TestPaymentConfirmation:
    """Tests for payment confirmation email."""

    @patch('refi_monitor.notifications.mail')
    def test_send_payment_confirmation_success(self, mock_mail, app, sample_user, sample_alert):
        """Test successful payment confirmation email."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            alert = Alert.query.get(sample_alert.id)

            result = send_payment_confirmation(user.email, alert.id, 'active')

            assert result is True
            mock_mail.send.assert_called_once()

            log = EmailLog.query.filter_by(alert_id=alert.id, email_type='payment_confirmation').first()
            assert log is not None
            assert log.status == 'sent'

    def test_send_payment_confirmation_invalid_email(self, app):
        """Test payment confirmation with unknown email."""
        with app.app_context():
            result = send_payment_confirmation('unknown@example.com', 1, 'active')
            assert result is False


class TestUnsubscribeConfirmation:
    """Tests for unsubscribe confirmation email."""

    @patch('refi_monitor.notifications.mail')
    def test_send_unsubscribe_confirmation_success(self, mock_mail, app, sample_user):
        """Test successful unsubscribe confirmation email."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            result = send_unsubscribe_confirmation(user.id)

            assert result is True
            mock_mail.send.assert_called_once()

            log = EmailLog.query.filter_by(user_id=user.id, email_type='unsubscribe_confirmation').first()
            assert log is not None
            assert log.status == 'sent'


class TestUnsubscribeRoute:
    """Tests for unsubscribe route."""

    def test_unsubscribe_invalid_token(self, client):
        """Test unsubscribe with invalid token returns 404."""
        response = client.get('/unsubscribe/invalid-token')
        assert response.status_code == 404

    def test_unsubscribe_get_shows_confirmation(self, app, client, sample_user):
        """Test GET request shows confirmation page."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            token = user.generate_unsubscribe_token()
            db.session.commit()

        response = client.get(f'/unsubscribe/{token}')
        assert response.status_code == 200
        assert b'Confirm Unsubscribe' in response.data or b'confirm' in response.data.lower()

    @patch('refi_monitor.notifications.mail')
    def test_unsubscribe_post_processes_request(self, mock_mail, app, client, sample_user):
        """Test POST request processes unsubscribe."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            token = user.generate_unsubscribe_token()
            db.session.commit()

        response = client.post(f'/unsubscribe/{token}')
        assert response.status_code == 200

        with app.app_context():
            user = User.query.get(sample_user.id)
            assert user.email_unsubscribed is True
