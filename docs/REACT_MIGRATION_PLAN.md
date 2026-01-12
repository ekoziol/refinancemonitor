# React Migration Plan - Hybrid Architecture (Test-First)

**Goal:** Migrate from Dash to React while keeping calculations server-side to protect IP and improve performance.

**Strategy:** Test current implementation → Build API with tests → Build React with tests → Validate parity

**Timeline:** 4-5 weeks (19 days)

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────┐
│         React Frontend (Vite)           │
│  - Input forms (controlled components)  │
│  - Summary tables                       │
│  - Plotly.js charts (client-rendered)   │
│  - Debounced API calls                  │
└──────────────┬──────────────────────────┘
               │ HTTP JSON API
               │ POST /api/calculator/compute
┌──────────────▼──────────────────────────┐
│         Flask Backend (Python)          │
│  - API Blueprint (/api/calculator)      │
│  - calc.py (proprietary logic)          │
│  - Returns computed data as JSON        │
│  - Auth, DB, Stripe (existing)          │
└─────────────────────────────────────────┘
```

**Key Benefits:**
- ✅ Protects proprietary efficient frontier calculation (server-side)
- ✅ 90% reduction in network calls vs current Dash
- ✅ Instant chart interactions (client-side rendering)
- ✅ 5-10x better performance at scale
- ✅ ~80% cost reduction at high load

---

## 🎯 Critical Principle: Test Gates

**NO phase can begin until the previous phase's tests pass 100%.**

Each phase has:
1. **Tests Written** - Define expected behavior (TDD)
2. **Implementation** - Build to pass tests
3. **Test Gate** - All tests must pass before next phase

---

## 📅 PHASE 0: Test Infrastructure & Baseline (Week 1 - 5 days)

**Goal:** Create comprehensive test coverage of CURRENT implementation before changing anything.

### 0.1 Setup Test Infrastructure (Day 1)

**Tasks:**
- [ ] Install pytest and testing dependencies
- [ ] Create test directory structure
- [ ] Configure pytest
- [ ] Create test fixtures module

**Install Dependencies:**
```bash
pip install pytest==7.4.0 pytest-cov==4.1.0 pytest-flask==1.2.0 pytest-mock==3.11.1
```

**Create Files:**

`requirements-dev.txt`:
```txt
pytest==7.4.0
pytest-cov==4.1.0
pytest-flask==1.2.0
pytest-mock==3.11.1
```

`pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=refi_monitor
    --cov-report=html
    --cov-report=term-missing
    --strict-markers
markers =
    unit: Unit tests for individual functions
    integration: Integration tests for components
    api: API endpoint tests
    regression: Regression tests comparing implementations
    slow: Tests that take a long time to run
```

**Directory Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── fixtures.py              # Test data fixtures
├── generate_baseline.py     # Script to capture baseline values
├── unit/
│   ├── __init__.py
│   └── test_calc.py         # Unit tests for calc.py
├── integration/
│   ├── __init__.py
│   └── test_dash_callbacks.py
├── api/
│   ├── __init__.py
│   └── test_calculator_api.py
├── regression/
│   ├── __init__.py
│   └── test_parity.py
├── e2e/
│   ├── __init__.py
│   └── test_complete_flow.py
└── performance/
    ├── __init__.py
    └── test_api_performance.py
```

---

### 0.2 Create Test Fixtures (Day 1-2)

**Tasks:**
- [ ] Define 5 test scenarios with varied inputs
- [ ] Create fixtures module
- [ ] Document fixture purpose

**Create:** `tests/fixtures.py`

