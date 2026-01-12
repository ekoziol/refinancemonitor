# Data Model Gap Analysis

**Version:** 1.0
**Date:** 2026-01-11
**Status:** Analysis Complete
**Related:** DATA_MODEL_EXPANSION_PLAN.md

## Executive Summary

This document identifies data structure gaps between the current implementation and intended functionality across five key feature areas. Analysis reveals **12 critical gaps** requiring new models and **8 enhancement gaps** requiring modifications to existing models.

---

## Current State Summary

### Existing Models

| Model | Fields | Purpose | Status |
|-------|--------|---------|--------|
| User | 11 | Authentication & profile | Needs enhancement |
| Mortgage | 11 | Mortgage details | Adequate |
| Mortgage_Tracking | 6 | Point-in-time tracking | Adequate |
| Alert | 18 | Alerts + payment (mixed) | Needs separation |
| Trigger | 8 | Alert trigger events | Has duplicate field |
| MortgageRate | 10 | Rate tracking (enum-based) | Exists |
| DailyMortgageRate | 10 | Rate tracking (string-based) | Duplicate - consolidate |

---

## Gap Analysis by Feature Area

### 1. Rate Monitoring Service (Phase 5)

**Intended Functionality:**
- Fetch and store daily mortgage rates from external sources
- Track rate history for trend analysis
- Schedule automated rate checks
- Support multiple rate types (30yr, 15yr, FHA, VA, ARM)

**Current State:**
- `MortgageRate` model exists with enum-based rate types
- `DailyMortgageRate` model exists with string-based rate types
- `scheduler.py` implements rate update scheduling via APScheduler
- `rate_updater.py` fetches rates from MortgageNewsDaily

**Gaps Identified:**

| Gap | Priority | Description | Recommendation |
|-----|----------|-------------|----------------|
| **Duplicate Rate Models** | P0 | Two nearly identical models exist (`MortgageRate`, `DailyMortgageRate`). Creates confusion and data fragmentation. | Consolidate to single model. Prefer `MortgageRate` (uses Enum for type safety) |
| **No Rate Source Tracking** | P2 | Both models have `source` field, but no dedicated table for rate sources. Cannot track source reliability or configure multiple sources. | Add `RateSource` model for multi-source support (future) |
| **No Rate Check Scheduling Data** | P1 | Scheduler config is hardcoded in `scheduler.py`. No database record of scheduled checks or their outcomes. | Add `RateCheckLog` model to track fetch attempts, success/failure, and timing |
| **No Rate Alert Thresholds** | P2 | No configurable thresholds for significant rate changes. Hardcoded in evaluation logic. | Consider adding to `UserPreference` model |

**Current vs Required:**

```
CURRENT:
MortgageRate ──┐
               ├── Duplicate, no source management
DailyMortgageRate ──┘

REQUIRED:
MortgageRate (consolidated)
├── rate_type (Enum)
├── source (FK to RateSource, optional)
├── fetch_timestamp (when fetched, not just date)
└── quality_score (data quality indicator, optional)

RateSource (NEW - future)
├── name
├── api_endpoint
├── is_active
├── reliability_score
└── last_successful_fetch

RateCheckLog (NEW)
├── check_timestamp
├── source
├── success (bool)
├── rates_updated (count)
├── error_message (nullable)
└── duration_ms
```

---

### 2. Email Notification System (Phase 5)

**Intended Functionality:**
- Send alert notifications when refinancing conditions are met
- Send payment confirmations
- Track email delivery status
- Support email templates
- Handle unsubscribes
- Prevent duplicate emails

**Current State:**
- `notifications.py` sends emails via Flask-Mail
- Emails are sent for: alert triggers, payment confirmations
- No tracking of emails sent
- Templates are inline in code (not configurable)

**Gaps Identified:**

