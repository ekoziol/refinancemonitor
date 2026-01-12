# Security Audit Report

**Date:** 2026-01-12
**Auditor:** Claude (Automated Security Audit)
**Scope:** Comprehensive security review before production deployment

---

## Executive Summary

This audit identified **4 critical/high vulnerabilities** that must be fixed before production deployment, along with several medium and low severity issues. The codebase has good foundations with SQLAlchemy ORM (preventing SQL injection) and Flask-WTF CSRF protection, but requires fixes in password hashing, URL validation, authorization, and Stripe webhook handling.

---

## Findings Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 1 | **FIXED** |
| High | 3 | **FIXED** |
| Medium | 4 | 2 Fixed, 2 Recommended |
| Low | 1 | Advisory |

### Fixes Applied
- Password hashing upgraded from SHA256 to scrypt
- Open redirect vulnerability patched with URL validation
- Stripe webhook now requires signature verification
- Admin endpoints now require admin role
- Hardcoded URLs replaced with environment variable
- Error leakage fixed (generic messages returned)
- Database migration added for is_admin field

---

## Critical Vulnerabilities

### 1. Weak Password Hashing Algorithm

**Severity:** CRITICAL
**Location:** `refi_monitor/models.py:26`
**Status:** FIXED

**Description:**
The application uses SHA256 for password hashing via `generate_password_hash(password, method='sha256')`. SHA256 is a cryptographic hash function, NOT a password hashing algorithm. It lacks:
- Cost factor (work factor) to slow down brute force attacks
- Memory-hard properties
- Built-in salt iteration

**Current Code:**
```python
def set_password(self, password):
    """Create hashed password."""
    self.password = generate_password_hash(password, method='sha256')
```

**Recommended Fix:**
```python
def set_password(self, password):
    """Create hashed password using bcrypt."""
    self.password = generate_password_hash(password, method='pbkdf2:sha256:600000')
```

Or better, use bcrypt directly:
```python
from werkzeug.security import generate_password_hash

def set_password(self, password):
    """Create hashed password using scrypt (default in modern Werkzeug)."""
    self.password = generate_password_hash(password)  # Uses scrypt by default
```

**Impact:** Passwords can be cracked significantly faster if database is compromised.

---

## High Severity Vulnerabilities

### 2. Open Redirect Vulnerability

**Severity:** HIGH
**Location:** `refi_monitor/auth.py:61-62`
**Status:** FIXED

**Description:**
The login endpoint accepts a `next` parameter from user input and redirects to it without validation. An attacker can craft a malicious URL like:
```
/login?next=https://evil.com/phishing
```

After successful login, the user would be redirected to the attacker's site.

**Current Code:**
```python
next_page = request.args.get('next')
return redirect(next_page or url_for('main_bp.dashboard'))
```

**Recommended Fix:**
```python
from urllib.parse import urlparse

def is_safe_url(target):
    """Validate that redirect target is safe (same host)."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# In login route:
next_page = request.args.get('next')
if next_page and not is_safe_url(next_page):
    next_page = None
return redirect(next_page or url_for('main_bp.dashboard'))
```

**Impact:** Phishing attacks, credential theft via lookalike sites.

---

### 3. Missing Admin Authorization

**Severity:** HIGH
**Location:** `refi_monitor/routes.py:267-280`
**Status:** FIXED

**Description:**
The `/admin/trigger-alerts` endpoint only requires login (`@login_required`) but any authenticated user can access it. There's a TODO comment acknowledging this issue.

**Current Code:**
```python
@main_bp.route("/admin/trigger-alerts", methods=['POST'])
@login_required
def admin_trigger_alerts():
    # TODO: Add proper admin role checking
    # For now, any logged-in user can trigger (should be restricted in production)
```

**Recommended Fix:**
Add an `is_admin` field to the User model and create an admin_required decorator:
```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route("/admin/trigger-alerts", methods=['POST'])
@login_required
@admin_required
def admin_trigger_alerts():
    ...
```

**Impact:** Unauthorized users can trigger system operations.

---

### 4. Stripe Webhook Signature Bypass

**Severity:** HIGH
**Location:** `refi_monitor/mortgage.py:296-310`
**Status:** FIXED

**Description:**
The Stripe webhook handler falls back to processing unverified webhook data if `STRIPE_WEBHOOK_SECRET` is not configured. In production, this would allow attackers to forge payment events.

**Current Code:**
```python
if webhook_secret:
    # Verify signature
    event = stripe.Webhook.construct_event(...)
else:
    # DANGEROUS: Process unverified data
    data = request_data['data']
    event_type = request_data['type']
```

**Recommended Fix:**
```python
webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
if not webhook_secret:
    return jsonify({'error': 'Webhook secret not configured'}), 500

signature = request.headers.get('stripe-signature')
try:
    event = stripe.Webhook.construct_event(
        payload=request.data, sig_header=signature, secret=webhook_secret
    )
except stripe.error.SignatureVerificationError:
    return jsonify({'error': 'Invalid signature'}), 400
```

