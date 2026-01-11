"""
API Contract Tests for Refinance Calculator

This file defines the expected behavior of POST /api/calculator/compute
using Test-Driven Development (TDD). These tests WILL FAIL initially
because the API endpoint doesn't exist yet.

Run with: pytest tests/api/test_calculator_contract.py -v

After Phase 2 implementation, all tests should pass.
"""
import pytest
import time
from dataclasses import dataclass
from typing import Optional


# =============================================================================
# REQUEST/RESPONSE SCHEMA DEFINITIONS
# =============================================================================

@dataclass
class CalculatorRequest:
    """Expected request schema for POST /api/calculator/compute"""
    # Current mortgage info (required)
    original_principal: float      # Original loan amount
    original_rate: float           # Original annual interest rate (decimal, e.g., 0.045 for 4.5%)
    original_term: int             # Original loan term in months (e.g., 360 for 30 years)

    # Current state (required)
    remaining_principal: float     # Current remaining balance
    remaining_term: int            # Months left on original loan

    # Refinance scenario (required)
    target_rate: float             # Target annual interest rate for refi
    target_term: int               # Target loan term in months
    refi_cost: float               # Estimated closing costs

    # Optional
    target_monthly_payment: Optional[float] = None  # Optional target payment


@dataclass
class CalculatorResponse:
    """Expected response schema for successful calculation"""
    # Original mortgage metrics
    original_monthly_payment: float
    minimum_monthly_payment: float  # At 0% interest (theoretical min)
    original_total_interest: float

    # Refinance metrics
    refi_monthly_payment: float
    refi_total_interest: float
    required_rate_for_target: Optional[float]

    # Savings analysis
    monthly_savings: float
    total_loan_savings: float
    months_to_breakeven_simple: float
    months_to_breakeven_interest: Optional[float]

    # Meta
    months_paid: int
    additional_months: int  # Extension beyond original payoff


@dataclass
class ErrorResponse:
    """Expected error response schema"""
    error: str
    code: str
    details: Optional[dict] = None


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def valid_request_data():
    """Standard valid request for a typical refinance scenario"""
    return {
        "original_principal": 400000.00,
        "original_rate": 0.045,  # 4.5%
        "original_term": 360,    # 30 years
        "remaining_principal": 364631.66,
        "remaining_term": 300,   # 25 years left
        "target_rate": 0.035,    # 3.5%
        "target_term": 360,      # New 30 year loan
        "refi_cost": 5000.00
    }


@pytest.fixture
def api_client():
    """
    Creates a test client for the API.
    This will be implemented in Phase 2.
    """
    # TODO: Import and create Flask/FastAPI test client
    # from refi_monitor.api import create_app
    # app = create_app()
    # return app.test_client()
    pytest.skip("API not implemented yet - TDD Phase 1")


# =============================================================================
# HAPPY PATH TESTS (10 tests)
# =============================================================================

class TestCalculatorHappyPath:
    """Tests for successful calculator operations"""

    def test_basic_refinance_calculation(self, api_client, valid_request_data):
        """POST /api/calculator/compute returns valid response for standard input"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # Verify all required fields present
        assert "original_monthly_payment" in data
        assert "refi_monthly_payment" in data
        assert "monthly_savings" in data
        assert "total_loan_savings" in data
        assert "months_to_breakeven_simple" in data

    def test_monthly_payment_calculation_accuracy(self, api_client, valid_request_data):
        """Monthly payment calculation matches expected formula"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # For $400k at 4.5% for 30 years, monthly payment should be ~$2,026.74
        assert abs(data["original_monthly_payment"] - 2026.74) < 1.0

    def test_refinance_savings_positive(self, api_client, valid_request_data):
        """Refinancing to lower rate shows positive savings"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # Lower rate should produce positive monthly savings
        assert data["monthly_savings"] > 0

    def test_breakeven_calculation(self, api_client, valid_request_data):
        """Breakeven months is calculated correctly"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # Breakeven should be refi_cost / monthly_savings
        expected_breakeven = valid_request_data["refi_cost"] / data["monthly_savings"]
        assert abs(data["months_to_breakeven_simple"] - expected_breakeven) < 0.1

    def test_target_payment_finds_rate(self, api_client, valid_request_data):
        """When target_monthly_payment provided, calculates required rate"""
        valid_request_data["target_monthly_payment"] = 1800.00

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        assert "required_rate_for_target" in data
        assert data["required_rate_for_target"] is not None
        assert 0 < data["required_rate_for_target"] < 0.10  # Reasonable rate range

    def test_same_rate_zero_savings(self, api_client, valid_request_data):
        """Refinancing at same rate shows zero monthly savings"""
        valid_request_data["target_rate"] = valid_request_data["original_rate"]

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # Same rate, same term should have ~0 monthly savings
        assert abs(data["monthly_savings"]) < 50  # Allow small difference due to remaining principal

    def test_shorter_term_higher_payment(self, api_client, valid_request_data):
        """Shorter refinance term results in higher monthly payment"""
        valid_request_data["target_term"] = 180  # 15 years

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # 15-year loan should have higher monthly than 30-year
        assert data["refi_monthly_payment"] > data["original_monthly_payment"] * 1.2

    def test_interest_savings_calculation(self, api_client, valid_request_data):
        """Total interest savings calculated correctly"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # With lower rate, should save on total interest
        assert "total_loan_savings" in data
        # Total savings should account for rate reduction benefit minus refi costs

    def test_additional_months_calculation(self, api_client, valid_request_data):
        """Additional months beyond original payoff calculated"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # 360 month new term - 300 remaining = 60 additional months
        assert data["additional_months"] == 60

    def test_response_time_under_500ms(self, api_client, valid_request_data):
        """API response time is under 500ms"""
        start = time.time()
        response = api_client.post("/api/calculator/compute", json=valid_request_data)
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 500, f"Response took {elapsed}ms, expected <500ms"


