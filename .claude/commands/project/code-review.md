# Comprehensive Code Review

Perform detailed code review for: $ARGUMENTS

## Code Review Process

1. **Architecture & Design Review**:
   - Verify adherence to Domain-Driven Design principles
   - Check separation of concerns and single responsibility
   - Review dependency injection implementation
   - Validate CQRS pattern usage
   - Assess overall code organization and structure

2. **Code Quality Assessment**:
   - Check TypeScript type safety and explicit typing
   - Review naming conventions for clarity and consistency
   - Assess function and class complexity (cyclomatic complexity)
   - Verify proper error handling and edge case coverage
   - Check for code duplication and opportunities for refactoring

3. **Security Review**:
   - Scan for potential security vulnerabilities
   - Verify input validation and sanitization
   - Check for hardcoded secrets or sensitive data
   - Review authentication and authorization logic
   - Assess data exposure and privacy considerations

4. **Performance Analysis**:
   - Identify potential performance bottlenecks
   - Review database query efficiency
   - Check for unnecessary re-renders in React components
   - Assess memory usage and potential leaks
   - Review caching implementation and effectiveness

5. **Testing Coverage**:
   - Analyze unit test coverage and quality
   - Review integration test scenarios
   - Check for missing edge case tests
   - Assess test maintainability and clarity
   - Verify mock usage is appropriate

6. **Documentation Review**:
   - Check API documentation completeness
   - Review code comments for clarity and necessity
   - Verify README and setup instructions
   - Assess inline documentation quality
   - Check for outdated or misleading documentation

## Technology-Specific Reviews

### Backend Python/FastAPI
- [ ] Poetry dependencies are up-to-date and secure
- [ ] Tortoise ORM usage follows best practices
- [ ] Async/await patterns used correctly
- [ ] Pydantic models have proper validation
- [ ] FastAPI route handlers are well-structured
- [ ] Error handling is comprehensive and consistent
- [ ] Logging is appropriate and not excessive

### Frontend React/TypeScript
- [ ] Components follow single responsibility principle
- [ ] Props are properly typed with TypeScript
- [ ] State management (Zustand) is used appropriately
- [ ] React hooks usage follows rules of hooks
- [ ] Performance optimizations (useMemo, useCallback) used when needed
- [ ] Accessibility (a11y) standards are met
- [ ] Tailwind CSS classes are used consistently

### ML/PyMC Components
- [ ] Bayesian models are properly specified
- [ ] Prior distributions are well-justified
- [ ] Model diagnostics are implemented
- [ ] Convergence checks are in place
- [ ] Uncertainty quantification is included
- [ ] MLflow tracking is comprehensive
- [ ] Data validation pipelines are robust

## Code Quality Metrics

### Complexity Analysis
- Cyclomatic complexity per function/method
- Nesting depth and readability
- Function/method length and cohesion
- Class size and responsibility scope

### Maintainability
- Code duplication percentage
- Coupling between modules
- Cohesion within modules
- Documentation coverage

### Reliability
- Error handling coverage
- Input validation completeness
- Edge case handling
- Graceful failure mechanisms

## Review Checklist

### Code Structure
- [ ] Follows established project patterns
- [ ] Proper separation of concerns
- [ ] Clear and consistent naming
- [ ] Appropriate abstraction levels
- [ ] Minimal coupling between components

### Functionality
- [ ] Meets specified requirements
- [ ] Handles edge cases appropriately
- [ ] Error conditions are managed
- [ ] Performance is acceptable
- [ ] Security considerations addressed

### Quality Standards
- [ ] Code is readable and maintainable
- [ ] Tests are comprehensive and meaningful
- [ ] Documentation is clear and current
- [ ] Follows coding standards and conventions
- [ ] No obvious bugs or issues

## Feedback Format

### Critical Issues (Must Fix)
- Security vulnerabilities
- Functionality breaking bugs
- Performance critical issues
- Architecture violations

### Major Issues (Should Fix)
- Code quality problems
- Missing test coverage
- Documentation gaps
- Minor security concerns

### Minor Issues (Consider Fixing)
- Style guide violations
- Optimization opportunities
- Refactoring suggestions
- Documentation improvements

### Positive Feedback
- Well-designed solutions
- Good practices implemented
- Clear and maintainable code
- Effective problem solving

## Action Items

Provide specific, actionable recommendations:
1. Immediate fixes required before merge
2. Improvements for better maintainability
3. Performance optimization opportunities
4. Security enhancements to consider
5. Documentation updates needed

## Long-term Recommendations

- Code organization improvements
- Testing strategy enhancements
- Performance monitoring implementation
- Security hardening measures
- Documentation standardization