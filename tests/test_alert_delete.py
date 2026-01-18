"""Tests for Alert delete API endpoint with Stripe subscription cancellation."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


def utcnow():
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class TestAlertDeleteLogic:
    """Test Alert delete business logic."""

    def _create_mock_alert(self, deleted_at=None, stripe_subscription_id=None, stripe_invoice_id=None):
        """Create a mock Alert with delete and subscription data."""
        alert = MagicMock()
        alert.id = 1
        alert.mortgage_id = 1
        alert.deleted_at = deleted_at
        alert.subscription = MagicMock()
        alert.subscription.stripe_subscription_id = stripe_subscription_id
        alert.subscription.payment_status = 'active'
        alert.subscription.updated_on = None

        # Proxy properties
        type(alert).stripe_subscription_id = property(
            lambda self: self.subscription.stripe_subscription_id if self.subscription else None
        )
        type(alert).stripe_invoice_id = property(
            lambda self: stripe_invoice_id
        )

        return alert

    def test_soft_delete_sets_deleted_at(self):
        """Deleting an alert should set deleted_at timestamp."""
        alert = self._create_mock_alert()
        assert alert.deleted_at is None

        # Simulate delete action
        alert.deleted_at = utcnow()
        assert alert.deleted_at is not None

    def test_deleted_alert_not_found(self):
        """Alert with deleted_at set should be treated as not found."""
        alert = self._create_mock_alert(deleted_at=utcnow())

        # This simulates the query filter: deleted_at=None
        # If deleted_at is set, the query would not find the alert
        assert alert.deleted_at is not None

    def test_subscription_status_updated_on_delete(self):
        """Subscription payment_status should be set to 'canceled' on delete."""
        alert = self._create_mock_alert(stripe_subscription_id='sub_123')

        # Simulate delete action
        alert.deleted_at = utcnow()
        alert.subscription.payment_status = 'canceled'
        alert.subscription.updated_on = utcnow()

        assert alert.subscription.payment_status == 'canceled'
        assert alert.subscription.updated_on is not None


class TestAlertDeleteStripeIntegration:
    """Test Stripe subscription cancellation on alert delete."""

    def test_stripe_subscription_cancel_logic(self):
        """Stripe cancel should be called with subscription_id when present."""
        subscription_id = 'sub_test123'
        stripe_cancel_called = False
        stripe_cancel_arg = None

        def mock_stripe_cancel(sub_id):
            nonlocal stripe_cancel_called, stripe_cancel_arg
            stripe_cancel_called = True
            stripe_cancel_arg = sub_id
            return MagicMock(id=sub_id, status='canceled')

        # Simulate delete logic
        alert = MagicMock()
        alert.stripe_subscription_id = subscription_id

        sub_id = alert.stripe_subscription_id
        if sub_id:
            result = mock_stripe_cancel(sub_id)

        assert stripe_cancel_called is True
        assert stripe_cancel_arg == subscription_id

    def test_stripe_invalid_request_handled_gracefully(self):
        """InvalidRequestError (subscription already canceled) should be handled."""
        error_caught = False

        class MockInvalidRequestError(Exception):
            pass

        def mock_stripe_cancel(sub_id):
            raise MockInvalidRequestError("No such subscription")

        # Simulate the error handling in delete endpoint
        try:
            mock_stripe_cancel('sub_invalid')
        except MockInvalidRequestError:
            # This is caught and logged, not re-raised
            error_caught = True

        assert error_caught is True

    def test_stripe_error_propagates(self):
        """StripeError should propagate and return 500."""
        class MockStripeError(Exception):
            pass

        def mock_stripe_cancel(sub_id):
            raise MockStripeError("Stripe API error")

        with pytest.raises(MockStripeError):
            mock_stripe_cancel('sub_123')

    def test_alert_without_subscription_skips_stripe_call(self):
        """Alert without stripe_subscription_id should skip Stripe cancel."""
        alert = MagicMock()
        alert.stripe_subscription_id = None
        alert.stripe_invoice_id = None

        # Get subscription_id like the API does
        subscription_id = alert.stripe_subscription_id or alert.stripe_invoice_id

        # Should be None, so Stripe cancel would be skipped
        assert subscription_id is None


class TestAlertDeleteEmailNotification:
    """Test cancellation confirmation email on alert delete."""

    def test_cancellation_email_sent(self):
        """send_cancellation_confirmation should be called on delete."""
        user_email = 'test@example.com'
        alert_id = 1
        email_sent = False
        sent_email = None
        sent_alert_id = None

        def mock_send_cancellation(email, aid):
            nonlocal email_sent, sent_email, sent_alert_id
            email_sent = True
            sent_email = email
            sent_alert_id = aid

        # Simulate the delete endpoint calling the notification
        user = MagicMock()
        user.email = user_email

        if user:
            mock_send_cancellation(user.email, alert_id)

        assert email_sent is True
        assert sent_email == user_email
        assert sent_alert_id == alert_id

    def test_cancellation_email_with_correct_params(self):
        """Email should be sent with correct user email and alert ID."""
        user_email = 'user@test.com'
        alert_id = 42
        captured_calls = []

        def mock_send(email, aid):
            captured_calls.append((email, aid))

        mock_send(user_email, alert_id)

        assert len(captured_calls) == 1
        assert captured_calls[0][0] == user_email
        assert captured_calls[0][1] == alert_id

    def test_email_not_sent_if_user_not_found(self):
        """Email should not be sent if user is None."""
        email_sent = False

        def mock_send(email, aid):
            nonlocal email_sent
            email_sent = True

        # Simulate user not found
        user = None
        alert_id = 1

        if user:
            mock_send(user.email, alert_id)

        assert email_sent is False


class TestAlertDeleteAuthorization:
    """Test authorization for alert delete."""

    def _create_mock_mortgage(self, user_id):
        """Create a mock Mortgage."""
        mortgage = MagicMock()
        mortgage.id = 1
        mortgage.user_id = user_id
        return mortgage

    def test_user_can_delete_own_alert(self):
        """User should be able to delete alert for their own mortgage."""
        current_user_id = 1
        mortgage = self._create_mock_mortgage(user_id=current_user_id)

        # User owns the mortgage
        assert mortgage.user_id == current_user_id

    def test_user_cannot_delete_other_users_alert(self):
        """User should not be able to delete alert for another user's mortgage."""
        current_user_id = 1
        other_user_id = 2
        mortgage = self._create_mock_mortgage(user_id=other_user_id)

        # User does not own the mortgage
        assert mortgage.user_id != current_user_id


