from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


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
    mortgages = db.relationship("Mortgage")

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

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


class Subscription(db.Model):
    """Subscription model for separating payment logic from Alert."""

    __tablename__ = 'subscription'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id', ondelete='CASCADE'), nullable=False, index=True)

    # Stripe integration
    stripe_customer_id = db.Column(db.String(100), nullable=False, index=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    stripe_price_id = db.Column(db.String(100), nullable=False)

    # Subscription status
    status = db.Column(db.String(50), nullable=False, default='incomplete', index=True)

    # Billing periods (Unix timestamps)
    current_period_start = db.Column(db.Integer, nullable=True)
    current_period_end = db.Column(db.Integer, nullable=True)
    trial_start = db.Column(db.Integer, nullable=True)
    trial_end = db.Column(db.Integer, nullable=True)
    canceled_at = db.Column(db.Integer, nullable=True)
    ended_at = db.Column(db.Integer, nullable=True)

    # Pricing
    amount = db.Column(db.Integer, nullable=False)  # In cents
    currency = db.Column(db.String(3), nullable=False, default='usd')
    interval = db.Column(db.String(20), nullable=False, default='month')

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    # Relationships
    user = db.relationship('User', backref='subscriptions')
    alert = db.relationship('Alert', backref=db.backref('subscription', uselist=False))
    invoices = db.relationship('Invoice', backref='subscription', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Subscription {} for Alert {}>'.format(self.id, self.alert_id)


class Invoice(db.Model):
    """Invoice model for tracking payment invoices."""

    __tablename__ = 'invoice'
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)

    # Stripe details
    stripe_invoice_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    stripe_payment_intent_id = db.Column(db.String(100), nullable=True)

    # Invoice details
    amount_due = db.Column(db.Integer, nullable=False)  # In cents
    amount_paid = db.Column(db.Integer, nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default='usd')

    # Status
    status = db.Column(db.String(50), nullable=False, default='draft', index=True)

    # Timestamps
    invoice_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)

    # Invoice URLs
    invoice_pdf_url = db.Column(db.String(500), nullable=True)
    hosted_invoice_url = db.Column(db.String(500), nullable=True)

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    # Relationships
    user = db.relationship('User', backref='invoices')

    def __repr__(self):
        return '<Invoice {} for Subscription {}>'.format(self.stripe_invoice_id, self.subscription_id)
