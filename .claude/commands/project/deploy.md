# Project Deployment Workflow

Execute comprehensive deployment workflow for: $ARGUMENTS

## Pre-Deployment Checklist

1. **Code Quality Verification**:
   - Run full test suite: `nx run-many -t test`
   - Execute linting: `nx run-many -t lint`
   - Verify build success: `nx run-many -t build`
   - Check TypeScript compilation
   - Validate no security vulnerabilities

2. **Documentation Review**:
   - Ensure CLAUDE.md is updated
   - Verify API documentation is current
   - Check deployment guides are accurate
   - Update changelog if needed

3. **Environment Preparation**:
   - Verify environment variables are set
   - Check database migrations are ready
   - Validate Docker configurations
   - Ensure Azure resources are provisioned

## Deployment Process

1. **Backend Deployment**:
   - Build backend Docker images
   - Run database migrations
   - Deploy to Azure Container Instances
   - Verify API endpoints are responding
   - Check logs for any errors

2. **Frontend Deployment**:
   - Build optimized frontend bundle
   - Deploy to CDN/static hosting
   - Verify all routes are working
   - Check for console errors
   - Test responsive design

3. **ML Components**:
   - Deploy ML models to Azure ML
   - Verify inference endpoints
   - Test model predictions
   - Check monitoring and logging

4. **Data Engineering**:
   - Deploy data pipelines
   - Verify data flow and transformations
   - Check data quality validations
   - Test scheduled jobs

## Post-Deployment Validation

1. **Functional Testing**:
   - Test critical user workflows
   - Verify API functionality
   - Check database connectivity
   - Validate authentication flows

2. **Performance Testing**:
   - Monitor response times
   - Check resource utilization
   - Verify caching is working
   - Test under load conditions

3. **Security Testing**:
   - Verify authentication is working
   - Check authorization rules
   - Test for common vulnerabilities
   - Validate data encryption

4. **Monitoring Setup**:
   - Configure application monitoring
   - Set up alerts for critical metrics
   - Verify logging is working
   - Check health checks

## Rollback Plan

1. **Rollback Triggers**:
   - Critical functionality broken
   - Performance degradation >50%
   - Security vulnerabilities detected
   - Data corruption or loss

2. **Rollback Process**:
   - Revert to previous stable version
   - Restore database from backup if needed
   - Verify system functionality
   - Communicate status to stakeholders

## Deployment Checklist

- [ ] All tests passing
- [ ] Code quality gates met
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Docker images built and pushed
- [ ] Services deployed to Azure
- [ ] API endpoints responding
- [ ] Frontend accessible and functional
- [ ] ML models deployed and working
- [ ] Data pipelines operational
- [ ] Monitoring and alerting configured
- [ ] Rollback plan tested and ready
- [ ] Documentation updated
- [ ] Stakeholders notified