| Gap | Priority | Description | Recommendation |
|-----|----------|-------------|----------------|
| **No Email Log/History** | P0 | Emails are sent but not tracked. Cannot audit, debug, or prevent duplicates. | Add `EmailLog` model (per expansion plan) |
| **No Email Template Tracking** | P2 | Templates are hardcoded in Python. Cannot edit without deployment. | Add `EmailTemplate` model for dynamic templates |
| **No Delivery Status Tracking** | P1 | No webhook integration with email provider to track bounces, opens, clicks. | Add status tracking to `EmailLog` with provider webhook support |
| **No Unsubscribe Tracking** | P1 | No mechanism for users to unsubscribe from specific email types. | Add to `UserPreference` model with per-type toggles |
| **No Email Queue** | P2 | Emails sent synchronously. Can cause request timeouts. | Consider background job queue (separate infrastructure concern) |

**Current vs Required:**

```
CURRENT:
notifications.py → Flask-Mail → SMTP → (no tracking)

REQUIRED:
EmailLog (NEW)
├── id
├── user_id (FK, nullable for anonymized)
├── recipient_email
├── email_type (Enum: welcome, alert_notification, password_reset, etc.)
├── subject
├── alert_id (FK, nullable)
├── trigger_id (FK, nullable)
├── status (Enum: queued, sent, failed, bounced, opened, clicked)
├── sent_at
├── opened_at (nullable)
├── clicked_at (nullable)
├── error_message (nullable)
├── provider (sendgrid, ses, etc.)
├── provider_message_id
└── created_at

EmailTemplate (NEW - optional)
├── id
├── name (unique)
├── email_type (Enum)
├── subject_template
├── body_html_template
├── body_text_template
├── is_active
├── version
└── created_at, updated_at

UserPreference (NEW - email section)
├── email_notifications (bool)
├── alert_frequency (Enum: instant, daily, weekly)
├── marketing_emails (bool)
└── (per-type unsubscribes as needed)
```

---

### 3. Stripe Payment System

**Intended Functionality:**
- Process subscription payments for alerts
- Track subscription lifecycle (active, canceled, past_due, etc.)
- Store invoice history
- Handle payment method updates
- Support multiple subscription plans

**Current State:**
- Stripe integration via `mortgage.py`
- Payment fields embedded directly in `Alert` model
- Webhook handles: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`
- No dedicated subscription or invoice models

**Gaps Identified:**

| Gap | Priority | Description | Recommendation |
|-----|----------|-------------|----------------|
| **Mixed Concerns in Alert Model** | P0 | Alert model has 9 Stripe-related fields mixed with business logic. Violates separation of concerns. | Extract to dedicated `Subscription` model |
| **No Separate Invoice Tracking** | P1 | Invoices are not stored locally. Cannot show payment history without Stripe API calls. | Add `Invoice` model |
| **No Payment Method Storage** | P2 | Payment methods stored only in Stripe. Cannot display masked card info locally. | Add `PaymentMethod` model (store Stripe IDs, last4, expiry only) |
| **No Subscription Plan Tracking** | P2 | Single hardcoded price ID. Cannot support multiple plans or pricing tiers. | Add `SubscriptionPlan` model |
| **Inconsistent payment_status Values** | P1 | Uses strings like 'active', 'Paid', 'incomplete', 'payment_failed'. No enum validation. | Standardize with Enum in new Subscription model |
| **Missing Webhook Events** | P1 | Only handles 3 webhook events. Missing: `customer.subscription.updated`, `customer.subscription.deleted`, `payment_method.attached` | Expand webhook handler with new models |

**Current vs Required:**

```
CURRENT:
Alert model contains:
├── initial_payment (Boolean)
├── payment_status (String - inconsistent values)
├── initial_period_start (Integer - Unix timestamp)
├── initial_period_end (Integer)
├── period_start (Integer)
├── period_end (Integer)
├── price_id (String)
├── stripe_customer_id (String)
└── stripe_invoice_id (String)