```python
"""
Test fixtures with known-good values from current Dash implementation.
"""

# Fixture 1: Standard 30-Year Refinance (Baseline)
FIXTURE_STANDARD = {
    "name": "standard_refinance",
    "description": "Typical refinance scenario - 30yr to 30yr with lower rate",
    "inputs": {
        "original_principal": 400000.0,
        "original_rate": 0.045,
        "original_term": 360,
        "remaining_principal": 364631.66,
        "remaining_term": 300,
        "target_rate": 0.02,
        "target_term": 360,
        "refi_cost": 5000.0,
    },
    "expected_outputs": {
        # To be filled by running current implementation
        "original_monthly_payment": None,
        "refi_monthly_payment": None,
        "monthly_savings": None,
        # ... etc
    },
}

# Fixture 2: Zero Interest Rate (Edge Case)
FIXTURE_ZERO_RATE = {
    "name": "zero_rate_refinance",
    "description": "Edge case with 0% interest rate",
    "inputs": {
        "original_principal": 300000.0,
        "original_rate": 0.03,
        "original_term": 360,
        "remaining_principal": 280000.0,
        "remaining_term": 300,
        "target_rate": 0.0,  # EDGE CASE
        "target_term": 300,
        "refi_cost": 3000.0,
    },
    "expected_outputs": {},
}

# Fixture 3: Bad Refinance (Negative Savings)
FIXTURE_BAD_REFI = {
    "name": "bad_refinance",
    "description": "Refinance that costs more money (higher rate)",
    "inputs": {
        "original_principal": 200000.0,
        "original_rate": 0.025,
        "original_term": 360,
        "remaining_principal": 180000.0,
        "remaining_term": 300,
        "target_rate": 0.04,  # HIGHER than original
        "target_term": 360,
        "refi_cost": 8000.0,
    },
    "expected_outputs": {},
}

# Fixture 4: High Interest Rate
FIXTURE_HIGH_RATE = {
    "name": "high_rate_refinance",
    "description": "Refinancing from very high rate (8%) to moderate (6%)",
    "inputs": {
        "original_principal": 500000.0,
        "original_rate": 0.08,
        "original_term": 360,
        "remaining_principal": 480000.0,
        "remaining_term": 330,
        "target_rate": 0.06,
        "target_term": 360,
        "refi_cost": 10000.0,
    },
    "expected_outputs": {},
}

# Fixture 5: Short Term Loan (15-year)
FIXTURE_SHORT_TERM = {
    "name": "short_term_refinance",
    "description": "15-year mortgage refinance",
    "inputs": {
        "original_principal": 150000.0,
        "original_rate": 0.035,
        "original_term": 180,
        "remaining_principal": 100000.0,
        "remaining_term": 120,
        "target_rate": 0.025,
        "target_term": 120,
        "refi_cost": 2500.0,
    },
    "expected_outputs": {},
}

ALL_FIXTURES = [
    FIXTURE_STANDARD,
    FIXTURE_ZERO_RATE,
    FIXTURE_BAD_REFI,
    FIXTURE_HIGH_RATE,
    FIXTURE_SHORT_TERM,
]
```

---

### 0.3 Calculate Expected Values (Day 2)

**Tasks:**
- [ ] Create baseline generation script
- [ ] Run current implementation with all fixtures
- [ ] Capture outputs
- [ ] Update fixtures.py with actual values

**Create:** `tests/generate_baseline.py`

```python
"""
Generate baseline expected values by running current implementation.
"""
import json
from refi_monitor import calc
from tests.fixtures import ALL_FIXTURES

def calculate_expected_values(inputs):
    """Calculate all expected values using current calc.py"""
    # Basic calculations
    original_payment = calc.calc_loan_monthly_payment(
        inputs['original_principal'],
        inputs['original_rate'],
        inputs['original_term']
    )

    refi_payment = calc.calc_loan_monthly_payment(
        inputs['remaining_principal'],
        inputs['target_rate'],
        inputs['target_term']
    )

    monthly_savings = original_payment - refi_payment
    months_paid = inputs['original_term'] - inputs['remaining_term']

    # Total interest
    original_total_interest = calc.ipmt_total(
        inputs['original_rate'],
        inputs['original_term'],
        inputs['original_principal']
    )

    refi_total_interest = calc.ipmt_total(
        inputs['target_rate'],
        inputs['target_term'],
        inputs['remaining_principal']
    )

    interest_already_paid = calc.ipmt_total(
        inputs['original_rate'],
        inputs['original_term'],
        inputs['original_principal'],
        calc.get_per(months_paid)
    )

    total_loan_savings = original_total_interest - (interest_already_paid + refi_total_interest + inputs['refi_cost'])

    # Break-even
    if monthly_savings > 0:
        month_to_even_simple = float(calc.time_to_even(inputs['refi_cost'], monthly_savings))
    else:
        month_to_even_simple = None

    return {
        "original_monthly_payment": round(original_payment, 2),
        "refi_monthly_payment": round(refi_payment, 2),
        "monthly_savings": round(monthly_savings, 2),
        "months_paid": months_paid,
        "original_total_interest": round(original_total_interest, 2),
        "refi_total_interest": round(refi_total_interest, 2),
        "total_loan_savings": round(total_loan_savings, 2),
        "month_to_even_simple": month_to_even_simple,
        "target_interest_rate": inputs['target_rate'],
    }

if __name__ == '__main__':
    print("Generating baseline from current implementation...\n")
    for fixture in ALL_FIXTURES:
        print(f"Fixture: {fixture['name']}")
        expected = calculate_expected_values(fixture['inputs'])
        print(json.dumps(expected, indent=2))
        print("\n" + "="*80 + "\n")
```

