# Refinance Monitor Product Roadmap

> Strategic product prioritization for maximum revenue impact

**Last Updated:** 2026-01-11
**Owner:** Product Team
**Status:** Active

---

## Executive Summary

This roadmap prioritizes features based on revenue impact using the RICE framework (Reach, Impact, Confidence, Effort). Focus is on shipping revenue-generating features first, then optimizing conversion and retention.

**Key Principle:** Don't build features that don't directly drive revenue until the core product generates sustainable income.

---

## Current Product State

### Completed
- Core refinance calculator (Dash-based)
- User authentication (Flask-Login)
- Mortgage CRUD operations
- Basic alert creation flow
- Stripe payment integration (in progress)

### Critical Gaps
- **Email alerts not functional** - Users pay but receive nothing
- **Rate monitoring missing** - No automated rate fetching
- **No onboarding** - Users confused on first visit

---

## Prioritization Framework: RICE Score

```
RICE = (Reach × Impact × Confidence) / Effort

Reach:      Users affected (thousands)
Impact:     Revenue/retention impact (1-10 scale)
Confidence: How sure are we this works? (0-100%)
Effort:     Engineering days required
```

### Example Comparison
| Feature | Reach | Impact | Conf | Effort | RICE |
|---------|-------|--------|------|--------|------|
| Email alerts | 10K | 9 | 80% | 5d | **14,400** |
| Mobile app | 5K | 6 | 60% | 60d | **300** |

Email alerts are **48x higher priority** than mobile app.

---

## Tier 1: Revenue Blockers (Build First)

> **Can't generate revenue without these features**

| Feature | Status | RICE | Owner | Notes |
|---------|--------|------|-------|-------|
| Stripe webhook completion | In Progress | N/A | Backend | Payment validation |
| Email alert delivery | TODO | 14,400 | Backend | SendGrid/Mailgun integration |
| Rate monitoring service | TODO | 12,000 | Backend | MortgageNewsDaily scraper |
| Production deployment | TODO | N/A | DevOps | Railway/Heroku setup |

### Success Metrics
- [ ] Users receive email when rates hit target
- [ ] Payments successfully processed end-to-end
- [ ] Rate data updates daily without errors
- [ ] 99.9% uptime on production

### Technical Requirements

**Email Alerts (ra-f97)**
- Integration with SendGrid or Mailgun
- Email templates for: welcome, rate alert, payment confirmation
- Unsubscribe handling
- Rate limiting to avoid spam filters

**Rate Monitoring (ra-m8v)**
- Daily scrape of MortgageNewsDaily
- Store historical rates in Mortgage_Tracking table
- Trigger alerts when rates meet user targets
- Failover to backup data sources

---

## Tier 2: Conversion Optimizers (Build Next)

> **Increase signup-to-paid conversion rate by 2-3x**

| Feature | RICE | Priority | Notes |
|---------|------|----------|-------|
| Onboarding flow | 8,500 | High | Reduce time-to-value |
| Free tier (freemium) | 7,200 | High | Lower barrier to entry |
| Social proof | 4,800 | Medium | Testimonials, user count |
| Email nurture sequence | 3,600 | Medium | Drip campaign for leads |
| Referral program | 2,400 | Low | Viral growth loop |

### Onboarding Flow Design
1. **Step 1:** Enter current mortgage details (principal, rate, term)
2. **Step 2:** Set target rate/payment
3. **Step 3:** See savings preview (no account required)
4. **Step 4:** Create account to set alert
5. **Step 5:** Payment for premium monitoring

**Conversion funnel targets:**
- Landing → Calculator: 60%
- Calculator → Signup: 20%
- Signup → Payment: 30%
- **Overall: 3.6% visitor-to-paid**

### Freemium Model
| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Calculator only, no alerts |
| Basic | $9/mo | 1 mortgage, email alerts |
| Pro | $29/mo | 5 mortgages, SMS + email, priority support |

---

## Tier 3: Retention Drivers

> **Reduce monthly churn from 10% to 5%**

| Feature | RICE | Priority | Retention Impact |
|---------|------|----------|------------------|
| Rate trend charts | 3,200 | High | Keep users engaged weekly |
| Multiple mortgage tracking | 2,800 | Medium | Higher LTV |
| Refinance savings dashboard | 2,400 | Medium | Visual progress |
| Browser extension | 1,600 | Low | Passive engagement |
| Mobile app | 300 | Very Low | High effort, low incremental value |

### Rate Trend Charts
- Show 30-day, 90-day, 1-year rate history
- Overlay user's target rate
- Predictive trend line (simple moving average)
- Email weekly rate summary

### Multiple Mortgage Support
- Track primary + investment properties
- Separate alerts per property
- Combined savings dashboard
- Bundle pricing discount

