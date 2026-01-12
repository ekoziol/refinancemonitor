# RefiAlert Email Report Templates

## Overview

This document compiles the complete template set for RefiAlert email reports, including sample data, multiple scenarios, and template variations for user review.

---

## Sample User Profile Data

### User: Sarah Johnson
```
Name: Sarah Johnson
Email: sarah.johnson@example.com
Credit Score: 760
Account Created: June 2023
```

### Mortgage: "Primary Residence - Oak Street"
```
Original Principal:      $450,000
Original Term:           360 months (30 years)
Original Interest Rate:  6.875%
Origination Date:        March 2023

Current Remaining Principal: $438,500
Remaining Term:              336 months (28 years)
Current Monthly Payment:     $2,955.89 (P&I only)
```

### Alert Configuration
```
Alert Type:              Break-even Analysis
Target Term:             360 months (30 years)
Estimated Refi Cost:     $8,500
Target Monthly Payment:  $2,650 (desired)
Target Interest Rate:    5.875% (desired)
```

### Current Market Rates (Sample Data)
```
30-Year Fixed:  6.125% (-0.125 from yesterday)
15-Year Fixed:  5.375%
5/1 ARM:        5.625%
FHA 30:         5.875%
VA 30:          5.750%
```

---

## Scenario 1: SHOULD REFI (Strong Recommendation)

### Trigger Conditions
- Current market rate: 5.625% (30-year fixed)
- Rate drop: 1.25% below original rate
- Break-even period: 18 months
- Total savings over remaining term: $67,200
- Monthly savings: $285/month

### Email Template: Should Refi

```
Subject: RefiAlert: Time to Refinance Your Oak Street Mortgage!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                        REFI ALERT
              Your Refinancing Opportunity is Here

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi Sarah,

Great news! Based on today's mortgage rates, NOW is an excellent
time to refinance your Oak Street mortgage.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    YOUR OPPORTUNITY AT A GLANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  RECOMMENDATION:  REFINANCE NOW

  Current Rate:      6.875%
  Available Rate:    5.625%  (↓ 1.25%)

  Current Payment:   $2,955.89/mo
  New Payment:       $2,670.57/mo
  ─────────────────────────────────
  Monthly Savings:   $285.32/mo

  Break-even Point:  18 months

  TOTAL LIFETIME SAVINGS: $67,200

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    DETAILED ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR CURRENT MORTGAGE
┌─────────────────────────────┬──────────────────┐
│ Remaining Balance           │ $438,500         │
│ Current Interest Rate       │ 6.875%           │
│ Remaining Term              │ 28 years         │
│ Monthly Payment (P&I)       │ $2,955.89        │
│ Total Interest Remaining    │ $248,670         │
└─────────────────────────────┴──────────────────┘

PROPOSED REFINANCE
┌─────────────────────────────┬──────────────────┐
│ New Loan Amount             │ $438,500         │
│ New Interest Rate           │ 5.625%           │
│ New Term                    │ 30 years         │
│ New Monthly Payment (P&I)   │ $2,670.57        │
│ Total Interest (New Loan)   │ $181,470         │
│ Closing Costs               │ $8,500           │
└─────────────────────────────┴──────────────────┘

SAVINGS BREAKDOWN
┌─────────────────────────────┬──────────────────┐
│ Monthly Payment Reduction   │ $285.32          │
│ Annual Savings              │ $3,424           │
│ Break-even Period           │ 18 months        │
│ Net Interest Savings        │ $67,200          │
│ Total Lifetime Savings      │ $58,700*         │
└─────────────────────────────┴──────────────────┘
*After accounting for closing costs and term extension

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    WHY NOW?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ Rates are 1.25% LOWER than your current rate
  ✓ Your break-even point is just 18 months
  ✓ You plan to stay in your home long-term
  ✓ Your credit score (760) qualifies for best rates
  ✓ You have sufficient equity (approximately 25%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Compare offers from multiple lenders (we recommend 3-5)
  2. Lock your rate quickly - rates can change daily
  3. Gather documents: pay stubs, tax returns, bank statements
  4. Schedule appraisal if required
  5. Review closing disclosure carefully before signing

  Rate Lock Tip: Today's rate of 5.625% may not last. Consider
  locking within 24-48 hours if you decide to proceed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    TODAY'S MARKET RATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  30-Year Fixed:  5.625%  ↓ 0.125
  15-Year Fixed:  5.375%  ↓ 0.125
  5/1 ARM:        5.625%  ━ 0.000

  Source: MortgageNewsDaily | Updated: January 11, 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions? Reply to this email or log in to your RefiAlert
dashboard to see more details and run custom scenarios.

Happy Saving,
The RefiAlert Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RefiAlert | Your Automated Refinance Monitor
Manage Alerts: https://refialert.com/dashboard
Unsubscribe: https://refialert.com/unsubscribe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated alert based on your configured preferences.
Not financial advice. Consult a licensed mortgage professional.
```

