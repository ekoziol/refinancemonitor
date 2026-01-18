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
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)
    mortgages = db.relationship("Mortgage")

    # Token expiry duration (24 hours)
    VERIFICATION_TOKEN_EXPIRY_HOURS = 24

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def generate_verification_token(self):
        """Generate a secure email verification token."""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = datetime.utcnow()
        return self.email_verification_token

    def is_verification_token_valid(self):
        """Check if the verification token is still valid (not expired)."""
        if not self.email_verification_sent_at:
            return False
        expiry_time = self.email_verification_sent_at + timedelta(
            hours=self.VERIFICATION_TOKEN_EXPIRY_HOURS
        )
        return datetime.utcnow() < expiry_time

    def verify_email(self):
        """Mark email as verified and clear the token."""
        self.email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None

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

    initial_payment = db.Column(db.Boolean, index=False, unique=False, nullable=True)
    payment_status = db.Column(db.String, index=False, unique=False, nullable=True)
    initial_period_start = db.Column(
        db.Integer, index=False, unique=False, nullable=True
    )
    initial_period_end = db.Column(db.Integer, index=False, unique=False, nullable=True)
    period_start = db.Column(db.Integer, index=False, unique=False, nullable=True)
    period_end = db.Column(db.Integer, index=False, unique=False, nullable=True)
    price_id = db.Column(db.String, index=False, unique=False, nullable=True)
    stripe_customer_id = db.Column(db.String, index=False, unique=False, nullable=True)
    stripe_invoice_id = db.Column(db.String, index=False, unique=False, nullable=True)
    triggers = db.relationship("Trigger")


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
