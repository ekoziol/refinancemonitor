# Data Model Review

**Version:** 1.0
**Date:** 2026-01-11
**Reviewer:** Automated Analysis
**Status:** Complete

## Executive Summary

This document provides a comprehensive review of the existing data models in the refi_alert application. The review analyzes each model's fields, relationships, identifies gaps, redundant/poorly designed fields, and provides recommendations for improvements.

**Current Models:**
- User (11 fields)
- Mortgage (12 fields)
- Mortgage_Tracking (7 fields)
- Alert (18 fields)
- Trigger (9 fields)
- MortgageRate (8 fields) - Recently added

---

## 1. User Model

**Location:** `refi_monitor/models.py:6-33`

### Current Fields

| Field | Type | Nullable | Index | Notes |
|-------|------|----------|-------|-------|
| id | Integer | No (PK) | Yes | Primary key |
| name | String(100) | No | No | User's display name |
| email | String(40) | No | Yes (unique) | **Issue: 40 chars may be too short** |
| password | String(200) | No | No | Hashed password |
| credit_score | Integer | Yes | No | User's credit score |
| created_on | DateTime | Yes | No | **Issue: Should not be nullable** |
| updated_on | DateTime | Yes | No | Audit field |
| last_login | DateTime | Yes | No | Tracking field |
| last_paid_date | DateTime | Yes | No | **Issue: Unclear purpose, redundant?** |
| paid | Integer | Yes | No | **Issue: Boolean as Integer, unclear meaning** |
| mortgages | relationship | - | - | One-to-Many with Mortgage |

### Issues Identified

1. **Email Length (String(40))**: RFC 5321 allows up to 254 characters for email addresses. 40 is too restrictive.
   - **Recommendation:** Change to `String(255)`

2. **created_on Nullable**: Creation timestamp should never be null.
   - **Recommendation:** Add `default=db.func.now()` and set `nullable=False`

3. **last_paid_date Field**: Purpose unclear. Appears to duplicate subscription payment tracking.
   - **Recommendation:** Remove once Subscription model is implemented

4. **paid Field**: Integer used as boolean flag. Unclear semantics (0/1? count of payments?).
   - **Recommendation:** Remove once Subscription model is implemented, or rename and document

5. **Missing Fields**:
   - `email_verified` - No email verification flow
   - `is_active` - No account deactivation support
   - `phone_number` - No SMS notification support
   - `deleted_at` - No soft delete capability
   - `failed_login_attempts` / `locked_until` - No brute force protection

6. **Password Hashing (sha256)**:
   - `generate_password_hash(password, method='sha256')` uses SHA256
   - **Recommendation:** Consider using bcrypt or argon2 for better security

### Relationships

```
User (1) -> (N) Mortgage
User (1) -> (N) Alert (via Alert.user_id)
```

---

## 2. Mortgage Model

**Location:** `refi_monitor/models.py:36-51`

### Current Fields

| Field | Type | Nullable | Index | Notes |
|-------|------|----------|-------|-------|
| id | Integer | No (PK) | Yes | Primary key |
| user_id | Integer (FK) | - | No | **Missing index on FK** |
| name | String(100) | No | No | Mortgage nickname |
| zip_code | String(5) | No | No | Property location |
| original_principal | Float | No | No | Initial loan amount |
| original_term | Integer | No | No | Term in months |
| original_interest_rate | Float | No | No | Initial rate (decimal) |
| remaining_principal | Float | No | No | Current balance |
| remaining_term | Integer | No | No | Months remaining |
| credit_score | Integer | No | No | Credit score at origination |
| created_on | DateTime | Yes | No | **Issue: Should not be nullable** |
| updated_on | DateTime | Yes | No | Audit field |
| trackings | relationship | - | - | One-to-Many with Mortgage_Tracking |
| alerts | relationship | - | - | One-to-Many with Alert |

### Issues Identified

1. **user_id Missing Index**: Foreign key queries will be slow without index.
   - **Recommendation:** Add `index=True` to user_id

2. **Float for Currency**: Float can have precision issues with currency.
   - **Recommendation:** Consider `Numeric(12, 2)` for monetary values

3. **created_on Nullable**: Should have default value and not be nullable.

4. **Missing Fields**:
   - `estimated_property_value` - Needed for LTV calculations
   - `property_type` - Single family, condo, etc. affects rates
   - `occupancy_type` - Primary, secondary, investment
   - `lender_name` - Current lender
   - `loan_type` - Conventional, FHA, VA, USDA
   - `deleted_at` - Soft delete support
   - `last_rate_check_date` - Prevent redundant API calls

