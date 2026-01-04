# Comprehensive Testing Workflow

Run comprehensive testing across all project components and provide detailed results.

## Testing Sequence

1. **Pre-test Setup**:
   - Ensure all dependencies are installed
   - Check that Docker services are running
   - Verify environment variables are configured

2. **Build Verification**:
   - Run `nx run-many -t build` and report any build failures
   - Check for TypeScript compilation errors
   - Verify all packages build successfully

3. **Linting and Code Quality**:
   - Run `nx run-many -t lint` for all projects
   - Execute backend Python linting: `cd apps/backend && ./scripts/lint.sh`
   - Report any linting violations and suggest fixes

4. **Unit Testing**:
   - Run `nx run-many -t test` for all projects
   - Execute backend tests: `cd apps/backend && poetry run pytest --cov=src`
   - Execute MMM workbench tests: `cd mmm_workbench && poetry run pytest`
   - Report test coverage and identify areas needing more tests

5. **Integration Testing**:
   - Run any integration tests
   - Test API endpoints if applicable
   - Verify database connections and migrations

6. **E2E Testing**:
   - Run `nx run-many -t e2e` if E2E tests exist
   - Test critical user workflows
   - Capture any failures with detailed error messages

## Reporting

Provide a summary report including:
- Overall test results (pass/fail counts)
- Code coverage metrics
- Performance benchmarks
- Recommendations for improvement
- Priority issues that need immediate attention

If any tests fail, provide specific guidance on how to fix them.