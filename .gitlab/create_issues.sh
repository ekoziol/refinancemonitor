#!/bin/bash

# Script to create GitLab issues for React Migration project

echo "Creating GitLab issues for React Migration..."

# Phase 0: Test Infrastructure & Baseline
glab issue create \
  --title "[Phase 0] Setup Test Infrastructure" \
  --description "## Tasks
- [ ] Install pytest and testing dependencies
- [ ] Create test directory structure
- [ ] Configure pytest.ini
- [ ] Create conftest.py with shared fixtures

## Files to Create
- \`requirements-dev.txt\`
- \`pytest.ini\`
- \`tests/__init__.py\`
- \`tests/conftest.py\`

## Acceptance Criteria
- pytest installed and working
- Tests can be run with \`pytest tests/ -v\`
- Coverage reporting configured

## Time Estimate
1 day" \
  --label "Phase 0: Testing,type::testing,priority::critical" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 0] Create Test Fixtures" \
  --description "## Tasks
- [ ] Define 5 test scenarios with varied inputs
- [ ] Create tests/fixtures.py module
- [ ] Document fixture purpose and expected use

## Fixtures to Create
1. **FIXTURE_STANDARD** - Typical 30-year refinance
2. **FIXTURE_ZERO_RATE** - Edge case with 0% interest
3. **FIXTURE_BAD_REFI** - Refinance that costs more money
4. **FIXTURE_HIGH_RATE** - High interest rate scenario
5. **FIXTURE_SHORT_TERM** - 15-year mortgage

## Files to Create
- \`tests/fixtures.py\`

## Acceptance Criteria
- All 5 fixtures defined with input parameters
- Fixtures importable in test files
- Documentation for each fixture

## Time Estimate
1 day" \
  --label "Phase 0: Testing,type::testing" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 0] Generate Baseline Expected Values" \
  --description "## Tasks
- [ ] Create tests/generate_baseline.py script
- [ ] Run current Dash implementation with all fixtures
- [ ] Capture all output values
- [ ] Update fixtures.py with expected_outputs

## Script Functionality
- Read all fixtures from fixtures.py
- Call calc.py functions to generate outputs
- Format outputs as JSON
- Provide copy-paste ready format for fixtures.py

## Files to Create
- \`tests/generate_baseline.py\`

## Acceptance Criteria
- Script runs successfully
- All 5 fixtures have complete expected_outputs
- Values match current Dash implementation
- Documented in tests/BASELINE_REPORT.md

## Time Estimate
1 day" \
  --label "Phase 0: Testing,type::implementation" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 0] Write Unit Tests for calc.py" \
  --description "## Tasks
- [ ] Test calc_loan_monthly_payment() - 5+ test cases
- [ ] Test create_mortage_range() - structure and values
- [ ] Test find_target_interest_rate() - reverse calculation
- [ ] Test amount_remaining() - balance at different points
- [ ] Test create_mortgage_table() - amortization table
- [ ] Test find_break_even_interest() - threshold finding
- [ ] Test create_efficient_frontier() - complex calculation
- [ ] Test ipmt_total() - interest calculations
- [ ] Test time_to_even() - breakeven months
- [ ] Test calculate_recoup_data() - recoup analysis
- [ ] Parametrize tests with all 5 fixtures
- [ ] Achieve 100% code coverage on calc.py

## Files to Create
- \`tests/unit/__init__.py\`
- \`tests/unit/test_calc.py\`

## Acceptance Criteria
- 50+ unit tests written
- All tests passing
- 100% coverage on refi_monitor/calc.py
- All edge cases covered (zero rate, negative values, etc.)

## Time Estimate
2 days" \
  --label "Phase 0: Testing,type::testing,priority::critical" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 0] Document Baseline & Known Issues" \
  --description "## Tasks
- [ ] Run complete test suite
- [ ] Document test results
- [ ] Identify bugs in current implementation
- [ ] Fix critical bugs (e.g., calculate_recoup_data incomplete)
- [ ] Create baseline report

## Files to Create
- \`tests/BASELINE_REPORT.md\`

## Known Issues to Document
1. calculate_recoup_data() missing interest_refi_savings column
2. [Any other issues found]

## Acceptance Criteria
- All unit tests documented as passing/failing
- Known issues catalogued with severity
- Critical bugs fixed
- Baseline report complete

## Test Gate
✅ **All unit tests must pass before Phase 1**

## Time Estimate
1 day" \
  --label "Phase 0: Testing,type::documentation,priority::critical" \
  --milestone "React Migration"

# Phase 1: API Layer
glab issue create \
  --title "[Phase 1] Write API Contract Tests (TDD)" \
  --description "## Tasks
- [ ] Create tests/api/test_calculator_api.py
- [ ] Write TestAPIHealth class - health check endpoint
- [ ] Write TestAPIValidation class - input validation tests
- [ ] Write TestAPICalculations class - calculation correctness
- [ ] Write TestAPIChartData class - chart data structure tests
- [ ] Parametrize with all 5 fixtures

## Test Coverage
- Health check endpoint
- Missing required fields
- Invalid values (negative principal, invalid rates)
- All 5 fixtures return correct data
- Chart data arrays have correct structure

## Files to Create
- \`tests/api/__init__.py\`
- \`tests/api/test_calculator_api.py\`

## Acceptance Criteria
- 30+ API contract tests written
- Tests FAIL initially (API not implemented yet)
- Clear test descriptions
- All fixtures covered

## Note
These tests define the API contract. Implementation comes next.

## Time Estimate
1 day" \
  --label "Phase 1: API,type::testing,priority::critical" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 1] Implement API Blueprint" \
  --description "## Tasks
- [ ] Create refi_monitor/api/ package
- [ ] Create schemas.py with CalculatorRequest/Response
- [ ] Create calculator.py with /api/calculator/compute endpoint
- [ ] Implement request validation
- [ ] Implement computation logic (calls calc.py)
- [ ] Register API blueprint in __init__.py
- [ ] Add CORS support for development
- [ ] Run API tests until they pass

## Files to Create
- \`refi_monitor/api/__init__.py\`
- \`refi_monitor/api/schemas.py\`
- \`refi_monitor/api/calculator.py\`

## API Endpoint
**POST /api/calculator/compute**

Request:
\`\`\`json
{
  \"originalPrincipal\": 400000,
  \"originalRate\": 0.045,
  \"originalTerm\": 360,
  \"remainingPrincipal\": 364631.66,
  \"remainingTerm\": 300,
  \"targetRate\": 0.02,
  \"targetTerm\": 360,
  \"refiCost\": 5000
}
\`\`\`

Response: All computed values + chart data arrays

## Acceptance Criteria
- API endpoint responds correctly
- All validation working
- All API contract tests passing
- Can be tested with curl/Postman

## Time Estimate
2 days" \
  --label "Phase 1: API,type::implementation,priority::critical" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 1] Regression Tests - API vs Dash Parity" \
  --description "## Tasks
- [ ] Create tests/regression/test_parity.py
- [ ] Implement get_dash_output() - calls current Dash callbacks
- [ ] Implement get_api_output() - calls new API
- [ ] Test scalar values match (within \$0.01)
- [ ] Test chart data arrays match
- [ ] Test all 5 fixtures for parity
- [ ] Document any differences found

## Critical Requirement
**API must produce IDENTICAL output to Dash callbacks**

Tolerance: \$0.01 for currency values

## Files to Create
- \`tests/regression/__init__.py\`
- \`tests/regression/test_parity.py\`

## Acceptance Criteria
- All regression tests passing
- 100% parity between Dash and API
- Differences < \$0.01 for all values
- All 5 fixtures produce matching results

## Test Gate
✅ **100% parity required before Phase 2**

## Time Estimate
1 day" \
  --label "Phase 1: API,type::testing,priority::critical" \
  --milestone "React Migration"

# Phase 2: React Frontend
glab issue create \
  --title "[Phase 2] Setup React Project & Testing" \
  --description "## Tasks
- [ ] Create Vite + React + TypeScript project
- [ ] Configure build output to refi_monitor/static/dist
- [ ] Install dependencies (Plotly, Axios, etc.)
- [ ] Install testing libraries (Vitest, Testing Library)
- [ ] Configure Vitest
- [ ] Setup Tailwind CSS
- [ ] Configure API proxy for development

## Commands
\`\`\`bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-plotly.js plotly.js axios
npm install -D vitest @testing-library/react @testing-library/jest-dom
\`\`\`

## Files to Create
- \`frontend/vite.config.ts\`
- \`frontend/tsconfig.json\`
- \`frontend/tailwind.config.js\`
- \`frontend/src/test/setup.ts\`

## Acceptance Criteria
- React app runs in dev mode
- Tests can be run with \`npm test\`
- Build outputs to correct directory
- API proxy working

## Time Estimate
1 day" \
  --label "Phase 2: React,type::implementation" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 2] Create TypeScript Types & API Client" \
  --description "## Tasks
- [ ] Create services/types.ts with all interfaces
- [ ] Create services/api.ts with API client
- [ ] Configure axios instance
- [ ] Create calculatorAPI object with compute() method
- [ ] Handle errors properly

## Type Definitions Needed
- CalculatorInputs
- CalculatorResponse
- MortgageRangePoint
- RecoupDataPoint
- EfficientFrontierPoint
- PayoffScenarioPoint

## Files to Create
- \`frontend/src/services/types.ts\`
- \`frontend/src/services/api.ts\`

## Acceptance Criteria
- All TypeScript types defined
- API client working
- Error handling implemented
- Type-safe API calls

## Time Estimate
0.5 days" \
  --label "Phase 2: React,type::implementation" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 2] Create Custom React Hooks" \
  --description "## Tasks
- [ ] Create hooks/useDebounce.ts
- [ ] Create hooks/useCalculator.ts
- [ ] Test debouncing works (500ms delay)
- [ ] Test auto-recalculation on input change
- [ ] Handle loading and error states

## Hooks to Create
1. **useDebounce** - Debounce inputs to avoid excessive API calls
2. **useCalculator** - Main hook for calculator state and API calls

## Files to Create
- \`frontend/src/hooks/useDebounce.ts\`
- \`frontend/src/hooks/useCalculator.ts\`

## Acceptance Criteria
- Debouncing working correctly
- API called 500ms after user stops typing
- Loading states handled
- Error states handled

## Time Estimate
0.5 days" \
  --label "Phase 2: React,type::implementation" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 2] Write React Component Tests (TDD)" \
  --description "## Tasks
- [ ] Create Calculator.test.tsx
- [ ] Test component renders correctly
- [ ] Test API called on mount
- [ ] Test values displayed after API response
- [ ] Test loading state shown while calculating
- [ ] Test error state on API failure
- [ ] Create InputSection.test.tsx
- [ ] Create SummaryTable.test.tsx

## Test Coverage
- Component rendering
- User interactions
- API integration
- Loading/error states
- Data display

## Files to Create
- \`frontend/src/components/Calculator/__tests__/Calculator.test.tsx\`
- \`frontend/src/components/Calculator/__tests__/InputSection.test.tsx\`
- \`frontend/src/components/Calculator/__tests__/SummaryTable.test.tsx\`

## Acceptance Criteria
- 20+ component tests written
- Tests FAIL initially (components not built)
- Mock API responses
- Test user interactions

## Note
Write tests FIRST, then implement components

## Time Estimate
1 day" \
  --label "Phase 2: React,type::testing" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 2] Implement React Components" \
  --description "## Tasks
- [ ] Create InputSection component (4-column layout)
- [ ] Create SummaryTable component (10-row metrics)
- [ ] Create Calculator container component
- [ ] Wire up useCalculator hook
- [ ] Style with Tailwind CSS
- [ ] Run tests until they pass

## Components to Create
1. **InputSection** - Original/remaining/target inputs
2. **SummaryTable** - Key metrics table
3. **Calculator** - Main container

## Files to Create
- \`frontend/src/components/Calculator/InputSection.tsx\`
- \`frontend/src/components/Calculator/SummaryTable.tsx\`
- \`frontend/src/components/Calculator/Calculator.tsx\`
- \`frontend/src/components/Calculator/index.ts\`

## Development Process
Run \`npm test -- --watch\` and keep coding until tests pass

## Acceptance Criteria
- All component tests passing
- UI displays correct data
- Inputs trigger API calls
- Loading/error states working

## Test Gate
✅ **All component tests passing before Phase 3**

## Time Estimate
2 days" \
  --label "Phase 2: React,type::implementation,priority::critical" \
  --milestone "React Migration"

# Phase 3: Chart Components
glab issue create \
  --title "[Phase 3] Write Chart Component Tests (TDD)" \
  --description "## Tasks
- [ ] Create PaymentChart.test.tsx
- [ ] Create BreakevenChart.test.tsx
- [ ] Create EfficientFrontierChart.test.tsx
- [ ] Create PayoffScenarioChart.test.tsx
- [ ] Test Plotly chart rendering
- [ ] Test correct number of traces
- [ ] Test data passed to Plotly

## Test Coverage
- Chart renders
- Correct traces displayed
- Data formatted correctly
- Layout configuration

## Files to Create
- \`frontend/src/components/Charts/__tests__/PaymentChart.test.tsx\`
- \`frontend/src/components/Charts/__tests__/BreakevenChart.test.tsx\`
- \`frontend/src/components/Charts/__tests__/EfficientFrontierChart.test.tsx\`
- \`frontend/src/components/Charts/__tests__/PayoffScenarioChart.test.tsx\`

## Acceptance Criteria
- 12+ chart tests written
- Tests FAIL initially
- Mock chart data

## Time Estimate
1 day" \
  --label "Phase 3: Charts,type::testing" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 3] Implement Chart Components" \
  --description "## Tasks
- [ ] Create PaymentChart component
- [ ] Create BreakevenChart component
- [ ] Create EfficientFrontierChart component
- [ ] Create PayoffScenarioChart component
- [ ] Configure Plotly layout for each chart
- [ ] Add shapes/annotations (threshold lines, etc.)
- [ ] Run tests until they pass

## Charts to Build
1. **PaymentChart** - Monthly payment vs interest rate
2. **BreakevenChart** - Breakeven analysis over time
3. **EfficientFrontierChart** - Interest rate threshold by month
4. **PayoffScenarioChart** - Loan payoff comparison

## Files to Create
- \`frontend/src/components/Charts/PaymentChart.tsx\`
- \`frontend/src/components/Charts/BreakevenChart.tsx\`
- \`frontend/src/components/Charts/EfficientFrontierChart.tsx\`
- \`frontend/src/components/Charts/PayoffScenarioChart.tsx\`
- \`frontend/src/components/Charts/index.ts\`

## Acceptance Criteria
- All 4 charts rendering correctly
- Data displayed accurately
- Interactive (zoom, pan, hover)
- All chart tests passing

## Test Gate
✅ **All chart tests passing before Phase 4**

## Time Estimate
2 days" \
  --label "Phase 3: Charts,type::implementation,priority::critical" \
  --milestone "React Migration"

# Phase 4: Integration & Deployment
glab issue create \
  --title "[Phase 4] Flask Integration - Serve React SPA" \
  --description "## Tasks
- [ ] Create templates/calculator.html to serve React SPA
- [ ] Update routes.py with /calculator/ route
- [ ] Remove Dash initialization from __init__.py
- [ ] Delete refi_monitor/dash/ directory
- [ ] Register API blueprint
- [ ] Add CORS for development
- [ ] Test full integration

## Files to Create/Modify
- \`refi_monitor/templates/calculator.html\`
- Update \`refi_monitor/routes.py\`
- Update \`refi_monitor/__init__.py\`

## Acceptance Criteria
- React app loads at /calculator/
- API endpoints working
- Dash code removed
- No errors in console

## Time Estimate
1 day" \
  --label "Phase 4: Deploy,type::implementation" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 4] End-to-End Tests" \
  --description "## Tasks
- [ ] Create tests/e2e/test_complete_flow.py
- [ ] Setup Selenium WebDriver
- [ ] Test complete user flow
- [ ] Test entering values and seeing results
- [ ] Test chart interactions
- [ ] Test error scenarios

## Test Scenarios
1. Load calculator page
2. Enter mortgage values
3. Wait for results
4. Verify displayed values
5. Test chart rendering

## Files to Create
- \`tests/e2e/__init__.py\`
- \`tests/e2e/test_complete_flow.py\`

## Dependencies
- selenium
- chromedriver

## Acceptance Criteria
- E2E tests running
- Full flow validated
- All scenarios passing

## Time Estimate
1 day" \
  --label "Phase 4: Deploy,type::testing" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 4] Performance Tests" \
  --description "## Tasks
- [ ] Create tests/performance/test_api_performance.py
- [ ] Test API response time < 500ms
- [ ] Test concurrent requests (100 simultaneous)
- [ ] Compare vs Dash performance
- [ ] Document performance improvements

## Performance Requirements
- API response < 500ms (95th percentile)
- Handle 100 concurrent users
- 5-10x faster than Dash

## Files to Create
- \`tests/performance/__init__.py\`
- \`tests/performance/test_api_performance.py\`

## Acceptance Criteria
- Performance tests passing
- API < 500ms response time
- Handles concurrent load
- Documented improvement vs Dash

## Time Estimate
1 day" \
  --label "Phase 4: Deploy,type::testing" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 4] Final Validation & QA" \
  --description "## Tasks
- [ ] Run complete test suite (backend + frontend)
- [ ] Manual testing with all 5 fixtures
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile testing (iOS, Android)
- [ ] Accessibility testing (WCAG 2.1 AA)
- [ ] Create validation report

## Complete Test Suite
\`\`\`bash
# Backend
pytest tests/ -v --cov=refi_monitor

# Frontend
cd frontend && npm test

# E2E
pytest tests/e2e/

# Performance
pytest tests/performance/
\`\`\`

## Validation Checklist
- [ ] All 130+ tests passing
- [ ] 5 fixtures tested manually
- [ ] Cross-browser compatible
- [ ] Mobile responsive
- [ ] Accessible
- [ ] Performance targets met

## Files to Create
- \`tests/VALIDATION_REPORT.md\`

## Test Gate
✅ **All tests passing before deployment**

## Time Estimate
1 day" \
  --label "Phase 4: Deploy,type::testing,priority::critical" \
  --milestone "React Migration"

glab issue create \
  --title "[Phase 4] Production Deployment" \
  --description "## Tasks
- [ ] Update Procfile for Heroku
- [ ] Configure buildpacks (Python + Node.js)
- [ ] Add frontend build to deployment
- [ ] Update environment variables
- [ ] Deploy to production
- [ ] Run smoke tests
- [ ] Monitor for errors
- [ ] Create rollback plan

## Deployment Steps
1. Update Procfile
2. Configure package.json with heroku-postbuild
3. Test build locally
4. Deploy to Heroku
5. Verify production API
6. Monitor logs

## Rollback Plan
If issues occur:
1. Revert last commit
2. Re-enable Dash
3. Redeploy

## Acceptance Criteria
- Deployed to production
- Calculator working correctly
- No errors in logs
- All features functional

## Post-Deployment Validation
- [ ] Test with production URL
- [ ] Verify all fixtures work
- [ ] Check performance
- [ ] Monitor for 24 hours

## Time Estimate
1 day" \
  --label "Phase 4: Deploy,type::implementation,priority::critical" \
  --milestone "React Migration"

echo "✅ All issues created successfully!"
echo ""
echo "View issues: glab issue list --milestone 'React Migration'"