5. **No Cascade Behavior Defined**: FK doesn't specify `ondelete` behavior.

### Relationships

```
Mortgage (N) <- (1) User
Mortgage (1) -> (N) Mortgage_Tracking
Mortgage (1) -> (N) Alert
```

---

## 3. Mortgage_Tracking Model

**Location:** `refi_monitor/models.py:54-63`

### Current Fields

| Field | Type | Nullable | Index | Notes |
|-------|------|----------|-------|-------|
| id | Integer | No (PK) | Yes | Primary key |
| mortgage_id | Integer (FK) | - | No | **Missing index on FK** |
| current_rate | Float | No | No | Current market rate |
| current_remaining_term | Integer | No | No | Remaining months |
| current_remaining_principal | Float | No | No | Current balance |
| created_on | DateTime | Yes | No | Timestamp |
| updated_on | DateTime | Yes | No | Audit field |

### Issues Identified

1. **Naming Convention**: Class name `Mortgage_Tracking` uses underscore instead of CamelCase.
   - **Recommendation:** Rename to `MortgageTracking`

2. **Table Name Mismatch**: `__tablename__ = 'mortgage_current_value'` doesn't match class name.
   - **Recommendation:** Rename to `mortgage_tracking` for consistency

3. **mortgage_id Missing Index**: FK should be indexed.

4. **Purpose Unclear**: This model tracks point-in-time snapshots of mortgage values. However:
   - Rate updates in `rate_updater.py` update ALL records with the same rate
   - `current_remaining_term` and `current_remaining_principal` duplicate Mortgage fields
   - **Question:** Should this be historical tracking or just current state?

5. **Relationship Direction**: Uses `Mortgage.trackings` for access. Consider adding `backref` for bidirectional access.

### Usage Analysis

From `rate_updater.py:87-99`:
```python
tracking_records = Mortgage_Tracking.query.all()
for record in tracking_records:
    record.current_rate = primary_rate
    record.updated_on = datetime.utcnow()
```

This updates ALL tracking records with the same rate, which suggests:
- It's not storing per-zip-code rates
- Not historical (just updating in place)
- **Recommendation:** Clarify purpose or remove in favor of MortgageRate model

---

## 4. Alert Model

**Location:** `refi_monitor/models.py:66-93`

### Current Fields

| Field | Type | Nullable | Index | Notes |
|-------|------|----------|-------|-------|
| id | Integer | No (PK) | Yes | Primary key |
| user_id | Integer (FK) | - | No | **Missing index** |
| mortgage_id | Integer (FK) | - | No | **Missing index** |
| alert_type | String | No | No | "monthly_payment" or "interest_rate" |
| target_monthly_payment | Float | Yes | No | Target payment amount |
| target_interest_rate | Float | Yes | No | Target rate |
| target_term | Integer | No | No | Refinance term in months |
| estimate_refinance_cost | Float | No | No | Expected closing costs |
| calculated_refinance_cost | Float | Yes | No | **Unused?** |
| created_on | DateTime | Yes | No | Timestamp |
| updated_on | DateTime | Yes | No | Audit field |
| initial_payment | Boolean | Yes | No | **Stripe: First payment made** |
| payment_status | String | Yes | No | **Stripe: active/incomplete/etc** |
| initial_period_start | Integer | Yes | No | **Stripe: Unix timestamp** |
| initial_period_end | Integer | Yes | No | **Stripe: Unix timestamp** |
| period_start | Integer | Yes | No | **Stripe: Current period** |
| period_end | Integer | Yes | No | **Stripe: Current period** |
| price_id | String | Yes | No | **Stripe: Price ID** |
| stripe_customer_id | String | Yes | No | **Stripe: Customer ID** |
| stripe_invoice_id | String | Yes | No | **Stripe: Actually subscription ID** |
| triggers | relationship | - | - | One-to-Many with Trigger |

### Issues Identified

1. **Separation of Concerns**: Alert mixes business logic (alert settings) with payment processing (Stripe fields).
   - **Critical Recommendation:** Extract Stripe fields into separate `Subscription` model

2. **Redundant Date Fields**:
   - `initial_period_start` / `initial_period_end` vs `period_start` / `period_end`
   - After first billing cycle, initial_* becomes historical
   - **Recommendation:** Move to Subscription model with proper history

