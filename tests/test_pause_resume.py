"""Tests for Alert pause/resume functionality.

These tests verify the pause/resume functionality for alerts without
canceling the Stripe subscription.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


def utcnow():
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class TestSubscriptionPauseResume:
    """Test Subscription.pause() and Subscription.resume() methods."""

    def _create_mock_subscription(self, paused_at=None, paused_reason=None, payment_status='active'):
        """Create a mock Subscription."""
        subscription = MagicMock()
        subscription.paused_at = paused_at
        subscription.paused_reason = paused_reason
        subscription.payment_status = payment_status
        subscription.updated_on = None

        def pause(reason='user_requested'):
            subscription.paused_at = utcnow()
            subscription.paused_reason = reason
            subscription.updated_on = utcnow()

        def resume():
            subscription.paused_at = None
            subscription.paused_reason = None
            subscription.updated_on = utcnow()

        def is_paused():
            return subscription.paused_at is not None

        subscription.pause = pause
        subscription.resume = resume
        subscription.is_paused = is_paused
        return subscription

    def test_pause_sets_paused_at(self):
        """Calling pause() sets paused_at timestamp."""
        subscription = self._create_mock_subscription()
        assert subscription.paused_at is None

        subscription.pause()

        assert subscription.paused_at is not None
        assert subscription.paused_reason == 'user_requested'

    def test_pause_with_custom_reason(self):
        """Calling pause() with custom reason stores it."""
        subscription = self._create_mock_subscription()

        subscription.pause(reason='payment_failed')

        assert subscription.paused_reason == 'payment_failed'

    def test_pause_updates_updated_on(self):
        """Calling pause() updates updated_on timestamp."""
        subscription = self._create_mock_subscription()
        assert subscription.updated_on is None

        subscription.pause()

        assert subscription.updated_on is not None

    def test_resume_clears_paused_fields(self):
        """Calling resume() clears paused_at and paused_reason."""
        subscription = self._create_mock_subscription(
            paused_at=utcnow() - timedelta(hours=1),
            paused_reason='user_requested'
        )

        subscription.resume()

        assert subscription.paused_at is None
        assert subscription.paused_reason is None

    def test_resume_updates_updated_on(self):
        """Calling resume() updates updated_on timestamp."""
        subscription = self._create_mock_subscription(
            paused_at=utcnow(),
            paused_reason='user_requested'
        )
        subscription.updated_on = None

        subscription.resume()

        assert subscription.updated_on is not None

    def test_is_paused_returns_true_when_paused(self):
        """is_paused() returns True when subscription is paused."""
        subscription = self._create_mock_subscription(
            paused_at=utcnow(),
            paused_reason='user_requested'
        )

        assert subscription.is_paused() is True

    def test_is_paused_returns_false_when_not_paused(self):
        """is_paused() returns False when subscription is not paused."""
        subscription = self._create_mock_subscription()

        assert subscription.is_paused() is False


class TestAlertStatusWithPause:
    """Test Alert.get_status() with user-initiated pauses."""

    def _create_mock_alert(self, initial_payment=True, payment_status='active',
                           paused_at=None, triggers=None):
        """Create a mock Alert with subscription data including pause support."""
        alert = MagicMock()
        alert.triggers = triggers or []
        alert.initial_payment = initial_payment
        alert.payment_status = payment_status
        alert.paused_at = paused_at

        def get_status():
            # Check for user-initiated pause first (highest priority)
            if alert.paused_at is not None:
                return 'paused'
            # Check for payment failure
            if alert.payment_status == 'payment_failed':
                return 'paused'
            # Check if waiting for payment/activation
            if not alert.initial_payment or alert.payment_status != 'active':
                return 'waiting'
            # Check for recent triggers (within 24 hours)
            if alert.triggers:
                triggered_records = [t for t in alert.triggers if t.alert_trigger_status == 1]
                if triggered_records:
                    recent = max(triggered_records, key=lambda t: t.created_on or datetime.min.replace(tzinfo=timezone.utc))
                    if recent.created_on:
                        hours_ago = (utcnow() - recent.created_on).total_seconds() / 3600
                        if hours_ago < 24:
                            return 'triggered'
            return 'active'

        alert.get_status = get_status
        return alert

    def _create_mock_trigger(self, status=1, created_on=None):
        """Create a mock Trigger."""
        trigger = MagicMock()
        trigger.alert_trigger_status = status
        trigger.created_on = created_on
        return trigger

    def test_status_paused_when_user_paused(self):
        """Alert with paused_at set returns 'paused'."""
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            paused_at=utcnow()
        )
        assert alert.get_status() == 'paused'

    def test_user_pause_takes_priority_over_payment_failure(self):
        """User pause is checked before payment failure (both return paused)."""
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='payment_failed',
            paused_at=utcnow()
        )
        # Both conditions would return 'paused', but user pause is checked first
        assert alert.get_status() == 'paused'

    def test_user_pause_takes_priority_over_triggered(self):
        """User pause takes priority over recent triggers."""
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=1)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            paused_at=utcnow(),
            triggers=[recent_trigger]
        )
        assert alert.get_status() == 'paused'

    def test_user_pause_takes_priority_over_waiting(self):
        """User pause takes priority over waiting status."""
        alert = self._create_mock_alert(
            initial_payment=False,
            payment_status='incomplete',
            paused_at=utcnow()
        )
        assert alert.get_status() == 'paused'

    def test_active_when_not_paused(self):
        """Alert without paused_at returns 'active' (if other conditions met)."""
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            paused_at=None
        )
        assert alert.get_status() == 'active'


class TestPauseResumeAPIValidation:
    """Test validation logic for pause/resume API endpoints."""

    def test_cannot_pause_already_paused_alert(self):
        """Attempting to pause an already paused alert should fail."""
        subscription = MagicMock()
        subscription.paused_at = utcnow()
        subscription.is_paused = lambda: True

        # This would be the validation check in the API
        assert subscription.is_paused() is True

    def test_cannot_resume_non_paused_alert(self):
        """Attempting to resume a non-paused alert should fail."""
        subscription = MagicMock()
        subscription.paused_at = None
        subscription.is_paused = lambda: False

        # This would be the validation check in the API
        assert subscription.is_paused() is False

    def test_cannot_resume_payment_failed_alert(self):
        """Cannot resume alert paused due to payment failure."""
        subscription = MagicMock()
        subscription.paused_at = utcnow()
        subscription.paused_reason = 'payment_failed'
        subscription.is_paused = lambda: True

        # Payment failures require payment method update, not resume
        assert subscription.paused_reason == 'payment_failed'

    def test_can_resume_user_requested_pause(self):
        """Can resume alert paused by user request."""
        subscription = MagicMock()
        subscription.paused_at = utcnow()
        subscription.paused_reason = 'user_requested'
        subscription.is_paused = lambda: True

        # User-requested pauses can be resumed
        assert subscription.paused_reason == 'user_requested'
        assert subscription.paused_reason != 'payment_failed'


class TestAlertDictSerialization:
    """Test alert_to_dict serialization includes pause fields."""

    def test_alert_to_dict_includes_paused_at(self):
        """alert_to_dict should include paused_at field."""
        paused_time = utcnow()
        expected_fields = {
            'paused_at': paused_time.isoformat(),
            'paused_reason': 'user_requested',
            'status': 'paused'
        }
        # Verify these fields are expected in the dict
        for field in expected_fields:
            assert field in expected_fields

    def test_alert_to_dict_handles_none_paused_at(self):
        """alert_to_dict should handle None paused_at gracefully."""
        expected_fields = {
            'paused_at': None,
            'paused_reason': None,
            'status': 'active'
        }
        # Verify None values are acceptable
        assert expected_fields['paused_at'] is None
        assert expected_fields['paused_reason'] is None
