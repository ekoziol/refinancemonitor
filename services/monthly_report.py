"""Monthly Report Service for refinancing alerts.

Provides data aggregation methods for monthly report generation:
- rate_summary: 30-day rate statistics
- mortgage_status: User mortgage details
- alert_status: Status of user's alerts
- savings: Potential refinancing savings
- outlook: Market outlook based on rate trends
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from refi_monitor import db
from refi_monitor.models import MortgageRate, Mortgage, Mortgage_Tracking, User, Alert
from refi_monitor.calc import calc_loan_monthly_payment, ipmt_total, time_to_even

logger = logging.getLogger(__name__)


@dataclass
class RateSummary:
    """Summary of rate data for a specific term."""
    term_months: int
    term_years: int
    current_rate: float
    min_rate: float
    max_rate: float
    avg_rate: float
    rate_change_30d: float
    trend: str  # 'up', 'down', 'stable'
    data_points: int


@dataclass
class MortgageStatusData:
    """Status data for a user's mortgage."""
    mortgage_id: int
    name: str
    zip_code: str
    original_principal: float
    original_rate: float
    original_term: int
    remaining_principal: float
    remaining_term: int
    current_monthly_payment: float
    current_market_rate: Optional[float]


@dataclass
class AlertStatusData:
    """Status data for a user's alert."""
    alert_id: int
    mortgage_name: str
    alert_type: str
    target_rate: Optional[float]
    target_payment: Optional[float]
    status: str  # 'active', 'paused', 'triggered', 'waiting'
    last_triggered: Optional[datetime]
    triggers_count: int


@dataclass
class SavingsData:
    """Potential savings from refinancing."""
    mortgage_id: int
    mortgage_name: str
    current_rate: float
    current_payment: float
    new_rate: float
    new_term: int
    new_payment: float
    monthly_savings: float
    total_interest_savings: float
    break_even_months: int
    recommendation: str


@dataclass
class MarketOutlook:
    """Market outlook based on rate trends."""
    overall_trend: str  # 'favorable', 'unfavorable', 'neutral'
    trend_description: str
    rate_direction: str  # 'rising', 'falling', 'stable'
    recommendation: str
    confidence: str  # 'high', 'medium', 'low'