REQUIRED:
Subscription (NEW)
├── id
├── user_id (FK)
├── alert_id (FK)
├── stripe_customer_id
├── stripe_subscription_id (unique)
├── stripe_price_id
├── status (Enum: active, canceled, past_due, unpaid, incomplete, trialing)
├── current_period_start (Integer - Unix timestamp)
├── current_period_end (Integer)
├── trial_start (nullable)
├── trial_end (nullable)
├── canceled_at (nullable)
├── ended_at (nullable)
├── amount (Integer - cents)
├── currency (String)
├── interval (String: month, year)
└── created_at, updated_at

Invoice (NEW)
├── id
├── subscription_id (FK)
├── user_id (FK)
├── stripe_invoice_id (unique)
├── stripe_payment_intent_id (nullable)
├── amount_due (Integer - cents)
├── amount_paid (Integer)
├── currency (String)
├── status (Enum: draft, open, paid, uncollectible, void)
├── invoice_date
├── due_date (nullable)
├── paid_at (nullable)
├── invoice_pdf_url (nullable)
├── hosted_invoice_url (nullable)
└── created_at, updated_at

Alert model (MODIFIED):
├── REMOVE all Stripe fields
├── ADD is_active (Boolean)
├── ADD paused_at (DateTime, nullable)
└── Relationship to Subscription (1:1)
```

---

### 4. Calculator Results

**Intended Functionality:**
- Calculate monthly payments, break-even points, efficient frontier
- Save calculation history for logged-in users
- Support anonymous calculations (session-based)
- Share calculations (generate shareable links)
- Compare multiple scenarios

**Current State:**
- `calc.py` has calculation functions (monthly payment, break-even, amortization, efficient frontier)
- `refi_calculator_dash.py` provides Dash UI for calculations
- No persistence of calculations
- No sharing mechanism

**Gaps Identified:**

| Gap | Priority | Description | Recommendation |
|-----|----------|-------------|----------------|
| **No Calculation History Storage** | P1 | All calculations are ephemeral. Users cannot review past calculations. | Add `CalculationHistory` model |
| **No Shared Calculation Support** | P2 | Cannot generate shareable links for calculations. | Add `SharedCalculation` model with UUID-based access |
| **No Comparison Tracking** | P3 | Cannot save and compare multiple scenarios side-by-side. | Add `CalculationComparison` model linking multiple calculations |
| **No Anonymous User Tracking** | P2 | Cannot associate calculations with session for unauthenticated users. | Add session_id field to `CalculationHistory` |

**Current vs Required:**

```
CURRENT:
calc.py functions → Dash UI → (no storage)

REQUIRED:
CalculationHistory (NEW)
├── id
├── user_id (FK, nullable - for logged-in users)
├── session_id (String, nullable - for anonymous users)
├── mortgage_id (FK, nullable - if linked to saved mortgage)
├── calculation_type (Enum: monthly_payment, break_even, efficient_frontier, refinance_savings, amortization)
├── input_params (JSON)
│   └── Example: {"principal": 300000, "rate": 0.065, "term": 360, "refi_cost": 5000}
├── output_results (JSON)
│   └── Example: {"monthly_payment": 1896.20, "total_interest": 382632.00, "break_even_months": 38}
├── ip_address (String, nullable - for analytics)
├── user_agent (String, nullable)
└── created_at

SharedCalculation (NEW - optional)
├── id
├── calculation_id (FK to CalculationHistory)
├── share_token (UUID, unique, indexed)
├── expires_at (nullable)
├── view_count
└── created_at

