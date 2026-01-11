# Data Model Expansion Plan

**Version:** 1.0
**Date:** 2026-01-10
**Status:** Planning Phase

## Executive Summary

This document outlines a comprehensive plan for expanding the refi_alert data model to support enhanced functionality, better data integrity, improved user experience, and scalable architecture. The expansion includes 7 new models, modifications to 4 existing models, enhanced relationships, and a carefully sequenced migration strategy.

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [New Models to Add](#new-models-to-add)
3. [Existing Models to Modify](#existing-models-to-modify)
4. [Relationships & Constraints](#relationships--constraints)
5. [Index Optimization Strategy](#index-optimization-strategy)
6. [Migration Strategy](#migration-strategy)
7. [Testing Approach](#testing-approach)
8. [Rollback Plan](#rollback-plan)

---

## Current State Analysis

### Existing Models

1. **User** - User authentication and profile (11 fields)
2. **Mortgage** - Mortgage details and tracking (11 fields)
3. **Mortgage_Tracking** - Current mortgage values over time (6 fields)
4. **Alert** - Refinance alerts with payment integration (18 fields)
5. **Trigger** - Alert trigger events (8 fields)

### Identified Issues

1. **Trigger Model**: Duplicate `alert_trigger_date` field (lines 103-108 in models.py)
2. **Alert Model**: Mixing of business logic (alert settings) with payment/subscription logic (Stripe fields)
3. **No Email Tracking**: No record of emails sent to users (notifications, alerts)
4. **No Calculation History**: User calculations in calc.py are not persisted
5. **No Password Reset Flow**: Missing token-based password reset mechanism
6. **No Email Verification**: Users can register without email verification
7. **No User Preferences**: Settings are hardcoded, not user-customizable
8. **No Rate History**: Cannot track historical mortgage rates for trend analysis

### Current Relationships

```
User (1) -> (N) Mortgage
Mortgage (1) -> (N) Mortgage_Tracking
Mortgage (1) -> (N) Alert
User (1) -> (N) Alert
Alert (1) -> (N) Trigger
```

---

## New Models to Add

### 1. MortgageRate Model

**Purpose**: Track daily mortgage rate data from external sources (MortgageNewsDaily, etc.)

**Fields**:
```python
class MortgageRate(db.Model):
    __tablename__ = 'mortgage_rate'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    rate_type = db.Column(
        db.Enum('30_year_fixed', '15_year_fixed', 'FHA_30', 'VA_30', '5_1_ARM',
                '7_1_ARM', '10_1_ARM', name='rate_type_enum'),
        nullable=False,
        index=True
    )
    rate = db.Column(db.Numeric(5, 3), nullable=False)  # e.g., 6.875
    points = db.Column(db.Numeric(3, 2), nullable=True)  # e.g., 0.70
    apr = db.Column(db.Numeric(5, 3), nullable=True)
    change_from_previous = db.Column(db.Numeric(4, 3), nullable=True)  # Daily change
    source = db.Column(db.String(100), nullable=False, default='mortgagenewsdaily')

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Composite unique constraint: one rate per day per type
    __table_args__ = (
        db.UniqueConstraint('date', 'rate_type', name='uq_rate_date_type'),
        db.Index('idx_rate_date_type', 'date', 'rate_type'),
    )
```

**Rationale**:
- Enables historical rate tracking and trend analysis
- Supports automated alert triggering based on market conditions
- Provides data for visualization (rate history charts)
- Allows comparison of current mortgage rates against historical trends

---

### 2. EmailLog Model

**Purpose**: Track all emails sent to users for auditing, debugging, and preventing duplicates

**Fields**:
```python
class EmailLog(db.Model):
    __tablename__ = 'email_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True, index=True)
    recipient_email = db.Column(db.String(255), nullable=False, index=True)
    email_type = db.Column(
        db.Enum('welcome', 'alert_notification', 'password_reset', 'email_verification',
                'payment_receipt', 'payment_failed', 'rate_drop_alert',
                'weekly_digest', 'marketing', name='email_type_enum'),
        nullable=False,
        index=True
    )
    subject = db.Column(db.String(255), nullable=False)

    # Related entities
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id', ondelete='SET NULL'), nullable=True)
    trigger_id = db.Column(db.Integer, db.ForeignKey('trigger.id', ondelete='SET NULL'), nullable=True)

    # Status tracking
    status = db.Column(
        db.Enum('queued', 'sent', 'failed', 'bounced', 'opened', 'clicked', name='email_status_enum'),
        nullable=False,
        default='queued',
        index=True
    )
    sent_at = db.Column(db.DateTime, nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    # Email service provider tracking
    provider = db.Column(db.String(50), nullable=True)  # e.g., 'sendgrid', 'ses'
    provider_message_id = db.Column(db.String(255), nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), index=True)

    # Relationships
    user = db.relationship('User', backref='email_logs')
    alert = db.relationship('Alert', backref='email_logs')
    trigger = db.relationship('Trigger', backref='email_logs')
```

**Rationale**:
- Audit trail for compliance and debugging
- Prevents duplicate email sends
- Tracks engagement (opens, clicks)
- Helps identify deliverability issues

---

### 3. CalculationHistory Model

**Purpose**: Save user mortgage calculations for future reference and analysis

**Fields**:
```python
class CalculationHistory(db.Model):
    __tablename__ = 'calculation_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True, index=True)
    session_id = db.Column(db.String(100), nullable=True, index=True)  # For anonymous users
    mortgage_id = db.Column(db.Integer, db.ForeignKey('mortgage.id', ondelete='SET NULL'), nullable=True)

    # Calculation type
    calculation_type = db.Column(
        db.Enum('monthly_payment', 'break_even', 'efficient_frontier',
                'refinance_savings', 'amortization', name='calc_type_enum'),
        nullable=False,
        index=True
    )

    # Input parameters (JSON for flexibility)
    input_params = db.Column(db.JSON, nullable=False)
    # Example: {
    #   "principal": 300000,
    #   "rate": 0.065,
    #   "term": 360,
    #   "refi_cost": 5000
    # }

    # Calculation results (JSON for flexibility)
    output_results = db.Column(db.JSON, nullable=False)
    # Example: {
    #   "monthly_payment": 1896.20,
    #   "total_interest": 382632.00,
    #   "break_even_months": 38
    # }

    # Metadata
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), index=True)

    # Relationships
    user = db.relationship('User', backref='calculation_history')
    mortgage = db.relationship('Mortgage', backref='calculation_history')

    __table_args__ = (
        db.Index('idx_calc_user_created', 'user_id', 'created_at'),
    )
```

**Rationale**:
- Allows users to review past calculations
- Analytics on popular features
- Can suggest alerts based on calculation history
- Support for both logged-in and anonymous users

---

### 4. Subscription Model

**Purpose**: Properly separate subscription/payment logic from Alert logic

**Fields**:
```python
class Subscription(db.Model):
    __tablename__ = 'subscription'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id', ondelete='CASCADE'), nullable=False, index=True)

    # Stripe integration
    stripe_customer_id = db.Column(db.String(100), nullable=False, index=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    stripe_price_id = db.Column(db.String(100), nullable=False)

    # Subscription status
    status = db.Column(
        db.Enum('active', 'canceled', 'past_due', 'unpaid', 'incomplete',
                'incomplete_expired', 'trialing', name='subscription_status_enum'),
        nullable=False,
        default='incomplete',
        index=True
    )

    # Billing periods
    current_period_start = db.Column(db.Integer, nullable=True)  # Unix timestamp
    current_period_end = db.Column(db.Integer, nullable=True)    # Unix timestamp
    trial_start = db.Column(db.Integer, nullable=True)
    trial_end = db.Column(db.Integer, nullable=True)
    canceled_at = db.Column(db.Integer, nullable=True)
    ended_at = db.Column(db.Integer, nullable=True)

    # Pricing
    amount = db.Column(db.Integer, nullable=False)  # In cents
    currency = db.Column(db.String(3), nullable=False, default='usd')
    interval = db.Column(db.String(20), nullable=False, default='month')  # month, year

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    user = db.relationship('User', backref='subscriptions')
    alert = db.relationship('Alert', backref='subscription', uselist=False)
    invoices = db.relationship('Invoice', backref='subscription', cascade='all, delete-orphan')
```

**Rationale**:
- Clean separation of concerns (Alert = business logic, Subscription = payment)
- Easier to manage subscription lifecycle
- Better alignment with Stripe's data model
- Supports future payment providers

---

### 5. Invoice Model

**Purpose**: Track payment invoices separately from subscriptions

**Fields**:
```python
class Invoice(db.Model):
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

    status = db.Column(
        db.Enum('draft', 'open', 'paid', 'uncollectible', 'void', name='invoice_status_enum'),
        nullable=False,
        default='draft',
        index=True
    )

    # Timestamps
    invoice_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)

    # Invoice PDF
    invoice_pdf_url = db.Column(db.String(500), nullable=True)
    hosted_invoice_url = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    user = db.relationship('User', backref='invoices')
```

**Rationale**:
- Complete payment history tracking
- Easy invoice retrieval for users
- Support for refunds and disputes
- Financial reporting and reconciliation

---

### 6. UserPreference Model

**Purpose**: Store user-specific settings and preferences

**Fields**:
```python
class UserPreference(db.Model):
    __tablename__ = 'user_preference'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Notification preferences
    email_notifications = db.Column(db.Boolean, nullable=False, default=True)
    alert_frequency = db.Column(
        db.Enum('instant', 'daily', 'weekly', name='alert_frequency_enum'),
        nullable=False,
        default='instant'
    )
    marketing_emails = db.Column(db.Boolean, nullable=False, default=True)

    # Display preferences
    theme = db.Column(db.String(20), nullable=False, default='light')  # light, dark
    currency = db.Column(db.String(3), nullable=False, default='USD')
    date_format = db.Column(db.String(20), nullable=False, default='MM/DD/YYYY')

    # Alert preferences
    min_rate_drop_threshold = db.Column(db.Numeric(4, 3), nullable=False, default=0.125)  # 0.125% = 1/8 point
    auto_calculate_refi_cost = db.Column(db.Boolean, nullable=False, default=True)
    default_refi_term = db.Column(db.Integer, nullable=False, default=360)  # 30 years

    # Privacy
    share_anonymous_data = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    user = db.relationship('User', backref=db.backref('preferences', uselist=False))
```

**Rationale**:
- Personalized user experience
- Flexible notification settings
- Better user engagement
- Respects user privacy preferences

---

### 7. PasswordResetToken Model

**Purpose**: Secure password reset flow with time-limited tokens

**Fields**:
```python
class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)

    token = db.Column(db.String(100), nullable=False, unique=True, index=True)

    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used_at = db.Column(db.DateTime, nullable=True)

    # Security tracking
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    # Relationships
    user = db.relationship('User', backref='password_reset_tokens')

    @property
    def is_expired(self):
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None
```

**Rationale**:
- Secure password reset mechanism
- Time-limited tokens (typically 1 hour)
- One-time use tokens
- Security audit trail

---

### 8. EmailVerificationToken Model

**Purpose**: Email verification for new user registrations

**Fields**:
```python
class EmailVerificationToken(db.Model):
    __tablename__ = 'email_verification_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)

    token = db.Column(db.String(100), nullable=False, unique=True, index=True)

    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # Allow resending verification emails
    resent_count = db.Column(db.Integer, nullable=False, default=0)
    last_resent_at = db.Column(db.DateTime, nullable=True)

    # Security tracking
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    # Relationships
    user = db.relationship('User', backref='email_verification_tokens')

    @property
    def is_expired(self):
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def is_verified(self):
        return self.verified_at is not None
```

**Rationale**:
- Prevent fake email registrations
- Ensure valid contact information
- Reduce spam accounts
- Better email deliverability

---

## Existing Models to Modify

### 1. User Model Modifications

**Changes**:
```python
class User(UserMixin, db.Model):
    # ... existing fields ...

    # NEW FIELDS:
    email_verified = db.Column(db.Boolean, nullable=False, default=False, index=True)
    email_verified_at = db.Column(db.DateTime, nullable=True)

    phone_number = db.Column(db.String(20), nullable=True)  # Future: SMS alerts
    phone_verified = db.Column(db.Boolean, nullable=False, default=False)

    # Account status
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    deactivated_at = db.Column(db.DateTime, nullable=True)

    # Better audit fields
    last_login_ip = db.Column(db.String(45), nullable=True)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Soft delete support
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
```

**Rationale**:
- Email verification improves data quality
- Account locking prevents brute force attacks
- Soft delete preserves data integrity
- Phone number enables future SMS features

---

### 2. Mortgage Model Modifications

**Changes**:
```python
class Mortgage(db.Model):
    # ... existing fields ...

    # NEW FIELDS:

    # Better audit trail
    last_updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    # Property information (for better refinance estimates)
    estimated_property_value = db.Column(db.Float, nullable=True)
    property_type = db.Column(
        db.Enum('single_family', 'condo', 'townhouse', 'multi_family', name='property_type_enum'),
        nullable=True
    )
    occupancy_type = db.Column(
        db.Enum('primary', 'secondary', 'investment', name='occupancy_type_enum'),
        nullable=True,
        default='primary'
    )

    # Current loan details
    lender_name = db.Column(db.String(100), nullable=True)
    loan_number = db.Column(db.String(50), nullable=True)  # Encrypted in production

    # Metadata for better tracking
    last_rate_check_date = db.Column(db.DateTime, nullable=True)
```

**Rationale**:
- Property details improve refinance calculations
- Soft delete preserves historical data
- Audit trail for data changes
- Last rate check prevents redundant API calls

---

### 3. Alert Model Modifications

**Changes**:

**REMOVE** these Stripe-specific fields (move to Subscription model):
- `initial_payment`
- `payment_status`
- `initial_period_start`
- `initial_period_end`
- `period_start`
- `period_end`
- `price_id`
- `stripe_customer_id`
- `stripe_invoice_id`

**ADD** these fields:
```python
class Alert(db.Model):
    # ... existing core fields ...

    # NEW FIELDS:

    # Alert status
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    paused_at = db.Column(db.DateTime, nullable=True)

    # Notification tracking
    last_notification_sent_at = db.Column(db.DateTime, nullable=True)
    notification_count = db.Column(db.Integer, nullable=False, default=0)

    # Alert effectiveness
    first_triggered_at = db.Column(db.DateTime, nullable=True)
    last_triggered_at = db.Column(db.DateTime, nullable=True)
    total_triggers = db.Column(db.Integer, nullable=False, default=0)

    # User action tracking
    user_dismissed = db.Column(db.Boolean, nullable=False, default=False)
    dismissed_at = db.Column(db.DateTime, nullable=True)

    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
```

**Rationale**:
- Cleaner separation of concerns (Alert vs Subscription)
- Better alert lifecycle management
- Tracking for analytics and optimization
- User control (pause/dismiss alerts)

---

### 4. Trigger Model Modifications

**Changes**:

**FIX**: Remove duplicate `alert_trigger_date` field (exists on lines 103-108)

**CLARIFY** purpose and **ADD** fields:
```python
class Trigger(db.Model):
    # ... existing fields (after removing duplicate) ...

    # RENAME for clarity:
    # alert_trigger_status -> status (use Enum)
    # alert_trigger_reason -> reason
    # alert_trigger_date -> triggered_at (remove duplicate!)

    status = db.Column(
        db.Enum('triggered', 'notified', 'acknowledged', 'expired', name='trigger_status_enum'),
        nullable=False,
        default='triggered',
        index=True
    )
    reason = db.Column(db.Text, nullable=False)
    triggered_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), index=True)

    # NEW FIELDS:

    # Trigger details
    threshold_value = db.Column(db.Numeric(10, 2), nullable=True)  # The value that triggered
    current_value = db.Column(db.Numeric(10, 2), nullable=True)    # Current market value

    # Notification tracking
    notification_sent = db.Column(db.Boolean, nullable=False, default=False)
    notification_sent_at = db.Column(db.DateTime, nullable=True)

    # User interaction
    user_viewed = db.Column(db.Boolean, nullable=False, default=False)
    viewed_at = db.Column(db.DateTime, nullable=True)
    user_action = db.Column(
        db.Enum('none', 'contacted_lender', 'dismissed', 'snoozed', name='user_action_enum'),
        nullable=True
    )
    action_taken_at = db.Column(db.DateTime, nullable=True)

    # Expiration (triggers can expire if not acted upon)
    expires_at = db.Column(db.DateTime, nullable=True)
```

**Rationale**:
- Fix data model bug (duplicate field)
- Better trigger lifecycle tracking
- User interaction analytics
- Expiration prevents stale triggers

---

## Relationships & Constraints

### New Relationship Diagram

```
User
├── (1:N) Mortgage
├── (1:N) Alert
├── (1:N) Subscription
├── (1:N) Invoice
├── (1:N) EmailLog
├── (1:N) CalculationHistory
├── (1:N) PasswordResetToken
├── (1:N) EmailVerificationToken
└── (1:1) UserPreference

Mortgage
├── (1:N) Mortgage_Tracking
├── (1:N) Alert
└── (1:N) CalculationHistory

Alert
├── (1:N) Trigger
├── (1:N) EmailLog
└── (1:1) Subscription

Trigger
└── (1:N) EmailLog

Subscription
├── (1:N) Invoice
└── (belongs to) Alert

MortgageRate
└── (standalone, no foreign keys)
```

### Cascade Delete Strategies

| Parent → Child | Cascade Strategy | Rationale |
|----------------|------------------|-----------|
| User → Mortgage | CASCADE | User deletion should remove all mortgages |
| User → Alert | CASCADE | User deletion should remove all alerts |
| User → Subscription | CASCADE | No orphan subscriptions |
| User → UserPreference | CASCADE | Preferences tied to user |
| User → EmailLog | SET NULL | Keep email logs for audit, anonymize |
| User → CalculationHistory | CASCADE | Remove user-specific calculations |
| User → PasswordResetToken | CASCADE | No orphan tokens |
| User → EmailVerificationToken | CASCADE | No orphan tokens |
| Mortgage → Mortgage_Tracking | CASCADE | No tracking without mortgage |
| Mortgage → Alert | CASCADE | No alerts without mortgage |
| Mortgage → CalculationHistory | SET NULL | Keep calculations, remove reference |
| Alert → Trigger | CASCADE | No triggers without alert |
| Alert → Subscription | CASCADE | No subscription without alert |
| Alert → EmailLog | SET NULL | Keep email logs, remove reference |
| Subscription → Invoice | CASCADE | Remove all invoices with subscription |
| Trigger → EmailLog | SET NULL | Keep email logs, remove reference |

### Foreign Key Constraints

All foreign key relationships should include:
- `ondelete` action (as specified above)
- Index on foreign key column for query performance
- Optional `onupdate='CASCADE'` for primary key changes (rare but future-proof)

---

## Index Optimization Strategy

### Composite Indexes

```sql
-- User queries
CREATE INDEX idx_user_email_verified ON user(email_verified, is_active);
CREATE INDEX idx_user_deleted ON user(deleted_at) WHERE deleted_at IS NULL;

-- Mortgage queries
CREATE INDEX idx_mortgage_user_active ON mortgage(user_id, deleted_at);

-- Alert queries
CREATE INDEX idx_alert_user_active ON alert(user_id, is_active, deleted_at);
CREATE INDEX idx_alert_mortgage_active ON alert(mortgage_id, is_active);

-- Trigger queries
CREATE INDEX idx_trigger_alert_status ON trigger(alert_id, status, triggered_at DESC);
CREATE INDEX idx_trigger_expires ON trigger(expires_at) WHERE expires_at IS NOT NULL;

-- MortgageRate queries (critical for performance)
CREATE INDEX idx_rate_date_type ON mortgage_rate(date DESC, rate_type);
CREATE INDEX idx_rate_type_date ON mortgage_rate(rate_type, date DESC);

-- EmailLog queries
CREATE INDEX idx_email_user_created ON email_log(user_id, created_at DESC);
CREATE INDEX idx_email_type_status ON email_log(email_type, status, created_at DESC);
CREATE INDEX idx_email_status ON email_log(status) WHERE status IN ('failed', 'bounced');

-- CalculationHistory queries
CREATE INDEX idx_calc_user_created ON calculation_history(user_id, created_at DESC);
CREATE INDEX idx_calc_session ON calculation_history(session_id, created_at DESC);
CREATE INDEX idx_calc_type ON calculation_history(calculation_type, created_at DESC);

-- Subscription queries
CREATE INDEX idx_subscription_user_status ON subscription(user_id, status);
CREATE INDEX idx_subscription_stripe ON subscription(stripe_subscription_id);
CREATE INDEX idx_subscription_period ON subscription(current_period_end) WHERE status = 'active';

-- Invoice queries
CREATE INDEX idx_invoice_user_status ON invoice(user_id, status, invoice_date DESC);
CREATE INDEX idx_invoice_subscription ON invoice(subscription_id, invoice_date DESC);
```

### Partial Indexes

Partial indexes for common filtered queries:
- Active users: `WHERE deleted_at IS NULL`
- Active alerts: `WHERE is_active = TRUE AND deleted_at IS NULL`
- Failed emails: `WHERE status IN ('failed', 'bounced')`
- Expired triggers: `WHERE expires_at < NOW()`
- Active subscriptions: `WHERE status = 'active'`

---

## Migration Strategy

### Phase 1: Foundation Models (Week 1)

**Goal**: Add supporting models that don't affect existing functionality

**Migrations**:
1. **Migration 001**: Create `user_preference` table
   - Add table
   - Backfill preferences for existing users with defaults

2. **Migration 002**: Create `password_reset_token` table
   - Add table
   - No backfill needed

3. **Migration 003**: Create `email_verification_token` table
   - Add table
   - No backfill needed

**Testing**:
- Unit tests for new models
- Test token generation and validation
- Test preference CRUD operations

**Rollback Strategy**: Simple table drops (no data dependencies)

---

### Phase 2: User Model Updates (Week 1)

**Goal**: Enhance User model with new fields

**Migrations**:
4. **Migration 004**: Add new fields to `user` table
   - Add: `email_verified`, `email_verified_at`, `phone_number`, `phone_verified`
   - Add: `is_active`, `deactivated_at`, `last_login_ip`
   - Add: `failed_login_attempts`, `locked_until`, `deleted_at`
   - Backfill: Set `email_verified = True` for existing users
   - Backfill: Set `is_active = True` for all existing users

**Testing**:
- Test email verification flow
- Test account locking mechanism
- Test soft delete queries (`WHERE deleted_at IS NULL`)

**Rollback Strategy**:
- Drop new columns
- May need data migration if production changes occurred

---

### Phase 3: Mortgage & Alert Updates (Week 2)

**Goal**: Enhance core business models

**Migrations**:
5. **Migration 005**: Add new fields to `mortgage` table
   - Add: `last_updated_by`, `deleted_at`, `estimated_property_value`
   - Add: `property_type`, `occupancy_type`, `lender_name`, `loan_number`
   - Add: `last_rate_check_date`

6. **Migration 006**: Modify `alert` table
   - Add: `is_active`, `paused_at`, `last_notification_sent_at`
   - Add: `notification_count`, `first_triggered_at`, `last_triggered_at`
   - Add: `total_triggers`, `user_dismissed`, `dismissed_at`, `deleted_at`
   - **DO NOT DROP** Stripe fields yet (compatibility)

7. **Migration 007**: Fix and enhance `trigger` table
   - **CRITICAL**: Remove duplicate `alert_trigger_date` field
   - Rename: `alert_trigger_status` → `status` (requires data migration)
   - Rename: `alert_trigger_reason` → `reason`
   - Rename: `alert_trigger_date` → `triggered_at`
   - Add: `threshold_value`, `current_value`, `notification_sent`
   - Add: `notification_sent_at`, `user_viewed`, `viewed_at`
   - Add: `user_action`, `action_taken_at`, `expires_at`

**Data Migration for Trigger**:
```sql
-- Step 1: Add new columns
ALTER TABLE trigger ADD COLUMN status VARCHAR(20);
ALTER TABLE trigger ADD COLUMN reason TEXT;
ALTER TABLE trigger ADD COLUMN triggered_at TIMESTAMP;

-- Step 2: Migrate data
UPDATE trigger SET
    status = CASE alert_trigger_status
        WHEN 1 THEN 'triggered'
        WHEN 0 THEN 'expired'
        ELSE 'triggered'
    END,
    reason = alert_trigger_reason,
    triggered_at = alert_trigger_date;

-- Step 3: Drop old columns (after verification)
ALTER TABLE trigger DROP COLUMN alert_trigger_status;
ALTER TABLE trigger DROP COLUMN alert_trigger_reason;
-- Note: alert_trigger_date appears twice - remove BOTH

-- Step 4: Add NOT NULL constraints
ALTER TABLE trigger ALTER COLUMN status SET NOT NULL;
ALTER TABLE trigger ALTER COLUMN reason SET NOT NULL;
ALTER TABLE trigger ALTER COLUMN triggered_at SET NOT NULL;
```

**Testing**:
- Test soft deletes on Mortgage and Alert
- Test Trigger data migration thoroughly
- Test all existing queries still work

**Rollback Strategy**:
- Keep old Trigger columns until data migration verified
- Use Alembic downgrade with data rollback

---

### Phase 4: Email & Calculation Tracking (Week 2)

**Goal**: Add observability and analytics models

**Migrations**:
8. **Migration 008**: Create `email_log` table
   - Add table with all fields
   - Add indexes
   - No backfill (prospective logging only)

9. **Migration 009**: Create `calculation_history` table
   - Add table with all fields
   - Add indexes
   - No backfill (prospective tracking only)

**Testing**:
- Test email logging integration
- Test calculation history storage
- Test query performance with indexes

**Rollback Strategy**: Simple table drops

---

### Phase 5: Rate Tracking (Week 3)

**Goal**: Add mortgage rate tracking

**Migrations**:
10. **Migration 010**: Create `mortgage_rate` table
    - Add table with all fields
    - Add unique constraint on (date, rate_type)
    - Add composite indexes
    - Seed with current rates (optional)

**Testing**:
- Test rate ingestion
- Test duplicate prevention (unique constraint)
- Test query performance for date ranges

**Rollback Strategy**: Table drop (no dependencies yet)

---

### Phase 6: Payment Separation (Week 3-4)

**Goal**: Properly separate payment logic from alerts

**Migrations**:
11. **Migration 011**: Create `subscription` table
    - Add table with all fields
    - Add indexes
    - **DO NOT** migrate data yet

12. **Migration 012**: Create `invoice` table
    - Add table with all fields
    - Add indexes

13. **Migration 013**: Migrate Alert → Subscription data
    ```sql
    -- Migrate existing alerts with payment data to Subscription
    INSERT INTO subscription (
        user_id, alert_id, stripe_customer_id, stripe_subscription_id,
        stripe_price_id, status, current_period_start, current_period_end,
        amount, currency, interval, created_at
    )
    SELECT
        a.user_id,
        a.id,
        a.stripe_customer_id,
        a.stripe_invoice_id,  -- Note: may need cleanup
        a.price_id,
        CASE
            WHEN a.payment_status = 'Paid' THEN 'active'
            WHEN a.payment_status = 'incomplete' THEN 'incomplete'
            ELSE 'canceled'
        END,
        a.period_start,
        a.period_end,
        999,  -- $9.99 in cents (update to actual pricing)
        'usd',
        'month',
        a.created_at
    FROM alert a
    WHERE a.stripe_customer_id IS NOT NULL;
    ```

14. **Migration 014**: Drop Stripe fields from `alert` table
    - **ONLY AFTER** data migration verified
    - Drop: `initial_payment`, `payment_status`
    - Drop: `initial_period_start`, `initial_period_end`
    - Drop: `period_start`, `period_end`
    - Drop: `price_id`, `stripe_customer_id`, `stripe_invoice_id`

**Testing**:
- Critical: Test data migration accuracy
- Test Stripe webhook integration with new models
- Test existing payment flows
- Test subscription lifecycle

**Rollback Strategy**:
- Keep backup of Alert table before dropping columns
- Multi-step rollback:
  1. Restore Alert columns
  2. Migrate data back from Subscription
  3. Drop Subscription/Invoice tables

---

### Migration Execution Order

```
Week 1:
├── Migration 001: user_preference
├── Migration 002: password_reset_token
├── Migration 003: email_verification_token
└── Migration 004: Update user table

Week 2:
├── Migration 005: Update mortgage table
├── Migration 006: Update alert table (add fields)
├── Migration 007: Fix & update trigger table (CRITICAL)
├── Migration 008: email_log table
└── Migration 009: calculation_history table

Week 3:
├── Migration 010: mortgage_rate table
├── Migration 011: subscription table
└── Migration 012: invoice table

Week 4:
├── Migration 013: Migrate alert → subscription data
├── Migration 014: Drop stripe fields from alert
└── Final testing & verification
```

---

## Testing Approach

### Unit Tests

For each new model, create tests for:
1. Model creation and field validation
2. Relationships and foreign keys
3. Custom methods and properties
4. Enum constraints
5. Unique constraints

Example test structure:
```python
# tests/unit/models/test_mortgage_rate.py
def test_mortgage_rate_creation():
    """Test creating a MortgageRate record"""

def test_mortgage_rate_unique_constraint():
    """Test that duplicate date+type raises IntegrityError"""

def test_mortgage_rate_change_calculation():
    """Test change_from_previous calculation"""
```

### Integration Tests

1. **Relationship Tests**: Test cascading deletes
2. **Query Performance Tests**: Test index effectiveness
3. **Migration Tests**: Test each migration up/down

### Data Migration Tests

Critical for Phase 6 (Alert → Subscription):
1. Count verification: `SELECT COUNT(*) FROM alert WHERE stripe_customer_id IS NOT NULL` should equal `SELECT COUNT(*) FROM subscription`
2. Sample data verification: Manually verify 10-20 records
3. Foreign key integrity: All subscription.alert_id must reference valid alerts
4. No data loss: All Stripe IDs accounted for

### End-to-End Tests

1. User registration with email verification
2. Password reset flow
3. Alert creation with subscription
4. Stripe webhook processing (use Stripe test mode)
5. Email logging and tracking
6. Rate tracking and alert triggering

---

## Rollback Plan

### Quick Rollback (Production Emergency)

If critical issues arise in production:

1. **Stop Application**: `heroku ps:scale web=0` (or equivalent)
2. **Database Rollback**: `alembic downgrade -1` (one migration back)
3. **Deploy Previous Code**: `git revert HEAD && git push heroku master`
4. **Restart Application**: `heroku ps:scale web=1`
5. **Monitor Logs**: Check for errors

### Partial Rollback (Specific Migration)

```bash
# Rollback to specific revision
alembic downgrade <revision_id>

# Example: Rollback trigger changes
alembic downgrade 9ab95efade3e
```

### Data Recovery

If data loss occurs:
1. Restore from backup (maintain hourly backups during migration period)
2. Replay missed transactions from application logs
3. Re-run data migration with corrections

### Rollback Testing

Before production:
1. Test each migration's `downgrade()` function in staging
2. Verify data integrity after downgrade
3. Document rollback time for each migration
4. Practice full rollback scenario

---

## Success Criteria

### Phase Completion Checklist

- [ ] All migrations run successfully in dev/staging/production
- [ ] No data loss (verify record counts)
- [ ] All existing features continue working
- [ ] New features accessible and tested
- [ ] Performance metrics within acceptable range
- [ ] All tests passing (unit, integration, e2e)
- [ ] Documentation updated

### Performance Targets

- [ ] Database query time < 100ms for 95th percentile
- [ ] Migration execution time < 5 minutes per migration
- [ ] Zero downtime deployments (except final Stripe migration)
- [ ] Email log queries performant with 1M+ records

### Data Integrity

- [ ] Foreign key constraints enforced
- [ ] No orphaned records
- [ ] Cascade deletes working correctly
- [ ] Unique constraints preventing duplicates

---

## Timeline Summary

| Phase | Duration | Complexity | Risk Level |
|-------|----------|------------|------------|
| Phase 1: Foundation Models | 3 days | Low | Low |
| Phase 2: User Updates | 2 days | Low | Low |
| Phase 3: Mortgage/Alert/Trigger | 5 days | Medium | Medium |
| Phase 4: Email & Calculations | 3 days | Low | Low |
| Phase 5: Rate Tracking | 3 days | Low | Low |
| Phase 6: Payment Separation | 7 days | High | High |
| **Total** | **23 days** (~4.5 weeks) | | |

---

## Dependencies

### External Dependencies

- Alembic for migrations
- PostgreSQL 12+ (for JSON support)
- Stripe API integration (existing)
- Email service provider (SendGrid/SES)

### Internal Dependencies

- `refi_monitor/models.py` - All model definitions
- `refi_monitor/mortgage.py` - Stripe webhook handlers
- `refi_monitor/routes.py` - Alert/subscription logic
- `migrations/` - Alembic migration files

### Blocking Dependencies

Migration 013 (Alert → Subscription data migration) blocks Migration 014 (dropping Alert fields).

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during migration | Medium | Critical | Backups, staging testing, phased rollout |
| Stripe webhook failures | Medium | High | Keep old Alert fields until verified |
| Performance degradation | Low | Medium | Index optimization, query testing |
| User experience disruption | Low | High | Feature flags, gradual rollout |
| Schema conflicts | Low | Medium | Lock schema during migration |

---

## Post-Migration Tasks

1. **Monitoring**:
   - Set up alerts for failed migrations
   - Monitor database performance metrics
   - Track error rates in logs

2. **Cleanup**:
   - Remove deprecated code handling old Alert payment fields
   - Archive old migration backups (after 30 days)
   - Update API documentation

3. **Optimization**:
   - Analyze slow queries
   - Add additional indexes if needed
   - Consider partitioning for large tables (EmailLog, CalculationHistory)

4. **Documentation**:
   - Update ERD diagrams
   - Document new API endpoints
   - Create developer migration guide

---

## Appendix A: ERD Diagram

```
┌─────────────────┐
│      User       │
│─────────────────│
│ id (PK)         │◄─────┐
│ email (UQ)      │      │
│ email_verified  │      │
│ is_active       │      │
│ deleted_at      │      │
└─────────────────┘      │
         │               │
         │ 1:1           │
         ▼               │
┌─────────────────┐      │
│ UserPreference  │      │
│─────────────────│      │
│ id (PK)         │      │
│ user_id (FK UQ) │      │
│ email_notif...  │      │
└─────────────────┘      │
                         │
         │               │
         │ 1:N           │
         ▼               │
┌─────────────────┐      │
│    Mortgage     │      │
│─────────────────│      │
│ id (PK)         │◄──┐  │
│ user_id (FK)    │───┘  │
│ deleted_at      │      │
└─────────────────┘      │
         │               │
         │ 1:N           │
         ▼               │
┌─────────────────┐      │
│      Alert      │      │
│─────────────────│      │
│ id (PK)         │◄──┐  │
│ user_id (FK)    │───┼──┘
│ mortgage_id(FK) │───┘
│ is_active       │
│ deleted_at      │
└─────────────────┘
         │
         │ 1:1
         ▼
┌─────────────────┐
│  Subscription   │
│─────────────────│
│ id (PK)         │
│ alert_id (FK)   │
│ stripe_sub_id   │
│ status          │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│    Invoice      │
│─────────────────│
│ id (PK)         │
│ subscription_id │
│ stripe_inv_id   │
│ amount_paid     │
└─────────────────┘
```

---

## Appendix B: Migration Checklist Template

Use this checklist for each migration:

```markdown
## Migration XXX: [Name]

### Pre-Migration
- [ ] Migration script written
- [ ] Downgrade function implemented
- [ ] Unit tests written and passing
- [ ] Tested in local environment
- [ ] Tested in staging environment
- [ ] Database backup created
- [ ] Rollback plan documented

### Execution
- [ ] Application stopped (if required)
- [ ] Migration executed
- [ ] Migration logged
- [ ] No errors in migration log

### Post-Migration
- [ ] Data integrity verified
- [ ] Application started
- [ ] Smoke tests passed
- [ ] Monitoring checked (5 min, 1 hr, 24 hr)
- [ ] No increase in error rate
- [ ] Performance metrics acceptable

### Sign-off
- Developer: _____________ Date: _______
- Reviewer: _____________ Date: _______
```

---

## Conclusion

This data model expansion plan provides a comprehensive roadmap for scaling the refi_alert application. The phased approach minimizes risk while delivering incremental value. Critical migrations (especially Phase 6) require careful execution and testing.

**Estimated Total Effort**: 4-5 weeks (1 developer)

**Recommended Approach**: Execute Phases 1-5 first, validate thoroughly, then proceed with Phase 6 (payment separation) after all other changes are stable.

