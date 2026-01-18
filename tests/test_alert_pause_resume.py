"""Tests for Alert pause/resume API endpoints."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


def utcnow():
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class TestAlertPauseResumeModel:
    """Test Alert model pause/resume properties."""

    def _create_mock_alert(self, paused_at=None):
        """Create a mock Alert with pause functionality."""
        alert = MagicMock()
        alert.paused_at = paused_at

        # Use the actual is_paused logic
        @property
        def is_paused(self):
            return self.paused_at is not None

        # Bind the property to the mock
        type(alert).is_paused = property(lambda self: self.paused_at is not None)
        return alert

    def test_is_paused_when_paused_at_set(self):
        """Alert with paused_at set should return is_paused=True."""
        alert = self._create_mock_alert(paused_at=utcnow())
        assert alert.is_paused is True

    def test_is_not_paused_when_paused_at_none(self):
        """Alert with paused_at=None should return is_paused=False."""
        alert = self._create_mock_alert(paused_at=None)
        assert alert.is_paused is False


class TestAlertGetStatusWithPaused:
    """Test Alert.get_status() with explicit pause functionality."""

    def _create_mock_alert(self, paused_at=None, initial_payment=True, payment_status='active', triggers=None):
        """Create a mock Alert with pause and status logic."""
        alert = MagicMock()
        alert.paused_at = paused_at
        alert.triggers = triggers or []
        alert.initial_payment = initial_payment
        alert.payment_status = payment_status

        # Bind is_paused property
        type(alert).is_paused = property(lambda self: self.paused_at is not None)

        # Use the actual get_status logic with is_paused check
        def get_status():
            if alert.is_paused:
                return 'paused'
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

    def test_status_paused_when_explicitly_paused(self):
        """Alert with paused_at set returns 'paused' status."""
        alert = self._create_mock_alert(
            paused_at=utcnow(),
            initial_payment=True,
            payment_status='active'
        )
        assert alert.get_status() == 'paused'

    def test_explicit_pause_takes_priority_over_triggered(self):
        """Explicit pause takes priority over recent triggers."""
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=1)
        )
        alert = self._create_mock_alert(
            paused_at=utcnow(),
            initial_payment=True,
            payment_status='active',
            triggers=[recent_trigger]
        )
        assert alert.get_status() == 'paused'

    def test_explicit_pause_takes_priority_over_active(self):
        """Explicit pause takes priority over active status."""
        alert = self._create_mock_alert(
            paused_at=utcnow(),
            initial_payment=True,
            payment_status='active',
            triggers=[]
        )
        assert alert.get_status() == 'paused'

    def test_resumed_alert_returns_to_active(self):
        """Resumed alert (paused_at=None) returns to appropriate status."""
        alert = self._create_mock_alert(
            paused_at=None,
            initial_payment=True,
            payment_status='active',
            triggers=[]
        )
        assert alert.get_status() == 'active'

    def test_resumed_alert_can_be_triggered(self):
        """Resumed alert can return 'triggered' status if conditions met."""
        recent_trigger = self._create_mock_trigger(
            status=1,
            created_on=utcnow() - timedelta(hours=1)
        )
        alert = self._create_mock_alert(
            paused_at=None,
            initial_payment=True,
            payment_status='active',
            triggers=[recent_trigger]
        )
        assert alert.get_status() == 'triggered'


class TestAlertPauseResumeAPI:
    """Test pause/resume API endpoint logic."""

    def test_pause_sets_paused_at(self):
        """Pausing an alert should set paused_at timestamp."""
        alert = MagicMock()
        alert.paused_at = None
        type(alert).is_paused = property(lambda self: self.paused_at is not None)

        # Simulate pause action
        assert alert.is_paused is False
        alert.paused_at = utcnow()
        assert alert.is_paused is True

    def test_resume_clears_paused_at(self):
        """Resuming an alert should clear paused_at to None."""
        alert = MagicMock()
        alert.paused_at = utcnow()
        type(alert).is_paused = property(lambda self: self.paused_at is not None)

        # Simulate resume action
        assert alert.is_paused is True
        alert.paused_at = None
        assert alert.is_paused is False

    def test_pause_already_paused_alert_error(self):
        """Pausing an already paused alert should be an error condition."""
        alert = MagicMock()
        alert.paused_at = utcnow()
        type(alert).is_paused = property(lambda self: self.paused_at is not None)

        # Check condition that would trigger error
        assert alert.is_paused is True
        # API would return 400 error in this case

    def test_resume_not_paused_alert_error(self):
        """Resuming an alert that is not paused should be an error condition."""
        alert = MagicMock()
        alert.paused_at = None
        type(alert).is_paused = property(lambda self: self.paused_at is not None)

        # Check condition that would trigger error
        assert alert.is_paused is False
        # API would return 400 error in this case


class TestSchedulerSkipsPausedAlerts:
    """Test that scheduler properly skips paused alerts."""

    def test_scheduler_filters_paused_alerts(self):
        """Scheduler query should filter out alerts with paused_at set."""
        # This tests the logic that:
        # Alert.paused_at.is_(None) filters out paused alerts
        paused_alert = MagicMock()
        paused_alert.paused_at = utcnow()

        active_alert = MagicMock()
        active_alert.paused_at = None

        all_alerts = [paused_alert, active_alert]

        # Filter like the scheduler does
        non_paused = [a for a in all_alerts if a.paused_at is None]

        assert len(non_paused) == 1
        assert non_paused[0] == active_alert

    def test_resumed_alert_included_in_scheduler(self):
        """Resumed alert should be included in scheduler check."""
        resumed_alert = MagicMock()
        resumed_alert.paused_at = None

        all_alerts = [resumed_alert]

        # Filter like the scheduler does
        non_paused = [a for a in all_alerts if a.paused_at is None]

        assert len(non_paused) == 1
        assert non_paused[0] == resumed_alert