CalculationComparison (NEW - optional, future)
├── id
├── user_id (FK, nullable)
├── name (String)
├── calculation_ids (JSON array of CalculationHistory IDs)
├── notes (Text, nullable)
└── created_at
```

---

### 5. User Management

**Intended Functionality:**
- User registration and authentication
- Email verification for new accounts
- Password reset via email token
- User preferences and settings
- Session management and security
- Account deactivation/deletion

**Current State:**
- `User` model with basic fields (name, email, password hash)
- `auth.py` handles login/signup with Flask-Login
- Password hashing with werkzeug (SHA256)
- No email verification
- No password reset
- No preferences

**Gaps Identified:**

| Gap | Priority | Description | Recommendation |
|-----|----------|-------------|----------------|
| **No Email Verification** | P0 | Users can register with any email. No validation of email ownership. | Add `EmailVerificationToken` model + User.email_verified field |
| **No Password Reset Tokens** | P0 | No "Forgot Password" flow. Users with forgotten passwords are locked out. | Add `PasswordResetToken` model |
| **No User Preferences** | P1 | All settings hardcoded. Cannot customize notifications, display, thresholds. | Add `UserPreference` model (1:1 with User) |
| **No Session Management** | P2 | No tracking of active sessions. Cannot revoke sessions or show login history. | Add `UserSession` model |
| **No Account Security Tracking** | P1 | No failed login tracking, no account locking, no login history. | Add security fields to User model |
| **Weak Password Hashing** | P1 | Uses SHA256 via werkzeug. Should use bcrypt or argon2. | Update password hashing (code change, not model) |
| **No Soft Delete** | P2 | User deletion is permanent. Cannot recover or maintain referential integrity. | Add `deleted_at` field to User |

**Current vs Required:**

```
CURRENT:
User model:
├── id
├── name
├── email (unique)
├── password (SHA256 hash)
├── credit_score
├── created_on
├── updated_on
├── last_login
├── last_paid_date
├── paid
└── mortgages (relationship)

REQUIRED:
User model (MODIFIED):
├── (existing fields)
├── email_verified (Boolean, default False)
├── email_verified_at (DateTime, nullable)
├── phone_number (String, nullable - future SMS)
├── phone_verified (Boolean, default False)
├── is_active (Boolean, default True)
├── deactivated_at (DateTime, nullable)
├── last_login_ip (String, nullable)
├── failed_login_attempts (Integer, default 0)
├── locked_until (DateTime, nullable)
└── deleted_at (DateTime, nullable - soft delete)

PasswordResetToken (NEW)
├── id
├── user_id (FK)
├── token (String, unique, indexed)
├── expires_at (DateTime)
├── used_at (DateTime, nullable)
├── ip_address (String, nullable)
├── user_agent (String, nullable)
└── created_at

EmailVerificationToken (NEW)
├── id
├── user_id (FK)
├── token (String, unique, indexed)
├── expires_at (DateTime)
├── verified_at (DateTime, nullable)
├── resent_count (Integer, default 0)
├── last_resent_at (DateTime, nullable)
├── ip_address (String, nullable)
├── user_agent (String, nullable)
└── created_at

UserPreference (NEW)
├── id
├── user_id (FK, unique)
├── email_notifications (Boolean, default True)
├── alert_frequency (Enum: instant, daily, weekly)
├── marketing_emails (Boolean, default True)
├── theme (String: light, dark)
├── currency (String, default USD)
├── date_format (String)
├── min_rate_drop_threshold (Decimal)
├── auto_calculate_refi_cost (Boolean)
├── default_refi_term (Integer)
├── share_anonymous_data (Boolean)
└── created_at, updated_at

