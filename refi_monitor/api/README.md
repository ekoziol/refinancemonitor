# Calculator API

REST API for refinance calculations, mirroring the Dash calculator functionality.

## Base URL

```
/api
```

## Endpoints

### Health Check

```
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "calculator-api"
}
```

---

### Full Calculator

```
POST /api/calculate
```

Main endpoint that performs all refinance calculations.

**Request Body:**
```json
{
  "current_principal": 400000,
  "current_rate": 0.045,
  "current_term": 360,
  "target_rate": 0.035,
  "target_term": 360,
  "refi_cost": 5000,
  "remaining_term": 300,
  "remaining_principal": 364631.66
}
```

| Field | Type | Description |
|-------|------|-------------|
| current_principal | float | Original loan principal |
| current_rate | float | Original interest rate (decimal, e.g., 0.045 = 4.5%) |
| current_term | int | Original term in months |
| target_rate | float | Target refinance rate (decimal) |
| target_term | int | Target refinance term in months |
| refi_cost | float | Refinancing costs |
| remaining_term | int | Remaining months on current loan |
| remaining_principal | float | Current remaining principal |

**Response:**
```json
{
  "original_monthly_payment": 2026.74,
  "minimum_monthly_payment": 1111.11,
  "monthly_savings": 389.38,
  "total_loan_savings": 85000.00,
  "months_paid": 60,
  "original_interest": 329625.29,
  "refi_monthly_payment": 1637.36,
  "refi_interest": 225000.00,
  "month_to_even_simple": 13,
  "month_to_even_interest": 45,
  "target_rate": 0.035
}
```

---

### Monthly Payment

```
POST /api/monthly-payment
```

Calculate monthly payment for a loan.

**Request Body:**
```json
{
  "principal": 400000,
  "rate": 0.045,
  "term": 360
}
```

**Response:**
```json
{
  "monthly_payment": 2026.74,
  "principal": 400000,
  "rate": 0.045,
  "term": 360
}
```

---

### Find Rate

```
POST /api/find-rate
```

Find interest rate needed for a target monthly payment.

**Request Body:**
```json
{
  "principal": 364631.66,
  "term": 360,
  "target_payment": 1637.87
}
```

**Response:**
```json
{
  "target_rate": 0.035,
  "target_rate_percent": 3.5,
  "principal": 364631.66,
  "term": 360,
  "target_payment": 1637.87
}
```

---

### Total Interest

```
POST /api/total-interest
```

Calculate total interest over life of loan.

**Request Body:**
```json
{
  "principal": 400000,
  "rate": 0.045,
  "term": 360
}
```

**Response:**
```json
{
  "total_interest": 329625.29,
  "principal": 400000,
  "rate": 0.045,
  "term": 360
}
```

---

### Breakeven

```
POST /api/breakeven
```

Calculate months to break even on refinance costs.

**Request Body:**
```json
{
  "refi_cost": 5000,
  "monthly_savings": 388.87
}
```

**Response:**
```json
{
  "months_to_breakeven": 13,
  "refi_cost": 5000,
  "monthly_savings": 388.87
}
```

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "error": "Missing required fields: [field_name]"
}
```

HTTP status codes:
- `200` - Success
- `400` - Bad request (missing/invalid fields)
- `500` - Server error

---

## Parity with Dash

All calculations match the Dash calculator output within `$0.01` tolerance.

Test coverage:
- 22 parity tests passing
- Monthly payment calculations
- Total interest calculations
- Breakeven calculations
- Full refinance scenarios
- Edge cases (0% rate, high rates, short terms)

Run tests:
```bash
python3 tests/verify_parity_simple.py
```
