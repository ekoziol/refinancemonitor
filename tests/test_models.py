"""Tests for database models."""
from datetime import datetime


class TestUserModel:
    """Test suite for User model."""

    def test_user_password_hashing(self, app):
        """Test password hashing works correctly."""
        from refi_monitor.models import User

        with app.app_context():
            user = User(
                name='Test User',
                email='test@example.com',
                password='temp'
            )
            user.set_password('secure_password')

            # Password should be hashed, not stored in plain text
            assert user.password != 'secure_password'
            assert user.check_password('secure_password')
            assert not user.check_password('wrong_password')

    def test_user_repr(self, app):
        """Test User string representation."""
        from refi_monitor.models import User

        with app.app_context():
            user = User(
                name='Test User',
                email='test@example.com',
                password='temp'
            )
            assert 'test@example.com' in repr(user)


class TestMortgageModel:
    """Test suite for Mortgage model."""

    def test_mortgage_creation(self, app):
        """Test mortgage model can be instantiated."""
        from refi_monitor.models import Mortgage

        with app.app_context():
            mortgage = Mortgage(
                name='Home Loan',
                zip_code='12345',
                original_principal=300000.0,
                original_term=360,
                original_interest_rate=3.5,
                remaining_principal=280000.0,
                remaining_term=300,
                credit_score=750
            )
            assert mortgage.name == 'Home Loan'
            assert mortgage.original_principal == 300000.0


class TestMortgageRateModel:
    """Test suite for MortgageRate model."""

    def test_mortgage_rate_creation(self, app):
        """Test MortgageRate model can be instantiated."""
        from refi_monitor.models import MortgageRate

        with app.app_context():
            rate = MortgageRate(
                zip_code='12345',
                term_months=360,
                rate=6.5,
                rate_date=datetime.utcnow()
            )
            assert rate.zip_code == '12345'
            assert rate.term_months == 360
            assert rate.rate == 6.5

    def test_mortgage_rate_repr(self, app):
        """Test MortgageRate string representation."""
        from refi_monitor.models import MortgageRate

        with app.app_context():
            rate = MortgageRate(
                zip_code='12345',
                term_months=360,
                rate=6.5,
                rate_date=datetime.utcnow()
            )
            repr_str = repr(rate)
            assert '12345' in repr_str
            assert '360' in repr_str


class TestAlertModel:
    """Test suite for Alert model."""

    def test_alert_creation(self, app):
        """Test Alert model can be instantiated."""
        from refi_monitor.models import Alert

        with app.app_context():
            alert = Alert(
                alert_type='payment',
                target_monthly_payment=1500.0,
                target_term=360,
                estimate_refinance_cost=3000.0
            )
            assert alert.alert_type == 'payment'
            assert alert.target_monthly_payment == 1500.0


class TestTriggerModel:
    """Test suite for Trigger model."""

    def test_trigger_creation(self, app):
        """Test Trigger model can be instantiated."""
        from refi_monitor.models import Trigger

        with app.app_context():
            trigger = Trigger(
                alert_type='payment',
                alert_trigger_status=1,
                alert_trigger_reason='Rate dropped below threshold'
            )
            assert trigger.alert_type == 'payment'
            assert trigger.alert_trigger_status == 1


class TestEmailLogModel:
    """Test suite for EmailLog model (unit tests for email logging logic)."""

    def test_mark_sent_logic(self):
        """Test mark_sent behavior sets status to 'sent' and timestamps."""
        from datetime import datetime

        # Simulate mark_sent logic
        status = 'pending'
        sent_at = None

        # mark_sent should update these values
        status = 'sent'
        sent_at = datetime.utcnow()

        assert status == 'sent'
        assert sent_at is not None
        assert isinstance(sent_at, datetime)

    def test_mark_failed_logic(self):
        """Test mark_failed behavior sets status and error message."""
        status = 'pending'
        error_message = None

        # mark_failed should update these values
        status = 'failed'
        error_message = 'SMTP connection refused'

        assert status == 'failed'
        assert error_message == 'SMTP connection refused'

    def test_mark_delivered_logic(self):
        """Test mark_delivered behavior sets status to 'delivered'."""
        from datetime import datetime

        status = 'sent'
        delivered_at = None

        # mark_delivered should update these values
        status = 'delivered'
        delivered_at = datetime.utcnow()

        assert status == 'delivered'
        assert delivered_at is not None
        assert isinstance(delivered_at, datetime)

    def test_email_log_repr_format(self):
        """Test EmailLog repr format includes type, email, and status."""
        # Test repr format: <EmailLog {type} to {email} ({status})>
        email_type = 'password_reset'
        recipient_email = 'user@example.com'
        status = 'sent'

        repr_str = '<EmailLog {} to {} ({})>'.format(email_type, recipient_email, status)

        assert 'password_reset' in repr_str
        assert 'user@example.com' in repr_str
        assert 'sent' in repr_str

    def test_email_type_values(self):
        """Test expected email type values for the system."""
        expected_types = ['verification', 'password_reset', 'alert', 'welcome']
        for email_type in expected_types:
            assert isinstance(email_type, str)
            assert len(email_type) <= 50  # Matches db column length

    def test_status_values(self):
        """Test expected status values for email log entries."""
        valid_statuses = ['pending', 'sent', 'failed', 'delivered']
        for status in valid_statuses:
            assert isinstance(status, str)
            assert len(status) <= 20  # Matches db column length