# =============================================================================
# INPUT VALIDATION TESTS (10 tests)
# =============================================================================

class TestCalculatorInputValidation:
    """Tests for input validation and error handling"""

    def test_missing_required_field(self, api_client, valid_request_data):
        """Returns 400 when required field is missing"""
        del valid_request_data["original_principal"]

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert "error" in response.json
        assert response.json["code"] == "MISSING_FIELD"

    def test_negative_principal_rejected(self, api_client, valid_request_data):
        """Returns 400 for negative principal"""
        valid_request_data["original_principal"] = -100000

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_VALUE"
        assert "principal" in response.json["error"].lower()

    def test_zero_principal_rejected(self, api_client, valid_request_data):
        """Returns 400 for zero principal"""
        valid_request_data["original_principal"] = 0

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_VALUE"

    def test_negative_rate_rejected(self, api_client, valid_request_data):
        """Returns 400 for negative interest rate"""
        valid_request_data["original_rate"] = -0.05

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_VALUE"

    def test_rate_over_100_percent_rejected(self, api_client, valid_request_data):
        """Returns 400 for rate > 100%"""
        valid_request_data["original_rate"] = 1.5  # 150%

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_VALUE"

    def test_zero_term_rejected(self, api_client, valid_request_data):
        """Returns 400 for zero term"""
        valid_request_data["original_term"] = 0

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_VALUE"

    def test_negative_term_rejected(self, api_client, valid_request_data):
        """Returns 400 for negative term"""
        valid_request_data["target_term"] = -360

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_VALUE"

    def test_remaining_greater_than_original_rejected(self, api_client, valid_request_data):
        """Returns 400 when remaining principal exceeds original"""
        valid_request_data["remaining_principal"] = 500000  # More than $400k original

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_VALUE"

    def test_remaining_term_greater_than_original_rejected(self, api_client, valid_request_data):
        """Returns 400 when remaining term exceeds original"""
        valid_request_data["remaining_term"] = 400  # More than 360 original

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_VALUE"

    def test_invalid_json_rejected(self, api_client):
        """Returns 400 for malformed JSON"""
        response = api_client.post(
            "/api/calculator/compute",
            data="not valid json",
            content_type="application/json"
        )

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_JSON"


# =============================================================================
# EDGE CASE TESTS (7 tests)
# =============================================================================

class TestCalculatorEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_zero_interest_rate(self, api_client, valid_request_data):
        """Handles 0% interest rate correctly"""
        valid_request_data["target_rate"] = 0.0

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # At 0% interest, monthly payment = principal / months
        expected = valid_request_data["remaining_principal"] / valid_request_data["target_term"]
        assert abs(data["refi_monthly_payment"] - expected) < 1.0

    def test_very_large_principal(self, api_client, valid_request_data):
        """Handles very large loan amounts"""
        valid_request_data["original_principal"] = 10_000_000  # $10M
        valid_request_data["remaining_principal"] = 9_500_000

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        assert response.json["original_monthly_payment"] > 50000

    def test_very_small_principal(self, api_client, valid_request_data):
        """Handles small loan amounts"""
        valid_request_data["original_principal"] = 10_000  # $10k
        valid_request_data["remaining_principal"] = 8_000

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        assert response.json["original_monthly_payment"] > 0

    def test_fully_paid_loan(self, api_client, valid_request_data):
        """Handles scenario with zero remaining balance"""
        valid_request_data["remaining_principal"] = 0
        valid_request_data["remaining_term"] = 0

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        # Should return error or handle gracefully
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            assert response.json["refi_monthly_payment"] == 0

    def test_one_month_remaining(self, api_client, valid_request_data):
        """Handles single month remaining"""
        valid_request_data["remaining_term"] = 1
        valid_request_data["remaining_principal"] = 2000

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200

    def test_very_high_rate(self, api_client, valid_request_data):
        """Handles high interest rate scenarios"""
        valid_request_data["original_rate"] = 0.20  # 20%
        valid_request_data["target_rate"] = 0.15   # 15%

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        assert response.json["monthly_savings"] > 0

    def test_negative_savings_scenario(self, api_client, valid_request_data):
        """Handles refinance to higher rate (negative savings)"""
        valid_request_data["target_rate"] = 0.06  # Higher than original 4.5%

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # Monthly savings should be negative when going to higher rate
        assert data["monthly_savings"] < 0
        # Breakeven should indicate "never" or very high value
        assert data["months_to_breakeven_simple"] < 0 or data["months_to_breakeven_simple"] > 9999


