from datetime import datetime
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta


class User(UserMixin, db.Model):
    """User account model."""

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(
        db.String(200), primary_key=False, unique=False, nullable=False
    )
    credit_score = db.Column(db.Integer, index=False, unique=False, nullable=True)
    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    last_login = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    last_paid_date = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    paid = db.Column(db.Integer, index=False, unique=False, nullable=True)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    mortgages = db.relationship("Mortgage")

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def generate_verification_token(self):
        """Generate email verification token with 24-hour expiry."""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.email_verification_token

    def verify_email_token(self, token):
        """Verify the email token and mark email as verified."""
        if (self.email_verification_token == token and
                self.token_expiry and
                datetime.utcnow() < self.token_expiry):
            self.email_verified = True
            self.email_verification_token = None
            self.token_expiry = None
            return True
        return False

    def is_token_expired(self):
        """Check if the verification token has expired."""
        if not self.token_expiry:
            return True
        return datetime.utcnow() >= self.token_expiry

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Mortgage(db.Model):
    __tablename__ = 'mortgage'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False, unique=False)
    zip_code = db.Column(db.String(5), nullable=False, unique=False)
    original_principal = db.Column(db.Float, nullable=False, unique=False)
    original_term = db.Column(db.Integer, nullable=False, unique=False)
    original_interest_rate = db.Column(db.Float, nullable=False, unique=False)
    remaining_principal = db.Column(db.Float, nullable=False, unique=False)
    remaining_term = db.Column(db.Integer, nullable=False, unique=False)
    credit_score = db.Column(db.Integer, nullable=False, unique=False)
    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    trackings = db.relationship("Mortgage_Tracking")
    alerts = db.relationship("Alert")


class Mortgage_Tracking(db.Model):
    __tablename__ = 'mortgage_current_value'
    id = db.Column(db.Integer, primary_key=True)
    mortgage_id = db.Column(db.Integer, db.ForeignKey('mortgage.id'))
    current_rate = db.Column(db.Float, nullable=False, unique=False)
    current_remaining_term = db.Column(db.Integer, nullable=False, unique=False)
    current_remaining_principal = db.Column(db.Float, nullable=False, unique=False)

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)


class Subscription(db.Model):
    """Stripe subscription model for handling payment data.

    Separates payment/subscription concerns from Alert model for cleaner architecture.
    Each Alert can have one Subscription (one-to-one relationship).
    """
    __tablename__ = 'subscription'
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id'), unique=True, nullable=False)

    # Payment status
    initial_payment = db.Column(db.Boolean, index=False, unique=False, nullable=True, default=False)
    payment_status = db.Column(db.String, index=True, unique=False, nullable=True, default='incomplete')
    paused_at = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    # Billing period tracking
    initial_period_start = db.Column(db.Integer, index=False, unique=False, nullable=True)
    initial_period_end = db.Column(db.Integer, index=False, unique=False, nullable=True)
    period_start = db.Column(db.Integer, index=False, unique=False, nullable=True)
    period_end = db.Column(db.Integer, index=False, unique=False, nullable=True)

    # Stripe identifiers
    price_id = db.Column(db.String, index=False, unique=False, nullable=True)
    stripe_customer_id = db.Column(db.String, index=True, unique=False, nullable=True)
    stripe_invoice_id = db.Column(db.String, index=False, unique=False, nullable=True)
    stripe_subscription_id = db.Column(db.String, index=True, unique=False, nullable=True)

    # Timestamps
    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    def __repr__(self):
        return '<Subscription {} for alert {}: {}>'.format(self.id, self.alert_id, self.payment_status)


class Alert(db.Model):
    __tablename__ = 'alert'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mortgage_id = db.Column(db.Integer, db.ForeignKey('mortgage.id'))
    alert_type = db.Column(db.String, nullable=False, unique=False)
    target_monthly_payment = db.Column(db.Float, nullable=True, unique=False)
    target_interest_rate = db.Column(db.Float, nullable=True, unique=False)
    target_term = db.Column(db.Integer, nullable=False, unique=False)
    estimate_refinance_cost = db.Column(db.Float, nullable=False, unique=False)

    calculated_refinance_cost = db.Column(db.Float, nullable=True, unique=False)

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    deleted_at = db.Column(db.DateTime, index=True, unique=False, nullable=True)
    paused_at = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    triggers = db.relationship("Trigger")
    subscription = db.relationship("Subscription", uselist=False, backref="alert", lazy="joined")

    @property
    def initial_payment(self):
        """Proxy property for subscription.initial_payment (backwards compatibility)."""
        return self.subscription.initial_payment if self.subscription else False

    @property
    def payment_status(self):
        """Proxy property for subscription.payment_status (backwards compatibility)."""
        return self.subscription.payment_status if self.subscription else None

    @property
    def is_paused(self):
        """Check if the alert is currently paused."""
        return self.paused_at is not None

    @property
    def stripe_subscription_id(self):
        """Proxy property for subscription.stripe_subscription_id (backwards compatibility)."""
        return self.subscription.stripe_subscription_id if self.subscription else None

    @property
    def stripe_invoice_id(self):
        """Proxy property for subscription.stripe_invoice_id (backwards compatibility)."""
        return self.subscription.stripe_invoice_id if self.subscription else None

    @property
    def stripe_customer_id(self):
        """Proxy property for subscription.stripe_customer_id (backwards compatibility)."""
        return self.subscription.stripe_customer_id if self.subscription else None

    def get_status(self):
        """Calculate current alert status for display.

        Returns one of: 'active', 'paused', 'triggered', 'waiting'
        """
        # Check if explicitly paused
        if self.is_paused:
            return 'paused'

        # Check for payment failure
        if self.payment_status == 'payment_failed':
            return 'paused'

        # Check if waiting for payment/activation
        if not self.initial_payment or self.payment_status != 'active':
            return 'waiting'

        # Check for recent triggers (within 24 hours)
        if self.triggers:
            triggered_records = [t for t in self.triggers if t.alert_trigger_status == 1]
            if triggered_records:
                recent = max(triggered_records, key=lambda t: t.created_on or datetime.min)
                if recent.created_on:
                    hours_ago = (datetime.utcnow() - recent.created_on).total_seconds() / 3600
                    if hours_ago < 24:
                        return 'triggered'

        return 'active'


