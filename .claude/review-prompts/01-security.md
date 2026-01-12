# Security Review

Review this code for security vulnerabilities, focusing on:

## Authentication & Authorization
- Session management and cookie security
- Password hashing and storage
- Access control for protected routes
- Admin functionality protection

## Financial Data Protection
- PII handling (names, addresses, SSN references)
- Financial data encryption at rest and in transit
- Secure storage of mortgage details
- API key and secret management

## Common Vulnerabilities
- SQL injection in database queries
- XSS in template rendering
- CSRF protection on forms
- Command injection risks
- Insecure deserialization

## Third-Party Integrations
- Stripe webhook signature verification
- Email header injection prevention
- Rate API response validation

Flag any issues with severity level (Critical/High/Medium/Low).