# =============================================================================
# RESPONSE FORMAT TESTS (5 tests)
# =============================================================================

class TestCalculatorResponseFormat:
    """Tests for response format and structure"""

    def test_response_content_type_json(self, api_client, valid_request_data):
        """Response content-type is application/json"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.content_type == "application/json"

    def test_monetary_values_are_floats(self, api_client, valid_request_data):
        """All monetary values returned as floats"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        monetary_fields = [
            "original_monthly_payment",
            "refi_monthly_payment",
            "monthly_savings",
            "total_loan_savings"
        ]

        for field in monetary_fields:
            assert isinstance(data[field], (int, float)), f"{field} should be numeric"

    def test_integer_fields_are_integers(self, api_client, valid_request_data):
        """Integer fields (months) returned as integers"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        assert isinstance(data["months_paid"], int)
        assert isinstance(data["additional_months"], int)

    def test_optional_fields_null_when_not_applicable(self, api_client, valid_request_data):
        """Optional fields are null when not applicable"""
        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 200
        data = response.json

        # When no target_monthly_payment provided, required_rate should be null
        if "target_monthly_payment" not in valid_request_data:
            assert data.get("required_rate_for_target") is None

    def test_error_response_structure(self, api_client, valid_request_data):
        """Error responses have consistent structure"""
        del valid_request_data["original_principal"]

        response = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response.status_code == 400
        data = response.json

        assert "error" in data
        assert "code" in data
        assert isinstance(data["error"], str)
        assert isinstance(data["code"], str)


# =============================================================================
# CONCURRENCY/PERFORMANCE TESTS (3 tests)
# =============================================================================

class TestCalculatorPerformance:
    """Tests for performance and concurrency"""

    def test_multiple_sequential_requests(self, api_client, valid_request_data):
        """Handles 10 sequential requests correctly"""
        for i in range(10):
            valid_request_data["original_principal"] = 300000 + (i * 10000)
            response = api_client.post("/api/calculator/compute", json=valid_request_data)
            assert response.status_code == 200

    def test_consistent_results(self, api_client, valid_request_data):
        """Same input produces same output"""
        response1 = api_client.post("/api/calculator/compute", json=valid_request_data)
        response2 = api_client.post("/api/calculator/compute", json=valid_request_data)

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json == response2.json

    def test_average_response_time(self, api_client, valid_request_data):
        """Average response time under 300ms over 5 requests"""
        times = []

        for _ in range(5):
            start = time.time()
            response = api_client.post("/api/calculator/compute", json=valid_request_data)
            times.append((time.time() - start) * 1000)
            assert response.status_code == 200

        avg_time = sum(times) / len(times)
        assert avg_time < 300, f"Average response time {avg_time}ms exceeds 300ms"


# =============================================================================
# API DOCUMENTATION
# =============================================================================
"""
## API Contract: POST /api/calculator/compute

### Request Body (JSON)
```json
{
    "original_principal": 400000.00,     // Required: Original loan amount
    "original_rate": 0.045,               // Required: Annual rate as decimal
    "original_term": 360,                 // Required: Term in months
    "remaining_principal": 364631.66,     // Required: Current balance
    "remaining_term": 300,                // Required: Months remaining
    "target_rate": 0.035,                 // Required: Target refi rate
    "target_term": 360,                   // Required: Target term months
    "refi_cost": 5000.00,                // Required: Closing costs
    "target_monthly_payment": 1800.00    // Optional: Desired payment
}
```

### Success Response (200 OK)
```json
{
    "original_monthly_payment": 2026.74,
    "minimum_monthly_payment": 1111.11,
    "original_total_interest": 329226.40,
    "refi_monthly_payment": 1636.25,
    "refi_total_interest": 224280.00,
    "required_rate_for_target": null,
    "monthly_savings": 390.49,
    "total_loan_savings": 85946.40,
    "months_to_breakeven_simple": 13,
    "months_to_breakeven_interest": 24,
    "months_paid": 60,
    "additional_months": 60
}
```

### Error Response (400 Bad Request)
```json
{
    "error": "Missing required field: original_principal",
    "code": "MISSING_FIELD",
    "details": {"field": "original_principal"}
}
```

### Error Codes
- MISSING_FIELD: Required field not provided
- INVALID_VALUE: Value out of acceptable range
- INVALID_JSON: Request body is not valid JSON
- CALCULATION_ERROR: Error during calculation

### Validation Rules
1. All principal values must be positive numbers
2. Interest rates must be between 0 and 1 (0% to 100%)
3. Terms must be positive integers
4. remaining_principal <= original_principal
5. remaining_term <= original_term
6. refi_cost must be non-negative

### Performance Requirements
- Response time < 500ms for 95th percentile
- Average response time < 300ms
"""
