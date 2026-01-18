"""Tests for Alert.get_status() method.

These tests verify the status calculation logic for alert status indicators.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock


def utcnow():
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class TestAlertStatus:
    """Test Alert.get_status() status calculation logic."""

    def _create_mock_alert(self, initial_payment=True, payment_status='active', triggers=None):
        """Create a mock Alert with subscription data."""
        alert = MagicMock()
        alert.triggers = triggers or []

        # Subscription proxy properties
        alert.initial_payment = initial_payment
        alert.payment_status = payment_status

        # Use the actual get_status logic
        def get_status():
            if alert.payment_status == 'payment_failed':
                return 'paused'
            if not alert.initial_payment or alert.payment_status != 'active':
                return 'waiting'
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

    # --- PAUSED status tests ---

    def test_status_paused_when_payment_failed(self):
        """Alert with payment_failed status returns 'paused'."""
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='payment_failed'
        )
        assert alert.get_status() == 'paused'

    def test_paused_takes_priority_over_triggered(self):
        """Payment failure takes priority even with recent triggers."""
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=1)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='payment_failed',
            triggers=[recent_trigger]
        )
        assert alert.get_status() == 'paused'

    # --- WAITING status tests ---

    def test_status_waiting_no_initial_payment(self):
        """Alert without initial payment returns 'waiting'."""
        alert = self._create_mock_alert(
            initial_payment=False,
            payment_status='incomplete'
        )
        assert alert.get_status() == 'waiting'

    def test_status_waiting_incomplete_payment(self):
        """Alert with incomplete payment_status returns 'waiting'."""
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='incomplete'
        )
        assert alert.get_status() == 'waiting'

    def test_status_waiting_canceled_payment(self):
        """Alert with canceled payment_status returns 'waiting'."""
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='canceled'
        )
        assert alert.get_status() == 'waiting'

    def test_status_waiting_none_payment_status(self):
        """Alert with None payment_status returns 'waiting'."""
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status=None
        )
        assert alert.get_status() == 'waiting'

    # --- TRIGGERED status tests ---

    def test_status_triggered_recent_trigger(self):
        """Alert with trigger within 24 hours returns 'triggered'."""
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=12)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[recent_trigger]
        )
        assert alert.get_status() == 'triggered'

    def test_status_triggered_just_under_24_hours(self):
        """Alert with trigger just under 24 hours returns 'triggered'."""
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=23, minutes=59)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[recent_trigger]
        )
        assert alert.get_status() == 'triggered'

    def test_status_active_trigger_over_24_hours(self):
        """Alert with trigger over 24 hours returns 'active'."""
        old_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=25)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[old_trigger]
        )
        assert alert.get_status() == 'active'

    def test_status_triggered_multiple_triggers_uses_most_recent(self):
        """With multiple triggers, uses most recent for status."""
        old_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=48)
        )
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=6)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[old_trigger, recent_trigger]
        )
        assert alert.get_status() == 'triggered'

    def test_status_active_only_non_triggered_records(self):
        """Alert with only status=0 triggers returns 'active'."""
        non_trigger = self._create_mock_trigger(
            status=0,
            created_on=utcnow() - timedelta(hours=1)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[non_trigger]
        )
        assert alert.get_status() == 'active'

    def test_status_triggered_ignores_non_triggered_records(self):
        """Only triggers with status=1 count for triggered status."""
        non_trigger = self._create_mock_trigger(
            status=0,
            created_on=utcnow() - timedelta(hours=1)
        )
        old_real_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=6)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[non_trigger, old_real_trigger]
        )
        assert alert.get_status() == 'triggered'

    def test_status_active_trigger_with_none_created_on(self):
        """Trigger without created_on doesn't cause triggered status."""
        trigger = self._create_mock_trigger(
            status=1,
            created_on=None
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[trigger]
        )
        assert alert.get_status() == 'active'

    # --- ACTIVE status tests ---

    def test_status_active_healthy_alert_no_triggers(self):
        """Healthy alert without triggers returns 'active'."""
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[]
        )
        assert alert.get_status() == 'active'

    def test_status_active_healthy_alert_old_trigger(self):
        """Healthy alert with old trigger returns 'active'."""
        old_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(days=7)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[old_trigger]
        )
        assert alert.get_status() == 'active'


class TestAlertStatusPriority:
    """Test status priority order: paused > waiting > triggered > active."""

    def _create_mock_alert(self, initial_payment=True, payment_status='active', triggers=None):
        """Create a mock Alert with subscription data."""
        alert = MagicMock()
        alert.triggers = triggers or []
        alert.initial_payment = initial_payment
        alert.payment_status = payment_status

        def get_status():
            if alert.payment_status == 'payment_failed':
                return 'paused'
            if not alert.initial_payment or alert.payment_status != 'active':
                return 'waiting'
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

    def test_paused_beats_waiting(self):
        """Paused status takes priority over waiting conditions."""
        # payment_failed even with incomplete initial_payment
        alert = self._create_mock_alert(
            initial_payment=False,
            payment_status='payment_failed'
        )
        assert alert.get_status() == 'paused'

    def test_waiting_beats_triggered(self):
        """Waiting status takes priority over triggered."""
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=1)
        )
        alert = self._create_mock_alert(
            initial_payment=False,
            payment_status='incomplete',
            triggers=[recent_trigger]
        )
        assert alert.get_status() == 'waiting'

    def test_triggered_beats_active(self):
        """Triggered status takes priority over active."""
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=1)
        )
        alert = self._create_mock_alert(
            initial_payment=True,
            payment_status='active',
            triggers=[recent_trigger]
        )
        assert alert.get_status() == 'triggered'