**Impact:** Payment fraud, fake subscription activations.

---

## Medium Severity Issues

### 5. Hardcoded Localhost URLs in Stripe Checkout

**Severity:** MEDIUM
**Location:** `refi_monitor/mortgage.py:271-272`
**Status:** FIXED

**Description:**
Stripe checkout success and cancel URLs are hardcoded to localhost.

**Current Code:**
```python
checkout_session = stripe.checkout.Session.create(
    ...
    success_url='http://localhost:5000/success',
    cancel_url='http://localhost:5000/cancel',
)
```

**Recommended Fix:**
```python
base_url = os.getenv('APP_BASE_URL', request.host_url.rstrip('/'))
checkout_session = stripe.checkout.Session.create(
    ...
    success_url=f'{base_url}/success',
    cancel_url=f'{base_url}/cancel',
)
```

---

### 6. Error Message Leakage

**Severity:** MEDIUM
**Location:** `refi_monitor/mortgage.py:284`
**Status:** FIXED

**Description:**
Exception details are returned directly to users, potentially exposing internal system information.

**Current Code:**
```python
except Exception as e:
    return str(e)
```

**Recommended Fix:**
```python
except Exception as e:
    app.logger.error(f"Checkout session creation failed: {e}")
    return jsonify({'error': 'Unable to create checkout session'}), 500
```

---

### 7. Weak Password Requirements

**Severity:** MEDIUM
**Location:** `refi_monitor/forms.py:38-43`
**Status:** RECOMMENDED FIX

**Description:**
Password only requires minimum 6 characters with no complexity requirements.

**Current Validation:**
```python
password = PasswordField(
    'Password',
    validators=[
        DataRequired(),
        Length(min=6, message='Select a stronger password.'),
    ],
)
```

**Recommended Fix:**
```python
from wtforms.validators import Regexp

password = PasswordField(
    'Password',
    validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.'),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
            message='Password must contain uppercase, lowercase, and a number.'
        ),
    ],
)
```

---

### 8. Missing Rate Limiting

**Severity:** MEDIUM
**Location:** Authentication endpoints
**Status:** RECOMMENDED FIX

**Description:**
No rate limiting on login/signup endpoints allows brute force attacks.

**Recommended Fix:**
Install Flask-Limiter:
```bash
pip install Flask-Limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    ...
```

---

## Low Severity Issues

### 9. XSS via |safe Filter

**Severity:** LOW
**Location:** Dashboard templates
**Status:** ADVISORY

**Description:**
Templates use `{{ graph|safe }}` for Plotly graphs. These graphs are server-generated from database values (not direct user input), so the risk is low. However, if user-controlled data ever flows into graph labels/titles, this could become exploitable.

**Current Usage:**
```jinja2
{{ status_graph|safe }}
{{ time_graph|safe }}
```

**Recommendation:**
Monitor that no user input flows directly into graph generation. Consider using Content Security Policy headers.

---

## Secure Implementations (No Issues Found)

### SQL Injection Protection ✓
- All database queries use SQLAlchemy ORM with parameterized queries
- `filter_by()` and `filter()` methods properly escape values
- No raw SQL queries found

### CSRF Protection ✓
- Flask-WTF CSRFProtect is properly initialized in `__init__.py`
- All forms inherit from FlaskForm which includes CSRF tokens
- Stripe webhook correctly exempted with `@csrf.exempt`

### Environment Variables ✓
- `.env` is in `.gitignore`
- `.env.example` provided with placeholder values
- Secrets loaded from environment, not hardcoded

### Session Security ✓
- Flask-Login properly configured
- `@login_required` decorator used consistently
- Proper logout functionality implemented

---

## Recommendations Priority

### Immediate (Before Production)
1. Fix password hashing algorithm (Critical)
2. Fix open redirect vulnerability (High)
3. Require Stripe webhook secret (High)
4. Add admin authorization (High)

### Short-term
5. Fix hardcoded URLs
6. Add rate limiting
7. Strengthen password requirements
8. Improve error handling

### Long-term
9. Add Content Security Policy headers
10. Implement security logging/monitoring
11. Add two-factor authentication option
12. Regular dependency vulnerability scanning

---

## Testing Recommendations

### Manual Testing
- Test login with malicious `next` parameter
- Verify password hash format in database
- Test Stripe webhook without signature
- Attempt admin endpoints as regular user

### Automated Testing
```bash
# Install security testing tools
pip install bandit safety

# Run static analysis
bandit -r refi_monitor/

# Check dependencies for known vulnerabilities
safety check
```

---

## Compliance Notes

For production deployment, consider:
- PCI DSS requirements for payment handling
- GDPR/CCPA for user data protection
- SOC 2 for service organization controls

---

*Report generated as part of Phase 6 security audit*