UserSession (NEW - optional)
├── id
├── user_id (FK)
├── session_token (String, unique)
├── ip_address
├── user_agent
├── expires_at
├── revoked_at (nullable)
└── created_at
```

---

## Gap Summary Matrix

| Feature Area | Critical (P0) | High (P1) | Medium (P2) | Low (P3) | Total |
|--------------|---------------|-----------|-------------|----------|-------|
| Rate Monitoring | 1 | 1 | 2 | 0 | 4 |
| Email System | 1 | 2 | 2 | 0 | 5 |
| Stripe Payments | 1 | 3 | 2 | 0 | 6 |
| Calculator | 0 | 1 | 2 | 1 | 4 |
| User Management | 2 | 2 | 2 | 0 | 6 |
| **TOTAL** | **5** | **9** | **10** | **1** | **25** |

---

## New Models Required

| Model | Priority | Purpose | Complexity |
|-------|----------|---------|------------|
| Subscription | P0 | Separate payment logic from Alert | Medium |
| Invoice | P1 | Track payment history | Low |
| EmailLog | P0 | Track all sent emails | Low |
| CalculationHistory | P1 | Save user calculations | Low |
| PasswordResetToken | P0 | Secure password reset | Low |
| EmailVerificationToken | P0 | Verify user emails | Low |
| UserPreference | P1 | User settings | Low |
| RateCheckLog | P1 | Track rate fetch operations | Low |
| SharedCalculation | P2 | Shareable calculation links | Low |
| EmailTemplate | P2 | Dynamic email templates | Medium |
| UserSession | P2 | Session management | Low |
| PaymentMethod | P2 | Store card info | Low |
| SubscriptionPlan | P2 | Multiple pricing tiers | Low |
| RateSource | P2 | Multiple rate providers | Low |

---

## Existing Model Modifications

| Model | Changes | Priority |
|-------|---------|----------|
| User | Add 11 new fields (email verification, security, soft delete) | P0 |
| Alert | Remove 9 Stripe fields, add 4 lifecycle fields | P0 |
| Trigger | Remove duplicate field, rename 3 fields, add 8 new fields | P0 |
| DailyMortgageRate | DELETE - consolidate with MortgageRate | P1 |

---

## Recommendations

### Immediate Actions (P0)
1. **Create Subscription model** - Extract Stripe fields from Alert
2. **Create EmailLog model** - Track all email sends
3. **Create PasswordResetToken model** - Enable password reset flow
4. **Create EmailVerificationToken model** - Validate user emails
5. **Modify User model** - Add email_verified, security fields

### Short-term Actions (P1)
1. **Create Invoice model** - Local payment history
2. **Create UserPreference model** - User settings
3. **Create CalculationHistory model** - Save calculations
4. **Create RateCheckLog model** - Track rate fetches
5. **Fix Trigger model** - Remove duplicate field, standardize naming
6. **Consolidate rate models** - Remove DailyMortgageRate

### Medium-term Actions (P2)
1. **Create SharedCalculation model** - Shareable links
2. **Create UserSession model** - Session management
3. **Create EmailTemplate model** - Dynamic templates
4. **Create PaymentMethod model** - Card display
5. **Create SubscriptionPlan model** - Pricing tiers

---

## Alignment with Expansion Plan

This gap analysis validates and extends the recommendations in `DATA_MODEL_EXPANSION_PLAN.md`:

| Expansion Plan Model | Gap Analysis Status |
|---------------------|---------------------|
| MortgageRate | **Exists** - needs consolidation with DailyMortgageRate |
| EmailLog | **Confirmed** - critical gap |
| CalculationHistory | **Confirmed** - high priority gap |
| Subscription | **Confirmed** - critical gap |
| Invoice | **Confirmed** - high priority gap |
| UserPreference | **Confirmed** - high priority gap |
| PasswordResetToken | **Confirmed** - critical gap |
| EmailVerificationToken | **Confirmed** - critical gap |

**Additional gaps identified not in expansion plan:**
- RateCheckLog (rate monitoring observability)
- SharedCalculation (calculation sharing)
- UserSession (security)
- EmailTemplate (notification flexibility)
- PaymentMethod (payment UX)
- SubscriptionPlan (pricing flexibility)
- RateSource (multi-source support)

---

## Conclusion

The current data model has significant gaps across all five feature areas analyzed. The most critical gaps are:

1. **Payment/Alert separation** - Business logic and payment logic are mixed
2. **Email tracking** - No visibility into email delivery
3. **User security** - No email verification or password reset
4. **Rate model duplication** - Two similar models causing confusion

Addressing these gaps will require 14 new models and modifications to 4 existing models, aligned with the phased approach outlined in DATA_MODEL_EXPANSION_PLAN.md.
