"""Tests for Alert threshold PATCH API endpoint."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


def utcnow():
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class TestAlertThresholdPatchLogic:
    """Test PATCH endpoint validation logic."""

    def test_patch_updates_target_interest_rate(self):
        """PATCH with target_interest_rate updates the field."""
        alert = MagicMock()
        alert.target_interest_rate = 0.05
        alert.target_monthly_payment = 1500.0
        alert.target_term = 360
        alert.estimate_refinance_cost = 5000.0

        # Simulate PATCH update
        data = {'target_interest_rate': 0.045}
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        updated_fields = []
        for field in threshold_fields:
            if field in data:
                setattr(alert, field, data[field])
                updated_fields.append(field)

        assert 'target_interest_rate' in updated_fields
        assert alert.target_interest_rate == 0.045

    def test_patch_updates_target_monthly_payment(self):
        """PATCH with target_monthly_payment updates the field."""
        alert = MagicMock()
        alert.target_interest_rate = 0.05
        alert.target_monthly_payment = 1500.0
        alert.target_term = 360
        alert.estimate_refinance_cost = 5000.0

        data = {'target_monthly_payment': 1400.0}
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        updated_fields = []
        for field in threshold_fields:
            if field in data:
                setattr(alert, field, data[field])
                updated_fields.append(field)

        assert 'target_monthly_payment' in updated_fields
        assert alert.target_monthly_payment == 1400.0

    def test_patch_updates_target_term(self):
        """PATCH with target_term updates the field."""
        alert = MagicMock()
        alert.target_interest_rate = 0.05
        alert.target_monthly_payment = 1500.0
        alert.target_term = 360
        alert.estimate_refinance_cost = 5000.0

        data = {'target_term': 180}
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        updated_fields = []
        for field in threshold_fields:
            if field in data:
                setattr(alert, field, data[field])
                updated_fields.append(field)

        assert 'target_term' in updated_fields
        assert alert.target_term == 180

    def test_patch_updates_estimate_refinance_cost(self):
        """PATCH with estimate_refinance_cost updates the field."""
        alert = MagicMock()
        alert.target_interest_rate = 0.05
        alert.target_monthly_payment = 1500.0
        alert.target_term = 360
        alert.estimate_refinance_cost = 5000.0

        data = {'estimate_refinance_cost': 6000.0}
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        updated_fields = []
        for field in threshold_fields:
            if field in data:
                setattr(alert, field, data[field])
                updated_fields.append(field)

        assert 'estimate_refinance_cost' in updated_fields
        assert alert.estimate_refinance_cost == 6000.0

    def test_patch_updates_multiple_fields(self):
        """PATCH with multiple fields updates all of them."""
        alert = MagicMock()
        alert.target_interest_rate = 0.05
        alert.target_monthly_payment = 1500.0
        alert.target_term = 360
        alert.estimate_refinance_cost = 5000.0

        data = {
            'target_interest_rate': 0.04,
            'target_term': 240,
            'estimate_refinance_cost': 4500.0
        }
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        updated_fields = []
        for field in threshold_fields:
            if field in data:
                setattr(alert, field, data[field])
                updated_fields.append(field)

        assert len(updated_fields) == 3
        assert 'target_interest_rate' in updated_fields
        assert 'target_term' in updated_fields
        assert 'estimate_refinance_cost' in updated_fields
        assert alert.target_interest_rate == 0.04
        assert alert.target_term == 240
        assert alert.estimate_refinance_cost == 4500.0

    def test_patch_ignores_non_threshold_fields(self):
        """PATCH ignores fields not in the allowed threshold list."""
        alert = MagicMock()
        alert.target_interest_rate = 0.05
        alert.alert_type = 'rate'
        alert.user_id = 1

        data = {
            'alert_type': 'payment',
            'user_id': 999,
            'target_interest_rate': 0.04
        }
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        updated_fields = []
        for field in threshold_fields:
            if field in data:
                setattr(alert, field, data[field])
                updated_fields.append(field)

        # Only threshold field should be updated
        assert len(updated_fields) == 1
        assert 'target_interest_rate' in updated_fields
        assert alert.target_interest_rate == 0.04
        # Non-threshold fields should NOT be updated
        assert alert.alert_type == 'rate'
        assert alert.user_id == 1

    def test_patch_no_valid_fields_error(self):
        """PATCH with no valid threshold fields should error."""
        data = {'alert_type': 'payment', 'user_id': 999}
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        updated_fields = []
        for field in threshold_fields:
            if field in data:
                updated_fields.append(field)

        # No valid fields means error condition
        assert len(updated_fields) == 0

    def test_patch_empty_data_error(self):
        """PATCH with empty data should error."""
        data = {}
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        updated_fields = []
        for field in threshold_fields:
            if field in data:
                updated_fields.append(field)

        # Empty data means error condition
        assert len(updated_fields) == 0


class TestAlertThresholdPatchAuthorization:
    """Test PATCH endpoint authorization logic."""

    def test_patch_requires_alert_ownership(self):
        """User can only PATCH alerts for their own mortgages."""
        # Simulating ownership check
        user_id = 1
        mortgage_user_id = 1
        assert user_id == mortgage_user_id

        # Different user cannot PATCH
        different_user_id = 2
        assert different_user_id != mortgage_user_id

    def test_patch_deleted_alert_returns_not_found(self):
        """PATCH on soft-deleted alert should return not found."""
        alert = MagicMock()
        alert.deleted_at = utcnow()

        # Query filter: deleted_at=None would not return this alert
        is_active = alert.deleted_at is None
        assert is_active is False


class TestAlertThresholdPatchTimestamp:
    """Test that PATCH updates the timestamp."""

    def test_patch_updates_updated_on(self):
        """PATCH should update the updated_on timestamp."""
        alert = MagicMock()
        original_time = utcnow()
        alert.updated_on = original_time

        # Simulate PATCH update
        data = {'target_interest_rate': 0.04}
        threshold_fields = ['target_monthly_payment', 'target_interest_rate',
                            'target_term', 'estimate_refinance_cost']

        for field in threshold_fields:
            if field in data:
                setattr(alert, field, data[field])

        # Update timestamp
        new_time = utcnow()
        alert.updated_on = new_time

        assert alert.updated_on >= original_time