---

## Scenario 2: SHOULD WAIT (Not Yet Favorable)

### Trigger Conditions
- Current market rate: 6.50% (30-year fixed)
- Rate drop: Only 0.375% below original rate
- Break-even period: 48+ months
- Marginal monthly savings: $85/month
- Would extend loan term significantly

### Email Template: Should Wait

```
Subject: RefiAlert Update: Oak Street Mortgage - Hold Steady

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                        REFI ALERT
                    Monthly Rate Update

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi Sarah,

Here's your monthly refinancing analysis for Oak Street.
While rates have improved slightly, we recommend waiting for
a better opportunity.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    YOUR STATUS AT A GLANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  RECOMMENDATION:  WAIT FOR BETTER RATES

  Current Rate:      6.875%
  Available Rate:    6.500%  (↓ 0.375%)

  Current Payment:   $2,955.89/mo
  Potential Payment: $2,870.24/mo
  ─────────────────────────────────
  Potential Savings: $85.65/mo

  Break-even Point:  48+ months (too long)

  WHY WAIT: The savings don't justify the costs yet.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    THE MATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CURRENT vs. POTENTIAL REFINANCE
┌─────────────────────┬─────────────┬─────────────┐
│                     │ Current     │ If You Refi │
├─────────────────────┼─────────────┼─────────────┤
│ Interest Rate       │ 6.875%      │ 6.500%      │
│ Monthly Payment     │ $2,955.89   │ $2,870.24   │
│ Monthly Savings     │ --          │ $85.65      │
│ Closing Costs       │ --          │ $8,500      │
│ Break-even          │ --          │ 99 months   │
└─────────────────────┴─────────────┴─────────────┘

ANALYSIS

  The numbers don't work in your favor right now:

  • Monthly savings of $85.65 are modest
  • Break-even period of 99 months (8+ years) is too long
  • You'd reset your loan to 30 years, paying more total interest
  • Risk of rates dropping further (potential buyer's remorse)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    WHEN SHOULD YOU REFI?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on your alert settings, we'll notify you when:

  Target Rate Reached:
  ┌────────────────────────────────────────────────┐
  │                                                │
  │   Current: 6.500%  ─────●───────── 5.875%     │
  │                    ▲              ▲            │
  │                  Today          Target        │
  │                                                │
  │   Rates need to drop another 0.625% to hit    │
  │   your target of 5.875%                       │
  │                                                │
  └────────────────────────────────────────────────┘

  OR when break-even period drops below 24 months

  Your alert is active and monitoring daily.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    MARKET OUTLOOK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  30-Day Trend:   ↓ Rates down 0.25%
  90-Day Trend:   ↓ Rates down 0.50%

  Fed Activity:   Next meeting Feb 15, 2026
  Market View:    Analysts expect continued gradual decline

  What this means: Patience may be rewarded. We're watching
  closely and will alert you immediately when conditions improve.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    TODAY'S RATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  30-Year Fixed:  6.500%  ↓ 0.125
  15-Year Fixed:  5.875%  ↓ 0.125
  5/1 ARM:        6.125%  ━ 0.000

  Source: MortgageNewsDaily | Updated: January 11, 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sit tight - we're watching the market for you.

The RefiAlert Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RefiAlert | Your Automated Refinance Monitor
Manage Alerts: https://refialert.com/dashboard
Unsubscribe: https://refialert.com/unsubscribe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated update based on your configured preferences.
Not financial advice. Consult a licensed mortgage professional.
```