---

## Tier 4: Revenue Expansion

> **New revenue streams: $2M+ ARR potential**

| Opportunity | Revenue Model | Effort | Notes |
|-------------|--------------|--------|-------|
| Lender marketplace | Lead gen ($50-200/lead) | High | Regulatory considerations |
| White-label SaaS | B2B licensing ($5K-50K/yr) | Medium | Banks, credit unions |
| Premium tier | $49/mo with expert consult | Low | High-touch for jumbo loans |
| International expansion | Subscription | Very High | UK, Canada, Australia |

### Lender Marketplace
- Partner with 5-10 lenders
- Display competitive quotes when user target is achievable
- Revenue: $50-200 per qualified lead
- **Risk:** Regulatory compliance, potential conflict of interest

### White-Label SaaS
- License calculator + alert engine to financial institutions
- Custom branding, API access
- Revenue: $5K-50K/year per client
- Target: Regional banks, credit unions, mortgage brokers

---

## Tier 5: Competitive Moats (Year 2+)

> **Build defensibility and brand strength**

| Feature | Strategic Value | Feasibility |
|---------|----------------|-------------|
| AI refinance recommendations | Personalized advice | Medium |
| Predictive rate forecasting | Unique data product | Hard |
| Community features | User-generated content | Medium |
| Public API | Platform ecosystem | Easy |

These features create **switching costs** and **network effects** that make the product harder to replicate.

---

## Features to AVOID (Low ROI)

| Feature | Why Avoid |
|---------|-----------|
| Complex financial planning | Scope creep, competitive market |
| Direct lending | Regulatory nightmare, massive capital |
| Blockchain/crypto | Distraction, no user demand |
| Over-complicated UI | Analysis paralysis for users |
| Desktop app | Web + PWA sufficient |
| Real-time rate streaming | Overkill, daily updates sufficient |

---

## Technical Debt & Infrastructure

### Must Address Before Scaling
- [ ] Migrate from Dash to React (in progress - Phase 1-3)
- [ ] Add comprehensive test coverage (>80%)
- [ ] Production logging and monitoring
- [ ] Database backups and disaster recovery
- [ ] Rate limiting and DDoS protection

### Nice to Have
- [ ] CI/CD pipeline improvements
- [ ] Staging environment parity
- [ ] Feature flags for gradual rollout
- [ ] A/B testing infrastructure

---

## Quarterly Roadmap

### Q1 2026 (Jan-Mar)
- [x] Critical bug fixes
- [ ] Complete Stripe webhook
- [ ] Email alert system
- [ ] Rate monitoring service
- [ ] Production deployment

### Q2 2026 (Apr-Jun)
- [ ] Onboarding flow
- [ ] Freemium tier launch
- [ ] Rate trend charts
- [ ] Social proof integration

### Q3 2026 (Jul-Sep)
- [ ] Multiple mortgage support
- [ ] Referral program
- [ ] Email nurture sequences
- [ ] Savings dashboard

### Q4 2026 (Oct-Dec)
- [ ] Lender marketplace pilot
- [ ] White-label exploration
- [ ] Premium tier launch
- [ ] International market research

---

## Success Metrics Dashboard

| Metric | Current | Q1 Target | Q2 Target |
|--------|---------|-----------|-----------|
| MRR | $0 | $5K | $25K |
| Paying Users | 0 | 500 | 2,500 |
| Churn Rate | N/A | <15% | <10% |
| Conversion Rate | N/A | 2% | 4% |
| NPS | N/A | 30 | 50 |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-11 | Prioritize email alerts over mobile | 48x higher RICE score |
| 2026-01-11 | React migration for frontend | Dash limitations, better UX |
| 2026-01-11 | Skip blockchain features | No user demand, distraction |

---

## Appendix: RICE Calculations

### Detailed Scoring

**Email Alerts**
- Reach: 10,000 (all potential paying users)
- Impact: 9 (core value proposition)
- Confidence: 80% (proven need)
- Effort: 5 days
- **RICE: (10,000 × 9 × 0.80) / 5 = 14,400**

**Rate Monitoring**
- Reach: 10,000
- Impact: 8 (enables email alerts)
- Confidence: 75%
- Effort: 5 days
- **RICE: (10,000 × 8 × 0.75) / 5 = 12,000**

**Onboarding Flow**
- Reach: 50,000 (all visitors)
- Impact: 5 (conversion improvement)
- Confidence: 85%
- Effort: 10 days
- **RICE: (50,000 × 5 × 0.85) / 10 = 8,500**

**Mobile App**
- Reach: 5,000 (mobile users)
- Impact: 6 (convenience)
- Confidence: 60% (unknown demand)
- Effort: 60 days
- **RICE: (5,000 × 6 × 0.60) / 60 = 300**