3. **Misleading Field Name**: `stripe_invoice_id` actually stores subscription ID (see `mortgage.py:360`)
   - **Recommendation:** Rename or fix usage

4. **Missing Indexes**: Both foreign keys lack indexes.

5. **alert_type Not Enum**: Uses String instead of Enum for type safety.
   - **Recommendation:** Use `db.Enum('monthly_payment', 'interest_rate')`

6. **Missing Fields**:
   - `is_active` - Alert pause/resume capability
   - `last_notification_sent_at` - Prevent notification spam
   - `notification_count` - Track engagement
   - `deleted_at` - Soft delete

7. **Inconsistent Payment Status Values**:
   - `mortgage.py:172`: Sets `payment_status="incomplete"`
   - `mortgage.py:352`: Sets `payment_status='active'`
   - `scheduler.py:116`: Queries `payment_status='active'`
   - `rate_updater.py:125-128`: Queries `payment_status == 'paid'`
   - **Issue:** Code uses both 'active' and 'paid' - need to standardize

---

## 5. Trigger Model

**Location:** `refi_monitor/models.py:96-108`

### Current Fields

| Field | Type | Nullable | Index | Notes |
|-------|------|----------|-------|-------|
| id | Integer | No (PK) | Yes | Primary key |
| alert_id | Integer (FK) | - | No | **Missing index** |
| alert_type | String | No | No | Duplicated from Alert |
| alert_trigger_status | Integer | No | No | **Issue: Integer instead of Enum** |
| alert_trigger_reason | String | No | No | Trigger explanation |
| alert_trigger_date | DateTime | Yes | No | When triggered |
| created_on | DateTime | Yes | No | Timestamp |
| updated_on | DateTime | Yes | No | Audit field |

### Issues Identified

1. **Duplicate Field Check**: The DATA_MODEL_EXPANSION_PLAN.md mentions duplicate `alert_trigger_date` field.
   - Review of models.py shows only one definition (lines 103-105)
   - This may have been a historical issue or planned fix
   - **Status:** Need to verify in migration history

2. **Integer Status**: `alert_trigger_status` uses Integer (1=success, 0=expired per expansion plan).
   - **Recommendation:** Use Enum for clarity: `'triggered', 'notified', 'acknowledged', 'expired'`

3. **Field Naming**: Redundant `alert_` prefix on all fields.
   - **Recommendation:** Rename to `status`, `reason`, `triggered_at`

4. **Duplicate alert_type**: Already stored in parent Alert record.
   - **Question:** Is this for historical tracking (if Alert.alert_type changes)?
   - **Recommendation:** Keep for denormalization but document purpose

5. **Missing Fields**:
   - `threshold_value` - What value triggered the alert
   - `current_value` - Current market value at trigger time
   - `notification_sent` - Was notification delivered
   - `user_viewed` / `viewed_at` - User engagement tracking
   - `expires_at` - Trigger expiration

### Usage Analysis

From `scheduler.py:143-151`:
```python
trigger = Trigger(
    alert_id=alert.id,
    alert_type=alert.alert_type,
    alert_trigger_status=1,  # 1 = success
    alert_trigger_reason=reason,
    alert_trigger_date=datetime.utcnow(),
    created_on=datetime.utcnow(),
    updated_on=datetime.utcnow()
)
```

Status values used:
- `1` = Successful trigger (scheduler.py:101, 158)
- `0` = Not used but implied for failed/expired

---

## 6. MortgageRate Model

**Location:** `refi_monitor/models.py:111-130`

### Current Fields

| Field | Type | Nullable | Index | Notes |
|-------|------|----------|-------|-------|
| id | Integer | No (PK) | Yes | Primary key |
| zip_code | String(5) | No | Yes | Location |
| term_months | Integer | No | Yes | Loan term |
| rate | Float | No | No | Interest rate |
| rate_date | DateTime | No | Yes | Rate effective date |
| created_on | DateTime | Yes | No | Timestamp |
| updated_on | DateTime | Yes | No | Audit field |

### Issues Identified

1. **Well Designed**: This is the newest model and follows better patterns:
   - Proper indexes on query fields
   - Composite index for common query pattern
   - Uses `__table_args__` for additional constraints

2. **Minor Issues**:
   - `created_on` should not be nullable
   - Could add `source` field to track where rate came from
   - Consider Numeric instead of Float for precision