---

## Scenario 3: NEUTRAL (Borderline Case)

### Trigger Conditions
- Current market rate: 6.00% (30-year fixed)
- Rate drop: 0.875% below original rate
- Break-even period: 26 months
- Monthly savings: $175/month
- Depends on user's specific plans

### Email Template: Neutral/Consider

```
Subject: RefiAlert: Oak Street Mortgage - Worth Considering

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                        REFI ALERT
                   Decision Point Reached

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi Sarah,

Rates have improved to a point where refinancing your Oak Street
mortgage is worth serious consideration. Here's the analysis.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    YOUR OPPORTUNITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  RECOMMENDATION:  CONSIDER REFINANCING

  Current Rate:      6.875%
  Available Rate:    6.000%  (↓ 0.875%)

  Current Payment:   $2,955.89/mo
  New Payment:       $2,780.16/mo
  ─────────────────────────────────
  Monthly Savings:   $175.73/mo

  Break-even Point:  26 months

  THIS IS A BORDERLINE CASE - Your decision depends on
  your specific situation and plans.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    FACTORS TO CONSIDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REASONS TO REFINANCE NOW
┌────────────────────────────────────────────────────────────────┐
│ ✓ You plan to stay in your home 3+ more years                 │
│ ✓ You want lower monthly payments immediately                 │
│ ✓ You're concerned rates might rise again                     │
│ ✓ You want to lock in savings now vs. waiting                 │
│ ✓ You have cash available for closing costs                   │
└────────────────────────────────────────────────────────────────┘

REASONS TO WAIT
┌────────────────────────────────────────────────────────────────┐
│ ○ You might sell within 2 years (won't recoup costs)          │
│ ○ Rates may continue declining (Fed signals more cuts)        │
│ ○ You'd rather not extend your loan term                      │
│ ○ 26-month break-even feels too long for you                  │
│ ○ You'd prefer to save cash for other priorities              │
└────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    TWO SCENARIOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO A: Refinance to New 30-Year Loan
┌─────────────────────────────┬──────────────────┐
│ New Rate                    │ 6.000%           │
│ New Payment                 │ $2,780.16/mo     │
│ Monthly Savings             │ $175.73          │
│ Break-even                  │ 26 months        │
│ Total Interest (New Loan)   │ $212,780         │
│ Closing Costs               │ $8,500           │
└─────────────────────────────┴──────────────────┘
  Note: Extends your loan by 2 years

SCENARIO B: Refinance to 20-Year Loan (Shorter Term)
┌─────────────────────────────┬──────────────────┐
│ New Rate                    │ 5.750%           │
│ New Payment                 │ $3,072.43/mo     │
│ Monthly Increase            │ +$116.54         │
│ Interest Savings            │ $95,400          │
│ Payoff                      │ 8 years sooner   │
│ Closing Costs               │ $8,500           │
└─────────────────────────────┴──────────────────┘
  Note: Higher payment but massive interest savings

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    WHAT'S YOUR TIMELINE?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your break-even point is 26 months. Here's what that means:

  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │  TODAY          26 MO          5 YR          10 YR       │
  │    │              │             │              │         │
  │    ▼              ▼             ▼              ▼         │
  │  ─────●──────────●────────────●─────────────●─────────  │
  │  Refi        Break-even    +$2,785       +$11,570       │
  │  Cost           Point       Saved          Saved        │
  │  -$8,500         $0                                     │
  │                                                          │
  └──────────────────────────────────────────────────────────┘

  • Stay less than 2 years: You'll lose money
  • Stay 2-3 years: Modest savings (~$1,500)
  • Stay 5+ years: Significant savings ($10,000+)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    OUR RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  If you're confident you'll stay 3+ years:
  → Consider refinancing now

  If you might move within 2-3 years:
  → Wait for rates to drop further

  If you're unsure:
  → Get quotes from 2-3 lenders (no commitment)
  → Compare actual offers to these estimates
  → Decide based on real numbers

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    TODAY'S RATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  30-Year Fixed:  6.000%  ↓ 0.125
  15-Year Fixed:  5.500%  ↓ 0.125
  20-Year Fixed:  5.750%  ↓ 0.125
  5/1 ARM:        5.875%  ━ 0.000

  Source: MortgageNewsDaily | Updated: January 11, 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions? Log in to run custom scenarios or reply to this email.

The RefiAlert Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RefiAlert | Your Automated Refinance Monitor
Manage Alerts: https://refialert.com/dashboard
Unsubscribe: https://refialert.com/unsubscribe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated analysis based on your configured preferences.
Not financial advice. Consult a licensed mortgage professional.
```