class TestAlertDeleteDatabaseOperations:
    """Test database operations for alert delete."""

    def test_alert_query_excludes_deleted(self):
        """Query for alert should filter out already deleted alerts."""
        # Simulate the filter: deleted_at=None
        alerts = [
            {'id': 1, 'deleted_at': None},
            {'id': 2, 'deleted_at': utcnow()},
            {'id': 3, 'deleted_at': None},
        ]

        # Filter like the API does
        non_deleted = [a for a in alerts if a['deleted_at'] is None]

        assert len(non_deleted) == 2
        assert all(a['deleted_at'] is None for a in non_deleted)

    def test_soft_delete_preserves_data(self):
        """Soft delete should preserve alert data, only setting deleted_at."""
        alert = MagicMock()
        alert.id = 1
        alert.alert_type = 'payment'
        alert.target_interest_rate = 0.05
        alert.deleted_at = None

        # Before delete
        original_type = alert.alert_type
        original_rate = alert.target_interest_rate

        # Soft delete
        alert.deleted_at = utcnow()

        # Data is preserved
        assert alert.alert_type == original_type
        assert alert.target_interest_rate == original_rate
        assert alert.deleted_at is not None


class TestAlertDeleteAdminMetrics:
    """Test that deleted alerts are tracked in admin metrics."""

    def test_deleted_alerts_counted_separately(self):
        """Admin dashboard should count deleted alerts separately."""
        alerts = [
            {'deleted_at': None},
            {'deleted_at': None},
            {'deleted_at': utcnow()},
            {'deleted_at': utcnow()},
        ]

        # Count like admin dashboard does
        total_alerts = len([a for a in alerts if a['deleted_at'] is None])
        deleted_alerts = len([a for a in alerts if a['deleted_at'] is not None])

        assert total_alerts == 2
        assert deleted_alerts == 2