3. **Missing Unique Constraint**: Could have duplicate rates for same zip/term/date.
   - **Recommendation:** Add unique constraint on `(zip_code, term_months, rate_date)`

### Relationship to RateFetcher

From `rate_updater.py:21-54`, the `RateFetcher` class returns mock data:
```python
base_rates = {
    '30 YR FRM': 0.0294,
    '15 YR FRM': 0.0245,
    '5/1 YR ARM': 0.0268,
    ...
}
```

**Issue:** Rate types use string keys ('30 YR FRM') but MortgageRate uses `term_months` (Integer).
- **Recommendation:** Standardize rate type representation

---

## 7. Relationship Analysis

### Current Relationship Map

```
User (1) ──────┬────────────────> (N) Mortgage
              │                         │
              │                         │ (1:N)
              │                         ▼
              │                  Mortgage_Tracking
              │
              └────────────────> (N) Alert
                                       │
                                       │ (1:N)
                                       ▼
                                    Trigger

MortgageRate (standalone - no relationships)
```

### Missing Relationships

1. **User ←→ Alert**: Alert has `user_id` FK but no relationship defined on User.
   - **Fix:** Add `alerts = db.relationship("Alert")` to User or use backref

2. **Mortgage_Tracking**: No backref to Mortgage.

3. **EmailLog**: Not implemented - no tracking of sent notifications.

### Cascade Behavior

**All foreign keys lack explicit `ondelete` behavior:**

| Relationship | Current | Recommended |
|--------------|---------|-------------|
| Mortgage.user_id | None | CASCADE |
| Mortgage_Tracking.mortgage_id | None | CASCADE |
| Alert.user_id | None | CASCADE |
| Alert.mortgage_id | None | CASCADE |
| Trigger.alert_id | None | CASCADE |

---

## 8. Index Analysis

### Current Indexes

| Model | Field | Indexed | Notes |
|-------|-------|---------|-------|
| User | email | Yes (unique) | Good |
| User | credit_score | No | Low priority |
| Mortgage | user_id (FK) | No | **Should index** |
| Mortgage_Tracking | mortgage_id (FK) | No | **Should index** |
| Alert | user_id (FK) | No | **Should index** |
| Alert | mortgage_id (FK) | No | **Should index** |
| Alert | payment_status | No | **Should index** - used in queries |
| Trigger | alert_id (FK) | No | **Should index** |
| MortgageRate | zip_code | Yes | Good |
| MortgageRate | term_months | Yes | Good |
| MortgageRate | rate_date | Yes | Good |
| MortgageRate | (composite) | Yes | Good |

### Recommended Indexes to Add

```sql
-- Foreign key indexes
CREATE INDEX ix_mortgage_user_id ON mortgage(user_id);
CREATE INDEX ix_mortgage_tracking_mortgage_id ON mortgage_current_value(mortgage_id);
CREATE INDEX ix_alert_user_id ON alert(user_id);
CREATE INDEX ix_alert_mortgage_id ON alert(mortgage_id);
CREATE INDEX ix_trigger_alert_id ON trigger(alert_id);

-- Query pattern indexes
CREATE INDEX ix_alert_payment_status ON alert(payment_status);
CREATE INDEX ix_trigger_status_date ON trigger(alert_trigger_status, alert_trigger_date DESC);
```

---

## 9. Rate Monitoring Architecture

### Current Flow

1. **Scheduler** (`scheduler.py`) runs daily rate updates
2. **RateUpdater** (`rate_updater.py`) fetches rates via **RateFetcher**
3. **RateFetcher** returns mock data (no real API integration)
4. All `Mortgage_Tracking` records updated with same rate
5. Alerts evaluated against current rate

### Issues

1. **No Real Rate Data**: RateFetcher uses mock data with random variation.
   - TODO comments indicate Freddie Mac API integration planned

2. **Rate Storage Confusion**:
   - `MortgageRate` model exists for per-zip-code/term rate storage
   - But `rate_updater.py` updates `Mortgage_Tracking` records
   - These two approaches aren't connected

3. **No Geographic Rate Variation**: All mortgages get same rate regardless of zip_code.

### Recommendation

Clarify rate storage strategy:
- **Option A:** Use MortgageRate for historical data, Mortgage_Tracking for current values
- **Option B:** Deprecate Mortgage_Tracking, use only MortgageRate
- **Option C:** Remove Mortgage_Tracking if redundant with MortgageRate

---

## 10. Email Notification Tracking

### Current State

