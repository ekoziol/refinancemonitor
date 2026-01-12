# Financial Logic & Calculations Review

Review this code for correctness in mortgage calculations and financial logic.

## Critical Checks

### Calculation Accuracy
- [ ] Formulas match industry-standard mortgage calculations
- [ ] Interest rate conversions correct (APR vs monthly rate)
- [ ] Payment schedules account for amortization properly
- [ ] Rounding applied at correct precision points

### Edge Cases
- [ ] Zero or negative rates handled
- [ ] Zero principal amount handled
- [ ] Maximum term lengths validated
- [ ] Division by zero prevented
- [ ] Overflow protection for large amounts

### Precision & Currency
- [ ] Using Decimal for currency, not float
- [ ] Rounding to cents at appropriate points
- [ ] Consistent precision across calculations
- [ ] No floating-point comparison for equality

### Business Logic
- [ ] Refinance savings calculated correctly
- [ ] Break-even analysis accounts for closing costs
- [ ] Rate comparisons use consistent terms
- [ ] Assumptions clearly documented

## Questions to Answer

1. Would a mortgage professional agree this calculation is correct?
2. What happens with extreme values (0.001% rate, $10M loan)?
3. Are all the assumptions in this calculation documented?
4. Is the precision appropriate for the use case?

## Red Flags

- Using `float` for currency amounts
- `rate / 12` without confirming rate is annual
- Missing validation on input ranges
- Comparing floats with `==`
- Hardcoded rates or terms
- Complex calculations without unit tests

## Key Formulas Reference

```python
# Monthly payment (standard amortization)
monthly_rate = annual_rate / 12
n_payments = years * 12
payment = principal * (monthly_rate * (1 + monthly_rate)**n_payments) /
          ((1 + monthly_rate)**n_payments - 1)

# Total interest over life of loan
total_paid = payment * n_payments
total_interest = total_paid - principal

# Refinance savings (simplified)
monthly_savings = old_payment - new_payment
break_even_months = closing_costs / monthly_savings
```

## Testing Requirements

- [ ] Unit tests for core calculations
- [ ] Edge case tests (boundary values)
- [ ] Comparison against known-good values
- [ ] Property-based tests for invariants