class MonthlyReportService:
    """Service for generating monthly report data.

    Aggregates data from various sources to generate comprehensive
    monthly refinancing reports for users.
    """

    STANDARD_TERMS = [180, 360]  # 15-year and 30-year in months
    DEFAULT_REFI_COST = 3000.0
    TREND_THRESHOLD = 0.001  # 0.1% change threshold for trend determination

    def __init__(self, days: int = 30):
        """Initialize the service.

        Args:
            days: Number of days of historical data to analyze.
        """
        self.days = days

    def rate_summary(
        self, zip_code: str, term_months: Optional[int] = None
    ) -> Dict[int, RateSummary]:
        """Get rate summary for a zip code.

        Args:
            zip_code: The zip code to get rates for.
            term_months: Specific term to query, or None for all standard terms.

        Returns:
            Dict mapping term_months to RateSummary objects.
        """
        terms = [term_months] if term_months else self.STANDARD_TERMS
        result = {}

        cutoff_date = datetime.utcnow() - timedelta(days=self.days)

        for term in terms:
            rates = MortgageRate.query.filter(
                MortgageRate.zip_code == zip_code,
                MortgageRate.term_months == term,
                MortgageRate.rate_date >= cutoff_date
            ).order_by(MortgageRate.rate_date.desc()).all()

            if not rates:
                logger.debug(f"No rate data for zip={zip_code}, term={term}")
                continue

            rate_values = [r.rate for r in rates]
            current_rate = rates[0].rate
            oldest_rate = rates[-1].rate
            rate_change = current_rate - oldest_rate

            # Determine trend
            if rate_change < -self.TREND_THRESHOLD:
                trend = 'down'
            elif rate_change > self.TREND_THRESHOLD:
                trend = 'up'
            else:
                trend = 'stable'

            result[term] = RateSummary(
                term_months=term,
                term_years=term // 12,
                current_rate=current_rate,
                min_rate=min(rate_values),
                max_rate=max(rate_values),
                avg_rate=sum(rate_values) / len(rate_values),
                rate_change_30d=rate_change,
                trend=trend,
                data_points=len(rates)
            )

        return result

    def mortgage_status(self, user_id: int) -> List[MortgageStatusData]:
        """Get mortgage status for a user.

        Args:
            user_id: The user's ID.

        Returns:
            List of MortgageStatusData objects.
        """
        mortgages = Mortgage.query.filter_by(user_id=user_id).all()
        result = []

        for mortgage in mortgages:
            # Get latest tracking for current market rate
            tracking = Mortgage_Tracking.query.filter_by(
                mortgage_id=mortgage.id
            ).order_by(Mortgage_Tracking.created_on.desc()).first()

            current_market_rate = tracking.current_rate if tracking else None

            # Calculate current monthly payment
            current_payment = calc_loan_monthly_payment(
                mortgage.remaining_principal,
                mortgage.original_interest_rate,
                mortgage.remaining_term
            )

            result.append(MortgageStatusData(
                mortgage_id=mortgage.id,
                name=mortgage.name,
                zip_code=mortgage.zip_code,
                original_principal=mortgage.original_principal,
                original_rate=mortgage.original_interest_rate,
                original_term=mortgage.original_term,
                remaining_principal=mortgage.remaining_principal,
                remaining_term=mortgage.remaining_term,
                current_monthly_payment=current_payment,
                current_market_rate=current_market_rate
            ))

        return result

    def alert_status(self, user_id: int) -> List[AlertStatusData]:
        """Get alert status for a user.

        Args:
            user_id: The user's ID.

        Returns:
            List of AlertStatusData objects.
        """
        alerts = Alert.query.filter(
            Alert.user_id == user_id,
            Alert.deleted_at.is_(None)
        ).all()

        result = []

        for alert in alerts:
            # Get mortgage name
            mortgage = Mortgage.query.get(alert.mortgage_id)
            mortgage_name = mortgage.name if mortgage else "Unknown"

            # Get alert status using model method
            status = alert.get_status()

            # Find last trigger
            last_triggered = None
            triggers_count = 0
            if alert.triggers:
                triggered_records = [
                    t for t in alert.triggers if t.alert_trigger_status == 1
                ]
                triggers_count = len(triggered_records)
                if triggered_records:
                    last_trigger = max(
                        triggered_records,
                        key=lambda t: t.created_on or datetime.min
                    )
                    last_triggered = last_trigger.created_on

            result.append(AlertStatusData(
                alert_id=alert.id,
                mortgage_name=mortgage_name,
                alert_type=alert.alert_type,
                target_rate=alert.target_interest_rate,
                target_payment=alert.target_monthly_payment,
                status=status,
                last_triggered=last_triggered,
                triggers_count=triggers_count
            ))

        return result

    def savings(
        self,
        user_id: int,
        min_monthly_savings: float = 50.0,
        max_break_even_months: int = 36
    ) -> List[SavingsData]:
        """Calculate potential savings for a user's mortgages.

        Args:
            user_id: The user's ID.
            min_monthly_savings: Minimum monthly savings to consider.
            max_break_even_months: Maximum break-even period to consider.

        Returns:
            List of SavingsData objects for viable refinancing opportunities.
        """
        mortgages = self.mortgage_status(user_id)
        result = []

        for mortgage in mortgages:
            rate_stats = self.rate_summary(mortgage.zip_code)

            for term_months, stats in rate_stats.items():
                # Only consider if new rate is lower
                if stats.current_rate >= mortgage.original_rate:
                    continue

                # Calculate new payment
                new_payment = calc_loan_monthly_payment(
                    mortgage.remaining_principal,
                    stats.current_rate,
                    term_months
                )

                monthly_savings = mortgage.current_monthly_payment - new_payment

                # Skip if savings too small
                if monthly_savings < min_monthly_savings:
                    continue

                # Calculate total interest savings
                current_interest = ipmt_total(
                    mortgage.original_rate,
                    mortgage.remaining_term,
                    mortgage.remaining_principal
                )
                new_interest = ipmt_total(
                    stats.current_rate,
                    term_months,
                    mortgage.remaining_principal
                )
                total_interest_savings = (
                    current_interest - new_interest - self.DEFAULT_REFI_COST
                )

                # Calculate break-even
                break_even = int(time_to_even(
                    self.DEFAULT_REFI_COST, monthly_savings
                ))

                # Skip if break-even too long
                if break_even > max_break_even_months:
                    continue

                # Generate recommendation
                recommendation = self._generate_savings_recommendation(
                    monthly_savings, break_even, total_interest_savings
                )

                result.append(SavingsData(
                    mortgage_id=mortgage.mortgage_id,
                    mortgage_name=mortgage.name,
                    current_rate=mortgage.original_rate,
                    current_payment=mortgage.current_monthly_payment,
                    new_rate=stats.current_rate,
                    new_term=term_months,
                    new_payment=new_payment,
                    monthly_savings=monthly_savings,
                    total_interest_savings=total_interest_savings,
                    break_even_months=break_even,
                    recommendation=recommendation
                ))

        # Sort by total interest savings
        result.sort(key=lambda x: x.total_interest_savings, reverse=True)
        return result

    def outlook(self, zip_code: str) -> MarketOutlook:
        """Generate market outlook based on rate trends.

        Args:
            zip_code: The zip code to analyze.

        Returns:
            MarketOutlook object with trend analysis.
        """
        rate_stats = self.rate_summary(zip_code)

        if not rate_stats:
            return MarketOutlook(
                overall_trend='neutral',
                trend_description="Insufficient rate data available for analysis.",
                rate_direction='stable',
                recommendation="Continue monitoring rates as more data becomes available.",
                confidence='low'
            )

        # Analyze trends across terms
        trends = [stats.trend for stats in rate_stats.values()]
        rate_changes = [stats.rate_change_30d for stats in rate_stats.values()]
        avg_change = sum(rate_changes) / len(rate_changes) if rate_changes else 0

        # Determine overall direction
        down_count = trends.count('down')
        up_count = trends.count('up')

        if down_count > up_count:
            rate_direction = 'falling'
            overall_trend = 'favorable'
        elif up_count > down_count:
            rate_direction = 'rising'
            overall_trend = 'unfavorable'
        else:
            rate_direction = 'stable'
            overall_trend = 'neutral'

        # Generate description and recommendation
        trend_description, recommendation = self._generate_outlook_text(
            rate_direction, avg_change, rate_stats
        )

        # Determine confidence based on data points
        total_data_points = sum(s.data_points for s in rate_stats.values())
        if total_data_points >= 60:
            confidence = 'high'
        elif total_data_points >= 30:
            confidence = 'medium'
        else:
            confidence = 'low'

        return MarketOutlook(
            overall_trend=overall_trend,
            trend_description=trend_description,
            rate_direction=rate_direction,
            recommendation=recommendation,
            confidence=confidence
        )

    def generate_report_context(self, user_id: int) -> Dict[str, Any]:
        """Generate full context for monthly report template.

        Args:
            user_id: The user's ID.

        Returns:
            Dict with all data needed for report rendering.
        """
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return {}

        mortgages = self.mortgage_status(user_id)

        # Get rate stats for user's zip codes
        zip_codes = set(m.zip_code for m in mortgages)
        rate_statistics = {}
        primary_outlook = None

        for zip_code in zip_codes:
            stats = self.rate_summary(zip_code)
            rate_statistics[zip_code] = stats
            if primary_outlook is None:
                primary_outlook = self.outlook(zip_code)

        # Get primary zip code's rate stats for template
        primary_zip = mortgages[0].zip_code if mortgages else None
        primary_rate_stats = rate_statistics.get(primary_zip, {})

        # Get savings opportunities
        savings_opportunities = self.savings(user_id)

        # Get alert statuses
        alerts = self.alert_status(user_id)

        return {
            'user_id': user_id,
            'user_name': user.name,
            'user_email': user.email,
            'report_month': datetime.utcnow().strftime('%B %Y'),
            'generated_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            'rate_statistics': {
                term: asdict(stats) for term, stats in primary_rate_stats.items()
            },
            'mortgages': [asdict(m) for m in mortgages],
            'savings_opportunities': [
                {
                    'mortgage_id': s.mortgage_id,
                    'mortgage_name': s.mortgage_name,
                    'term_years': s.new_term // 12,
                    'current_rate': s.new_rate,
                    'savings': {
                        'new_monthly_payment': s.new_payment,
                        'monthly_savings': s.monthly_savings,
                        'total_interest_savings': s.total_interest_savings,
                        'break_even_months': s.break_even_months
                    }
                }
                for s in savings_opportunities
            ],
            'alert_status': [asdict(a) for a in alerts],
            'outlook': asdict(primary_outlook) if primary_outlook else None
        }

    def _generate_savings_recommendation(
        self,
        monthly_savings: float,
        break_even: int,
        total_savings: float
    ) -> str:
        """Generate a recommendation based on savings metrics."""
        if monthly_savings > 200 and break_even < 12:
            return "Strongly recommended - significant monthly savings with quick payback."
        elif monthly_savings > 100 and break_even < 24:
            return "Recommended - good savings potential with reasonable payback period."
        elif total_savings > 20000:
            return "Consider - substantial long-term interest savings."
        else:
            return "Worth exploring - modest savings opportunity."

    def _generate_outlook_text(
        self,
        rate_direction: str,
        avg_change: float,
        rate_stats: Dict[int, RateSummary]
    ) -> tuple:
        """Generate outlook description and recommendation text."""
        change_pct = abs(avg_change * 100)

        if rate_direction == 'falling':
            description = (
                f"Mortgage rates have decreased by an average of {change_pct:.2f}% "
                f"over the past 30 days. This creates favorable conditions for refinancing."
            )
            recommendation = (
                "Consider refinancing soon to lock in lower rates. "
                "Monitor for continued decreases before committing."
            )
        elif rate_direction == 'rising':
            description = (
                f"Mortgage rates have increased by an average of {change_pct:.2f}% "
                f"over the past 30 days. Refinancing opportunities may be diminishing."
            )
            recommendation = (
                "If you're considering refinancing, acting sooner may be beneficial "
                "before rates increase further."
            )
        else:
            description = (
                "Mortgage rates have remained relatively stable over the past 30 days. "
                "The market is in a holding pattern."
            )
            recommendation = (
                "Current conditions are neutral. Evaluate refinancing based on "
                "your specific financial situation and goals."
            )

        return description, recommendation