From `notifications.py`:
- `send_alert_notification()` sends email on trigger
- `send_payment_confirmation()` sends payment emails
- **No logging of sent emails**

### Issues

1. **No EmailLog Model**: Cannot track:
   - Which emails were sent
   - Whether they were delivered
   - Whether they were opened/clicked
   - Duplicate prevention

2. **No Error Recovery**: If email fails, no retry mechanism.

3. **No Unsubscribe Tracking**: No way to manage email preferences.

---

## 11. Stripe Integration Analysis

### Current Payment Fields in Alert

| Field | Purpose | Issue |
|-------|---------|-------|
| initial_payment | Boolean - first payment made | Should be on Subscription |
| payment_status | String - subscription state | Inconsistent values used |
| initial_period_start | Unix timestamp | Redundant with period_start |
| initial_period_end | Unix timestamp | Redundant with period_end |
| period_start | Unix timestamp | Current billing period |
| period_end | Unix timestamp | Current billing period |
| price_id | Stripe Price ID | Should be on Subscription |
| stripe_customer_id | Stripe Customer | Belongs on User |
| stripe_invoice_id | Misnamed - actually subscription ID | Wrong name |

### Webhook Handling

From `mortgage.py:290-393`:
- Handles `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`
- Updates Alert model directly with payment data

### Issues

1. **stripe_customer_id on Alert**: Should be on User model (one customer per user).

2. **Mixed Semantics**: Alert model is doing too much.

3. **No Invoice History**: Only current subscription data stored.

---

## 12. Summary of Critical Issues

### High Priority (Data Integrity/Security)

| Issue | Model | Recommendation |
|-------|-------|----------------|
| Email length 40 chars | User | Increase to 255 |
| No email verification | User | Add email_verified field |
| SHA256 password hashing | User | Consider bcrypt/argon2 |
| Missing FK indexes | All | Add indexes |
| Float for currency | Mortgage, Alert | Use Numeric |
| No cascade delete | All FKs | Add ondelete behavior |

### Medium Priority (Design/Maintainability)

| Issue | Model | Recommendation |
|-------|-------|----------------|
| Stripe fields in Alert | Alert | Extract to Subscription model |
| Integer status in Trigger | Trigger | Use Enum |
| Inconsistent payment_status | Alert | Standardize to single set of values |
| Naming (Mortgage_Tracking) | Mortgage_Tracking | Rename to MortgageTracking |
| Table name mismatch | Mortgage_Tracking | Align class and table names |

### Low Priority (Enhancements)

| Issue | Model | Recommendation |
|-------|-------|----------------|
| Missing soft delete | All | Add deleted_at fields |
| No email logging | - | Add EmailLog model |
| No calculation history | - | Add CalculationHistory model |
| No user preferences | - | Add UserPreference model |

---

## 13. Comparison with DATA_MODEL_EXPANSION_PLAN.md

The expansion plan document already identifies most issues found in this review:

| Issue | Found in Review | In Expansion Plan |
|-------|-----------------|-------------------|
| Trigger duplicate date field | Not found in current code | Yes (may be fixed) |
| Alert mixing business/payment | Yes | Yes |
| No EmailLog | Yes | Yes |
| No CalculationHistory | Yes | Yes |
| Missing email verification | Yes | Yes |
| Missing soft deletes | Yes | Yes |
| Integer status in Trigger | Yes | Yes |

**Recommendation:** The expansion plan is comprehensive. This review validates its findings and confirms the proposed changes are appropriate.

---

## 14. Next Steps

1. **Immediate:** Add missing indexes on foreign keys (low risk)
2. **Short-term:** Fix payment_status inconsistency (standardize on 'active')
3. **Medium-term:** Implement Subscription model per expansion plan
4. **Long-term:** Complete full data model expansion

---

## Appendix: File Locations

| File | Purpose |
|------|---------|
| `refi_monitor/models.py` | All model definitions |
| `refi_monitor/calc.py` | Mortgage calculations |
| `refi_monitor/routes.py` | Main routes (dashboard, manage) |
| `refi_monitor/mortgage.py` | Mortgage/Alert CRUD, Stripe webhooks |
| `refi_monitor/auth.py` | Authentication routes |
| `refi_monitor/scheduler.py` | Background job scheduling |
| `refi_monitor/rate_updater.py` | Rate fetching and updating |
| `refi_monitor/notifications.py` | Email notification sending |
| `docs/DATA_MODEL_EXPANSION_PLAN.md` | Detailed expansion plan |
