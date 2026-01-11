"""Personalized recommendation engine for refinancing decisions."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from .calc import calc_loan_monthly_payment, time_to_even


class Recommendation(Enum):
    YES = "YES"
    NO = "NO"
    WAIT = "WAIT"


@dataclass
class SavingsAnalysis:
    """Calculated savings from refinancing."""
    current_monthly_payment: float
    new_monthly_payment: float
    monthly_savings: float
    annual_savings: float
    total_savings_over_term: float
    break_even_months: int
    refinance_cost: float


@dataclass
class RecommendationResult:
    """Complete recommendation with reasoning and action steps."""
    recommendation: Recommendation
    headline: str
    reasoning: List[str]
    timing_advice: Optional[str]
    action_steps: List[str]
    savings: Optional[SavingsAnalysis]
    confidence_factors: List[str]


def calculate_savings(
    current_principal: float,
    current_rate: float,
    current_remaining_term: int,
    new_rate: float,
    new_term: int,
    refinance_cost: float
) -> SavingsAnalysis:
    """Calculate savings analysis for refinancing."""
    current_monthly = calc_loan_monthly_payment(
        current_principal, current_rate, current_remaining_term
    )

    # Include refinance cost in new principal
    new_principal = current_principal + refinance_cost
    new_monthly = calc_loan_monthly_payment(new_principal, new_rate, new_term)

    monthly_savings = current_monthly - new_monthly
    annual_savings = monthly_savings * 12
    total_savings = monthly_savings * new_term

    if monthly_savings > 0:
        break_even = int(time_to_even(refinance_cost, monthly_savings))
    else:
        break_even = -1  # Never breaks even

    return SavingsAnalysis(
        current_monthly_payment=current_monthly,
        new_monthly_payment=new_monthly,
        monthly_savings=monthly_savings,
        annual_savings=annual_savings,
        total_savings_over_term=total_savings,
        break_even_months=break_even,
        refinance_cost=refinance_cost
    )


def generate_recommendation(
    mortgage,
    alert,
    current_market_rate: float,
    credit_score: Optional[int] = None
) -> RecommendationResult:
    """
    Generate a personalized YES/NO/WAIT recommendation.

    Args:
        mortgage: User's mortgage record
        alert: User's alert settings
        current_market_rate: Current market rate (as decimal, e.g., 0.065)
        credit_score: User's credit score (optional)

    Returns:
        RecommendationResult with recommendation, reasoning, and action steps
    """
    refinance_cost = alert.estimate_refinance_cost or 3000

    # Calculate savings
    savings = calculate_savings(
        current_principal=mortgage.remaining_principal,
        current_rate=mortgage.original_interest_rate,
        current_remaining_term=mortgage.remaining_term,
        new_rate=current_market_rate,
        new_term=alert.target_term,
        refinance_cost=refinance_cost
    )

    # Rate reduction
    rate_reduction = mortgage.original_interest_rate - current_market_rate
    rate_reduction_bps = rate_reduction * 10000  # basis points

    # Decision factors
    factors = []
    recommendation = None
    reasoning = []
    timing_advice = None
    action_steps = []

    # Factor 1: Monthly savings threshold
    if savings.monthly_savings >= 100:
        factors.append("significant_savings")
        reasoning.append(
            f"You'll save ${savings.monthly_savings:,.0f}/month (${savings.annual_savings:,.0f}/year)"
        )
    elif savings.monthly_savings >= 50:
        factors.append("moderate_savings")
        reasoning.append(
            f"Modest savings of ${savings.monthly_savings:,.0f}/month"
        )
    elif savings.monthly_savings > 0:
        factors.append("minimal_savings")
        reasoning.append(
            f"Minimal savings of ${savings.monthly_savings:,.0f}/month"
        )
    else:
        factors.append("no_savings")
        reasoning.append(
            "Current rates would increase your monthly payment"
        )

    # Factor 2: Break-even analysis
    if savings.break_even_months > 0:
        if savings.break_even_months <= 24:
            factors.append("quick_breakeven")
            reasoning.append(
                f"Break-even in {savings.break_even_months} months - you'll recoup costs quickly"
            )
        elif savings.break_even_months <= 48:
            factors.append("moderate_breakeven")
            reasoning.append(
                f"Break-even in {savings.break_even_months} months - reasonable payback period"
            )
        else:
            factors.append("long_breakeven")
            reasoning.append(
                f"Break-even takes {savings.break_even_months} months - consider how long you'll stay"
            )

    # Factor 3: Rate reduction significance
    if rate_reduction_bps >= 100:  # 1% or more
        factors.append("major_rate_drop")
        reasoning.append(
            f"Rate drops {rate_reduction_bps/100:.2f}% - a significant improvement"
        )
    elif rate_reduction_bps >= 50:  # 0.5% or more
        factors.append("good_rate_drop")
        reasoning.append(
            f"Rate improvement of {rate_reduction_bps/100:.2f}%"
        )
    elif rate_reduction_bps >= 25:
        factors.append("small_rate_drop")

    # Factor 4: Credit score consideration
    if credit_score:
        if credit_score >= 740:
            factors.append("excellent_credit")
            reasoning.append(
                "Your excellent credit qualifies you for the best rates"
            )
        elif credit_score >= 670:
            factors.append("good_credit")
        elif credit_score < 670:
            factors.append("credit_concern")
            reasoning.append(
                "Consider improving credit score first for better rates"
            )

    # Factor 5: Remaining term consideration
    if mortgage.remaining_term <= 60:  # 5 years or less
        factors.append("short_remaining")
        reasoning.append(
            f"Only {mortgage.remaining_term} months left - limited time to recoup costs"
        )

    # Generate recommendation based on factors
    positive_factors = [
        "significant_savings", "quick_breakeven", "major_rate_drop",
        "excellent_credit", "good_rate_drop"
    ]
    negative_factors = [
        "no_savings", "long_breakeven", "credit_concern", "short_remaining",
        "minimal_savings"
    ]
    wait_factors = ["moderate_savings", "moderate_breakeven", "small_rate_drop"]

    positive_count = sum(1 for f in factors if f in positive_factors)
    negative_count = sum(1 for f in factors if f in negative_factors)
    wait_count = sum(1 for f in factors if f in wait_factors)

    # Decision logic
    if negative_count >= 2 or "no_savings" in factors:
        recommendation = Recommendation.NO
        headline = "Not the Right Time to Refinance"
        timing_advice = (
            "Monitor rates for a better opportunity. "
            "We'll alert you when conditions improve for your situation."
        )
        action_steps = [
            "Keep your current mortgage for now",
            "Focus on any credit improvement opportunities",
            "Review your alert settings to ensure they match your goals",
            "Check back in 3-6 months as market conditions change"
        ]
    elif positive_count >= 2 and savings.break_even_months <= 36:
        recommendation = Recommendation.YES
        headline = "Great Time to Refinance!"
        action_steps = [
            "Get quotes from 2-3 lenders this week",
            "Gather documents: pay stubs, tax returns, bank statements",
            "Lock your rate once you find the best offer",
            "Review closing disclosure carefully before signing",
            "Set up automatic payments on your new loan"
        ]
    else:
        recommendation = Recommendation.WAIT
        headline = "Consider Waiting for Better Conditions"
        timing_advice = (
            "Current savings are marginal. Wait for rates to drop further "
            "or your situation to change (credit improvement, rate drops). "
            "We're actively monitoring for you."
        )
        action_steps = [
            "Keep this opportunity in mind but don't rush",
            "Get a preliminary quote to have a baseline",
            "Work on any credit improvements if applicable",
            "We'll notify you if conditions improve significantly"
        ]

    return RecommendationResult(
        recommendation=recommendation,
        headline=headline,
        reasoning=reasoning,
        timing_advice=timing_advice,
        action_steps=action_steps,
        savings=savings,
        confidence_factors=factors
    )