---

## Template Variation Comparison

### Variation A: Minimalist (Quick Summary)

Best for: Users who want quick, actionable information

```
Subject: RefiAlert: Oak Street - Refinance NOW (Save $285/mo)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  REFI ALERT: Action Recommended

  Your Mortgage:    Oak Street
  Current Rate:     6.875%
  Available Rate:   5.625%

  Monthly Savings:  $285.32
  Break-even:       18 months
  Lifetime Savings: $67,200

  RECOMMENDATION: REFINANCE NOW

  → Get quotes today: https://refialert.com/quotes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RefiAlert | Manage: https://refialert.com/dashboard
```

**Pros:**
- Fast to read
- Clear action item
- Mobile-friendly
- Reduces email fatigue

**Cons:**
- Lacks context for decision-making
- May seem impersonal
- No educational content

---

### Variation B: Detailed Analysis (Full Report)

Best for: Users who want comprehensive data

*See Scenario 1 template above - this is the detailed version*

**Pros:**
- Complete information for decision-making
- Educational content builds trust
- Professional presentation
- Shows value of premium service

**Cons:**
- Long; may not be fully read
- Can overwhelm some users
- Takes longer to process

---

### Variation C: Visual Dashboard Style

Best for: Users who respond to visual information

```
Subject: RefiAlert: Oak Street Analysis Ready

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

            YOUR REFI SCORE: 87/100

    ┌────────────────────────────────────────┐
    │████████████████████████████████░░░░░░░░│
    │ STRONG REFINANCE OPPORTUNITY           │
    └────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  RATE COMPARISON

  Your Rate    ████████████████████████  6.875%
  Market Rate  ██████████████████░░░░░░  5.625%
  Target Rate  █████████████████░░░░░░░  5.875%  ✓ MET

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  SAVINGS METER

  Monthly:   [$285] ████████████████████████████
  Yearly:    [$3,424] ███████████████████████████
  Lifetime:  [$67,200] █████████████████████████

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  BREAK-EVEN TIMELINE

  NOW ──●────────────●──────────────────── PAID OFF
        │            │
      Refi       Break-even
      Today       18 months

  ✓ Excellent: Under 24 months

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  KEY FACTORS              SCORE

  Rate Difference          ████████░░  8/10
  Break-even Period        █████████░  9/10
  Closing Costs            ███████░░░  7/10
  Equity Position          █████████░  9/10
  Credit Score             █████████░  9/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [VIEW FULL ANALYSIS] → https://refialert.com/report
  [GET LENDER QUOTES] → https://refialert.com/quotes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RefiAlert | Manage: https://refialert.com/dashboard
```

**Pros:**
- Engaging visual format
- Quick to scan
- Gamification element (score)
- Modern feel

**Cons:**
- ASCII charts may render differently in email clients
- Requires more testing across email platforms
- Score methodology needs explanation

---

### Variation D: Action-Oriented (Checklist Style)

Best for: Users who want guidance on next steps