**Run:**
```bash
python tests/generate_baseline.py
```

---

### 0.4 Write Unit Tests for calc.py (Day 3-4)

**Tasks:**
- [ ] Test every function in calc.py
- [ ] Cover edge cases
- [ ] Test mathematical precision
- [ ] Achieve 100% code coverage

**Create:** `tests/unit/test_calc.py`

```python
"""Unit tests for refi_monitor/calc.py"""
import pytest
import numpy as np
import pandas as pd
from refi_monitor import calc
from tests.fixtures import FIXTURE_STANDARD, ALL_FIXTURES

class TestCalcLoanMonthlyPayment:
    @pytest.mark.unit
    def test_standard_mortgage(self):
        payment = calc.calc_loan_monthly_payment(400000, 0.045, 360)
        assert abs(payment - 2026.74) < 0.01

    @pytest.mark.unit
    def test_zero_interest_rate(self):
        payment = calc.calc_loan_monthly_payment(300000, 0.0, 300)
        assert payment == 1000.0

    @pytest.mark.unit
    def test_negative_rate_falls_back(self):
        payment = calc.calc_loan_monthly_payment(360000, -0.01, 360)
        assert payment == 1000.0

# ... 40+ more test methods covering all functions
```

**Run:**
```bash
pytest tests/unit/test_calc.py -v --cov=refi_monitor.calc
```

**Target:** 100% coverage on calc.py

---

### 0.5 Document Baseline (Day 4-5)

**Tasks:**
- [ ] Run all tests and capture results
- [ ] Document any bugs found in current implementation
- [ ] Fix critical bugs before migration
- [ ] Create baseline report

**Create:** `tests/BASELINE_REPORT.md`

**TEST GATE:** ✅ All unit tests passing before Phase 1

---

## 📅 PHASE 1: API Layer with TDD (Week 2 - 3 days)

**Goal:** Build API endpoints that pass regression tests against Dash.

### 1.1 Write API Contract Tests FIRST (Day 6)

**Test-Driven Development: Write tests before implementation**

**Create:** `tests/api/test_calculator_api.py`

```python
"""API contract tests - written BEFORE implementation"""
import pytest
from tests.fixtures import ALL_FIXTURES

@pytest.fixture
def client():
    from refi_monitor import init_app
    app = init_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestAPIHealth:
    def test_health_check(self, client):
        response = client.get('/api/calculator/health')
        assert response.status_code == 200

class TestAPIValidation:
    def test_negative_principal(self, client):
        payload = {"originalPrincipal": -100000, ...}
        response = client.post('/api/calculator/compute', json=payload)
        assert response.status_code == 400

class TestAPICalculations:
    def test_standard_fixture(self, client):
        payload = {...}  # From FIXTURE_STANDARD
        response = client.post('/api/calculator/compute', json=payload)
        assert response.status_code == 200
        # Validate all outputs match fixture expected values
```

**These tests WILL FAIL initially** (API not built yet)

---

