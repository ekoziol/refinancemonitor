# Security Audit

Perform comprehensive security assessment for: $ARGUMENTS

## Security Assessment Process

1. **Authentication & Authorization Review**:
   - Verify OAuth 2.0/SAML implementation with Azure Entra ID
   - Check JWT token validation and expiration handling
   - Review role-based access controls
   - Validate session management and logout procedures

2. **Input Validation & Data Sanitization**:
   - Audit all API endpoints for input validation
   - Check for SQL injection vulnerabilities (should be none with Tortoise ORM)
   - Verify XSS protection in React components
   - Review file upload security if applicable

3. **Dependency Security**:
   - Scan Python dependencies: `poetry audit`
   - Check Node.js vulnerabilities: `npm audit` or `yarn audit`
   - Review outdated packages and security patches
   - Identify packages with known vulnerabilities

4. **API Security**:
   - Review rate limiting implementation
   - Check CORS configuration
   - Verify HTTPS enforcement
   - Audit API versioning and deprecation handling

5. **Database Security**:
   - Review database connection security (TLS)
   - Check for sensitive data exposure in logs
   - Verify data encryption at rest and in transit
   - Review backup and recovery security

6. **Infrastructure Security**:
   - Audit Docker container configurations
   - Review Azure security groups and firewall rules
   - Check secrets management (no hardcoded secrets)
   - Verify environment variable handling

7. **Frontend Security**:
   - Review content security policy (CSP)
   - Check for sensitive data in client-side storage
   - Verify secure API communication
   - Audit third-party script inclusion

## Security Checklist

### Authentication
- [ ] Multi-factor authentication available
- [ ] Secure password policies enforced
- [ ] Session timeout configured appropriately
- [ ] Account lockout protection implemented

### Data Protection
- [ ] Sensitive data encrypted in database
- [ ] PII handling complies with regulations
- [ ] Audit logging for data access
- [ ] Data retention policies implemented

### Infrastructure
- [ ] All communications use HTTPS/TLS
- [ ] Security headers configured
- [ ] Error messages don't expose sensitive info
- [ ] Regular security updates applied

### Code Security
- [ ] No hardcoded secrets or API keys
- [ ] Input validation on all user inputs
- [ ] Output encoding to prevent XSS
- [ ] Proper error handling without info leakage

## Vulnerability Assessment

### High Priority Issues
- Authentication bypasses
- SQL injection vulnerabilities
- Cross-site scripting (XSS)
- Insecure direct object references

### Medium Priority Issues
- Missing security headers
- Weak session management
- Insufficient logging and monitoring
- Vulnerable dependencies

### Low Priority Issues
- Information disclosure
- Missing rate limiting
- Weak password policies
- Insecure configurations

## Recommendations

Provide specific, actionable recommendations for each identified issue:
1. Immediate fixes for critical vulnerabilities
2. Short-term improvements for medium priority issues
3. Long-term security enhancements
4. Security awareness and training needs

## Compliance Considerations

### For MMM/Analytics Applications
- Data privacy regulations (GDPR, CCPA)
- Financial data handling requirements
- Marketing data usage compliance
- Cross-border data transfer restrictions

## Monitoring & Alerting

- Security event logging
- Anomaly detection
- Intrusion detection systems
- Regular security scan automation