```
Subject: RefiAlert: Oak Street - Your Refinance Action Plan

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi Sarah,

Great news! It's time to refinance Oak Street. Here's exactly
what to do:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  THE NUMBERS (Quick Summary)

  You'll save: $285/month | $67,200 total
  Break-even:  18 months
  Action:      REFINANCE NOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  YOUR ACTION CHECKLIST

  This Week:
  □ Compare offers from 3+ lenders
  □ Check your credit report for errors
  □ Decide: 30-year vs shorter term

  Documents to Gather:
  □ Last 2 years of tax returns
  □ Last 2 months of pay stubs
  □ Last 2 months of bank statements
  □ Current mortgage statement
  □ Homeowners insurance declaration page

  When You Apply:
  □ Lock your rate within 48 hours of approval
  □ Ask about float-down options
  □ Compare closing cost estimates
  □ Request seller credits if applicable

  At Closing:
  □ Review Closing Disclosure 3 days before
  □ Compare to Loan Estimate
  □ Wire funds from verified account

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PRO TIPS FOR BEST RATES

  1. Apply with 3-5 lenders on the SAME DAY
     (Multiple inquiries within 14 days count as one)

  2. Ask each lender for their "par rate"
     (Rate with zero points/credits)

  3. Negotiate! Lenders expect it.
     "I have a quote for 5.5% - can you match?"

  4. Watch for junk fees
     "Processing fee," "admin fee" - push back

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  FULL ANALYSIS → https://refialert.com/report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RefiAlert | We monitor. You save.
Manage Alerts: https://refialert.com/dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Pros:**
- Highly actionable
- Reduces anxiety with clear steps
- Educational (tips build trust)
- Saves users research time

**Cons:**
- May feel too long
- Checklist format is opinionated
- Some tips may not apply to all users

---

## Template Comparison Matrix

| Feature | A: Minimalist | B: Detailed | C: Visual | D: Action |
|---------|---------------|-------------|-----------|-----------|
| Length | Short | Long | Medium | Medium |
| Scan Time | 10 sec | 2-3 min | 30 sec | 1 min |
| Data Depth | Low | High | Medium | Medium |
| Actionability | High | Medium | Medium | Very High |
| Educational Value | Low | High | Medium | High |
| Mobile Friendly | Yes | Moderate | Moderate | Yes |
| Email Client Support | Excellent | Good | Variable | Good |
| Personal Feel | Low | Medium | Medium | High |

---

## Recommended Approach

### Primary Template Selection
We recommend using **Variation B (Detailed Analysis)** as the default template for triggered alerts because:
1. Justifies the premium subscription cost
2. Provides all information needed for decision-making
3. Builds trust through transparency
4. Reduces need for follow-up questions

### Supplementary Templates
- **Variation A (Minimalist)**: Use for SMS alerts or secondary notification
- **Variation C (Visual)**: Test with subset of users; potential A/B test candidate
- **Variation D (Action)**: Send as follow-up 24-48 hours after initial alert

### User Preference Option
Consider allowing users to select their preferred email format:
- Quick Summary (Minimalist)
- Full Analysis (Detailed)  [Default]
- Action Plan (Checklist)

---

## HTML Email Considerations

The text templates above would be converted to responsive HTML with:

1. **Header**: Logo, green brand color (#4CAF50)
2. **Hero Section**: Large recommendation text
3. **Data Tables**: Clean, alternating row colors
4. **CTA Buttons**: Prominent "Get Quotes" button
5. **Footer**: Unsubscribe link, social links, legal disclaimer

### Mobile Responsiveness
- Single-column layout for screens < 600px
- Larger touch targets for buttons (min 44x44px)
- Readable font sizes (min 14px body, 18px headers)
- Adequate spacing between sections

### Email Client Testing Required
- Gmail (Web, iOS, Android)
- Outlook (Desktop, Web, Mobile)
- Apple Mail (macOS, iOS)
- Yahoo Mail
- Dark mode support

---

## Next Steps for Implementation

1. **User Review**: Get feedback on template preference
2. **HTML Conversion**: Convert selected templates to responsive HTML
3. **A/B Testing**: Test variations to optimize engagement
4. **Integration**: Update `notifications.py` with new templates
5. **Personalization**: Add dynamic content based on user preferences
6. **Testing**: Validate across email clients and devices

---

*Document compiled for ra-7b4: [Reports] Compile complete template set for user review*
*Created: January 11, 2026*