class Trigger(db.Model):
    __tablename__ = 'trigger'
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id'))
    alert_type = db.Column(db.String, nullable=False, unique=False)
    alert_trigger_status = db.Column(db.Integer, nullable=False, unique=False)
    alert_trigger_reason = db.Column(db.String, nullable=False, unique=False)
    alert_trigger_date = db.Column(
        db.DateTime, index=False, unique=False, nullable=True
    )
    triggered_rate = db.Column(db.Float, nullable=True, unique=False)

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)


class MortgageRate(db.Model):
    """Mortgage rate data model for tracking rates by zip code and term."""

    __tablename__ = 'mortgage_rate'
    id = db.Column(db.Integer, primary_key=True)
    zip_code = db.Column(db.String(5), nullable=False, unique=False, index=True)
    term_months = db.Column(db.Integer, nullable=False, unique=False, index=True)
    rate = db.Column(db.Float, nullable=False, unique=False)
    rate_date = db.Column(db.DateTime, nullable=False, unique=False, index=True)
    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    __table_args__ = (
        db.Index('ix_mortgage_rate_zip_term_date', 'zip_code', 'term_months', 'rate_date'),
    )

    def __repr__(self):
        return '<MortgageRate {}: {} for {}-month term on {}>'.format(
            self.zip_code, self.rate, self.term_months, self.rate_date
        )


class PasswordResetToken(db.Model):
    """Token for secure password reset."""

    __tablename__ = 'password_reset_token'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_on = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('reset_tokens', lazy='dynamic'))

    def __init__(self, user_id, expires_hours=1):
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.created_on = datetime.utcnow()
        self.expires_on = self.created_on + timedelta(hours=expires_hours)
        self.used = False

    def is_valid(self):
        """Check if token is still valid (not expired and not used)."""
        return not self.used and datetime.utcnow() < self.expires_on

    def mark_used(self):
        """Mark token as used."""
        self.used = True

    def __repr__(self):
        return '<PasswordResetToken {} for user {}>'.format(self.token[:8], self.user_id)


class UserPreference(db.Model):
    """User preferences for reports and notifications."""

    __tablename__ = 'user_preference'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    monthly_report_enabled = db.Column(db.Boolean, default=True, nullable=False)
    weekly_digest_enabled = db.Column(db.Boolean, default=False, nullable=False)
    theme = db.Column(db.String(20), default='light', nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('preferences', uselist=False, lazy='joined'))

    def __repr__(self):
        return '<UserPreference {} for user {}>'.format(self.id, self.user_id)


class EmailLog(db.Model):
    """Log of all emails sent by the system."""

    __tablename__ = 'email_log'
    id = db.Column(db.Integer, primary_key=True)
    email_type = db.Column(db.String(50), nullable=False, index=True)
    recipient_email = db.Column(db.String(255), nullable=False, index=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    subject = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    error_message = db.Column(db.Text, nullable=True)
    related_entity_type = db.Column(db.String(50), nullable=True)
    related_entity_id = db.Column(db.Integer, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('email_logs', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_email_log_type_status', 'email_type', 'status'),
        db.Index('ix_email_log_entity', 'related_entity_type', 'related_entity_id'),
    )

    def mark_sent(self):
        """Mark email as successfully sent."""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()

    def mark_failed(self, error_message):
        """Mark email as failed with error message."""
        self.status = 'failed'
        self.error_message = error_message

    def mark_delivered(self):
        """Mark email as delivered."""
        self.status = 'delivered'
        self.delivered_at = datetime.utcnow()

    def __repr__(self):
        return '<EmailLog {} to {} ({})>'.format(self.email_type, self.recipient_email, self.status)