### 1.2 Implement API Blueprint (Day 6-7)

**Tasks:**
- [ ] Create API blueprint structure
- [ ] Create request/response schemas
- [ ] Implement /api/calculator/compute endpoint
- [ ] Implement input validation
- [ ] Run tests until they pass

**Create:**
- `refi_monitor/api/__init__.py`
- `refi_monitor/api/schemas.py`
- `refi_monitor/api/calculator.py`

**Iterative Development:**
```bash
# Write code, run tests, fix, repeat
pytest tests/api/test_calculator_api.py -v
```

**Keep going until all API tests pass.**

---

### 1.3 Regression Tests: API vs Dash (Day 8)

**Goal:** Prove API produces IDENTICAL output to Dash

**Create:** `tests/regression/test_parity.py`

```python
"""Regression tests: API must match Dash outputs exactly"""
import pytest
from tests.fixtures import ALL_FIXTURES

def get_dash_output(inputs):
    """Call actual Dash callback"""
    from refi_monitor.dash.refi_calculator_dash import update_data_stores
    result = update_data_stores(...)
    return parse_dash_result(result)

def get_api_output(inputs, client):
    """Call API endpoint"""
    response = client.post('/api/calculator/compute', json=inputs)
    return response.json

class TestDashAPIParity:
    def test_scalar_values_match(self, client):
        dash_out = get_dash_output(FIXTURE_STANDARD['inputs'])
        api_out = get_api_output(FIXTURE_STANDARD['inputs'], client)

        # Must match within 1 cent
        assert abs(dash_out['original_monthly_payment'] - api_out['original_monthly_payment']) < 0.01

    @pytest.mark.parametrize("fixture", ALL_FIXTURES)
    def test_all_fixtures_match(self, client, fixture):
        """Every fixture must produce identical results"""
        dash_out = get_dash_output(fixture['inputs'])
        api_out = get_api_output(fixture['inputs'], client)
        # Compare all values...
```

**Run:**
```bash
pytest tests/regression/test_parity.py -v
```

**TEST GATE:** ✅ 100% parity (< $0.01 difference) before Phase 2

---

## 📅 PHASE 2: React Frontend with Component Tests (Week 2-3 - 4 days)

**Goal:** Build React UI that displays API data correctly

### 2.1 Setup React Project (Day 9)

**Tasks:**
- [ ] Create Vite + React + TypeScript project
- [ ] Install dependencies
- [ ] Configure build to output to Flask static directory
- [ ] Setup Vitest for testing

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-plotly.js plotly.js axios
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

**Configure:** `frontend/vite.config.ts`

```typescript
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../refi_monitor/static/dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
  },
})
```

---

### 2.2 Create React Component Tests FIRST (Day 9-10)

**TDD for React components**

**Create:** `frontend/src/components/Calculator/__tests__/Calculator.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Calculator } from '../Calculator';

describe('Calculator', () => {
  it('renders input section on mount', () => {
    render(<Calculator />);
    expect(screen.getByText('Refinancing Info')).toBeInTheDocument();
  });

  it('calls API on mount', async () => {
    const mockAPI = vi.fn().mockResolvedValue({...});
    render(<Calculator />);
    await waitFor(() => expect(mockAPI).toHaveBeenCalled());
  });

  it('displays correct values after API response', async () => {
    render(<Calculator />);
    await waitFor(() => {
      expect(screen.getByText(/\$2,026.74/)).toBeInTheDocument();
    });
  });
});
```

**Tests WILL FAIL** (components not built yet)

---

### 2.3 Implement React Components (Day 10-12)

**Tasks:**
- [ ] Create TypeScript types
- [ ] Create API client
- [ ] Create useCalculator hook
- [ ] Create InputSection component
- [ ] Create SummaryTable component
- [ ] Create Calculator container

**Watch mode:**
```bash
npm test -- --watch
```

**Build components until tests pass**

**TEST GATE:** ✅ All component tests passing before Phase 3

---

## 📅 PHASE 3: Chart Components (Week 3 - 3 days)

### 3.1 Chart Component Tests (Day 13)

