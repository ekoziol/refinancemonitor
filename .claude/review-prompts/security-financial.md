# Security & Financial Data Protection Review

Review this code for security vulnerabilities and proper handling of sensitive financial data.

## Critical Checks

### Secrets & Credentials
- [ ] No hardcoded API keys, passwords, or tokens
- [ ] Secrets loaded from environment variables or secure vault
- [ ] No credentials in comments, logs, or error messages
- [ ] `.env` files properly gitignored

### Financial Data Protection
- [ ] PII (SSN, account numbers) never logged
- [ ] Sensitive data masked in any user-facing output
- [ ] Financial data encrypted at rest and in transit
- [ ] Proper access controls on financial endpoints

### Injection Prevention
- [ ] SQL queries use parameterized statements
- [ ] No string concatenation in database queries
- [ ] User input sanitized before processing
- [ ] Command execution avoids shell injection

### API Security
- [ ] Authentication required on all financial endpoints
- [ ] Rate limiting on sensitive operations
- [ ] Input validation on all request parameters
- [ ] Proper error responses (no stack traces to clients)

## Questions to Answer

1. Are any API keys or secrets exposed in this code?
2. Could an attacker access financial data through this change?
3. Is user input properly validated and sanitized?
4. Are there any paths that bypass authentication?

## Red Flags

- `password`, `secret`, `api_key` as string literals
- SQL with f-strings or `.format()`
- `eval()`, `exec()`, or `subprocess.shell=True`
- Logging of request bodies containing financial data
- Missing `@require_auth` or equivalent decorators