**Create tests for each chart:**
- `PaymentChart.test.tsx`
- `BreakevenChart.test.tsx`
- `EfficientFrontierChart.test.tsx`
- `PayoffScenarioChart.test.tsx`

---

### 3.2 Implement Charts (Day 13-15)

**Tasks:**
- [ ] Build PaymentChart with react-plotly.js
- [ ] Build BreakevenChart
- [ ] Build EfficientFrontierChart
- [ ] Build PayoffScenarioChart

**TEST GATE:** ✅ All chart tests passing before Phase 4

---

## 📅 PHASE 4: Integration & Deployment (Week 4 - 4 days)

### 4.1 Flask Integration (Day 16)

**Tasks:**
- [ ] Create Flask route to serve React SPA
- [ ] Remove Dash initialization
- [ ] Register API blueprint
- [ ] Add CORS for development

---

### 4.2 E2E Tests (Day 16-17)

**Create:** `tests/e2e/test_complete_flow.py`

```python
"""End-to-end tests with Selenium"""
def test_calculator_flow(browser):
    browser.get('http://localhost:5000/calculator/')
    # Enter values, wait for results, verify output
```

---

### 4.3 Performance Tests (Day 17)

**Create:** `tests/performance/test_api_performance.py`

```python
def test_api_response_time(client):
    """API must respond in < 500ms"""
    start = time.time()
    response = client.post('/api/calculator/compute', json={...})
    assert time.time() - start < 0.5
```

---

### 4.4 Final Validation (Day 18-19)

**Complete Test Suite:**
```bash
# All backend tests
pytest tests/ -v --cov=refi_monitor --cov-report=html

# All frontend tests
cd frontend && npm test

# E2E tests
pytest tests/e2e/

# Performance tests
pytest tests/performance/
```

**Manual QA:**
- [ ] Test all 5 fixtures manually
- [ ] Cross-browser testing
- [ ] Mobile testing
- [ ] Accessibility testing

---

### 4.5 Deployment (Day 20)

**Tasks:**
- [ ] Update Procfile
- [ ] Configure Heroku buildpacks
- [ ] Deploy to production
- [ ] Run smoke tests
- [ ] Monitor for errors

---

## 🎯 Success Metrics

Migration successful when:

✅ **100% unit test coverage** on calc.py
✅ **100% API tests pass**
✅ **100% regression tests pass** (Dash vs API < $0.01)
✅ **100% React component tests pass**
✅ **100% chart tests pass**
✅ **E2E tests pass**
✅ **Performance: API < 500ms** (5-10x faster than Dash)
✅ **All 5 fixtures** produce expected outputs
✅ **Zero calculation differences** between old and new
✅ **Manual QA passed**

---

## 📊 Test Summary

| Test Type | Count | Purpose | Gate |
|-----------|-------|---------|------|
| Unit (calc.py) | 50+ | Calculation accuracy | Phase 0 → 1 |
| API Contract | 30+ | API behavior | Phase 1 → 2 |
| Regression | 10 | Dash/API parity | Phase 1 → 2 |
| Component | 20+ | React UI | Phase 2 → 3 |
| Chart | 12 | Visualizations | Phase 3 → 4 |
| E2E | 5 | Full flow | Phase 4 done |
| Performance | 5 | Speed | Phase 4 done |
| **TOTAL** | **130+** | **Full coverage** | **Complete** |

---

## ⏱️ Timeline

| Phase | Days | Deliverables | Gate |
|-------|------|--------------|------|
| Phase 0 | 5 | Test infrastructure, baseline | Unit tests pass |
| Phase 1 | 3 | API endpoints | Regression pass |
| Phase 2 | 4 | React components | Component tests pass |
| Phase 3 | 3 | Charts | Chart tests pass |
| Phase 4 | 4 | Deployment | E2E pass |
| **TOTAL** | **19** | **Migration complete** | **All tests pass** |

---

## 🚀 Next Steps

1. ✅ Review and approve this plan
2. ✅ Create GitLab epics and issues
3. Start Phase 0, Task 0.1

**Ready to create GitLab issues?**
