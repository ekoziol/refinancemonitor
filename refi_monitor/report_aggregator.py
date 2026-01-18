"""Report Data Aggregation Service for refinancing alerts.

Aggregates 30-day rate data, user mortgage status, and calculates potential savings.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from sqlalchemy import func

from . import db
from .models import MortgageRate, Mortgage, Mortgage_Tracking, User, Alert
from .calc import calc_loan_monthly_payment, ipmt_total, time_to_even

logger = logging.getLogger(__name__)


@dataclass
class RateStatistics:
    """Statistics for rate data over a period."""
    current_rate: float
    min_rate: float
    max_rate: float
    avg_rate: float
    rate_change_30d: float
    data_points: int


@dataclass
class MortgageStatus:
    """Current status of a user's mortgage."""
    mortgage_id: int
    name: str
    zip_code: str
    original_principal: float
    original_rate: float
    original_term: int
    remaining_principal: float
    remaining_term: int
    current_monthly_payment: float
    current_rate: Optional[float]


@dataclass
class SavingsCalculation:
    """Potential savings from refinancing."""
    new_rate: float
    new_term: int
    new_monthly_payment: float
    monthly_savings: float
    total_interest_savings: float
    break_even_months: int
    refi_cost: float


@dataclass
class ReportData:
    """Aggregated report data for a user."""
    user_id: int
    user_name: str
    user_email: str
    generated_at: datetime
    rate_statistics: Dict[int, RateStatistics]  # keyed by term_months
    mortgages: List[MortgageStatus]
    savings_opportunities: List[Dict]


class ReportDataAggregationService:
    """Service to aggregate data for refinancing reports."""

    DEFAULT_REFI_COST = 3000.0  # Default refinancing cost estimate
    STANDARD_TERMS = [180, 360]  # 15-year and 30-year terms in months

    def __init__(self, days: int = 30):
        """
        Initialize the service.

        Args:
            days: Number of days of historical rate data to aggregate.
        """
        self.days = days

    def aggregate_rate_data(
        self, zip_code: str, term_months: int
    ) -> Optional[RateStatistics]:
        """
        Aggregate rate data for a specific zip code and term over the configured period.

        Args:
            zip_code: The zip code to get rates for.
            term_months: Loan term in months (e.g., 360 for 30-year).

        Returns:
            RateStatistics object or None if no data available.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.days)

        # Query rate data for the period
        rates = MortgageRate.query.filter(
            MortgageRate.zip_code == zip_code,
            MortgageRate.term_months == term_months,
            MortgageRate.rate_date >= cutoff_date
        ).order_by(MortgageRate.rate_date.desc()).all()

        if not rates:
            logger.warning(
                f"No rate data found for zip={zip_code}, term={term_months}"
            )
            return None

        rate_values = [r.rate for r in rates]
        current_rate = rates[0].rate  # Most recent

        # Get rate from 30 days ago for change calculation
        oldest_rate = rates[-1].rate if rates else current_rate
        rate_change = current_rate - oldest_rate

        return RateStatistics(
            current_rate=current_rate,
            min_rate=min(rate_values),
            max_rate=max(rate_values),
            avg_rate=sum(rate_values) / len(rate_values),
            rate_change_30d=rate_change,
            data_points=len(rates)
        )

    def aggregate_rate_data_bulk(
        self, zip_code: str
    ) -> Dict[int, RateStatistics]:
        """
        Aggregate rate data for all standard terms for a zip code.

        Args:
            zip_code: The zip code to get rates for.

        Returns:
            Dict mapping term_months to RateStatistics.
        """
        result = {}
        for term in self.STANDARD_TERMS:
            stats = self.aggregate_rate_data(zip_code, term)
            if stats:
                result[term] = stats
        return result

    def get_mortgage_status(self, mortgage: Mortgage) -> MortgageStatus:
        """
        Get the current status of a mortgage.

        Args:
            mortgage: The Mortgage object.

        Returns:
            MortgageStatus with current details.
        """
        # Get latest tracking record for current rate
        tracking = Mortgage_Tracking.query.filter_by(
            mortgage_id=mortgage.id
        ).order_by(Mortgage_Tracking.created_on.desc()).first()

        current_rate = tracking.current_rate if tracking else None

        # Calculate current monthly payment
        current_monthly = calc_loan_monthly_payment(
            mortgage.remaining_principal,
            mortgage.original_interest_rate,
            mortgage.remaining_term
        )

        return MortgageStatus(
            mortgage_id=mortgage.id,
            name=mortgage.name,
            zip_code=mortgage.zip_code,
            original_principal=mortgage.original_principal,
            original_rate=mortgage.original_interest_rate,
            original_term=mortgage.original_term,
            remaining_principal=mortgage.remaining_principal,
            remaining_term=mortgage.remaining_term,
            current_monthly_payment=current_monthly,
            current_rate=current_rate
        )

    def get_user_mortgages(self, user_id: int) -> List[MortgageStatus]:
        """
        Get status of all mortgages for a user.

        Args:
            user_id: The user's ID.

        Returns:
            List of MortgageStatus objects.
        """
        mortgages = Mortgage.query.filter_by(user_id=user_id).all()
        return [self.get_mortgage_status(m) for m in mortgages]

    def calculate_savings(
        self,
        mortgage_status: MortgageStatus,
        new_rate: float,
        new_term: int,
        refi_cost: Optional[float] = None
    ) -> SavingsCalculation:
        """
        Calculate potential savings from refinancing.

        Args:
            mortgage_status: Current mortgage status.
            new_rate: New interest rate (as decimal, e.g., 0.05 for 5%).
            new_term: New loan term in months.
            refi_cost: Estimated refinancing cost.

        Returns:
            SavingsCalculation with savings details.
        """
        if refi_cost is None:
            refi_cost = self.DEFAULT_REFI_COST

        # Calculate new monthly payment
        new_monthly = calc_loan_monthly_payment(
            mortgage_status.remaining_principal,
            new_rate,
            new_term
        )

        # Monthly savings
        monthly_savings = mortgage_status.current_monthly_payment - new_monthly

        # Total interest on current loan for remaining term
        current_total_interest = ipmt_total(
            mortgage_status.original_rate,
            mortgage_status.remaining_term,
            mortgage_status.remaining_principal
        )

        # Total interest on new loan
        new_total_interest = ipmt_total(
            new_rate,
            new_term,
            mortgage_status.remaining_principal
        )

        # Interest savings (accounting for refi cost)
        interest_savings = current_total_interest - new_total_interest - refi_cost

        # Break-even calculation
        if monthly_savings > 0:
            break_even = int(time_to_even(refi_cost, monthly_savings))
        else:
            break_even = -1  # Never breaks even

        return SavingsCalculation(
            new_rate=new_rate,
            new_term=new_term,
            new_monthly_payment=new_monthly,
            monthly_savings=monthly_savings,
            total_interest_savings=interest_savings,
            break_even_months=break_even,
            refi_cost=refi_cost
        )

    def find_savings_opportunities(
        self,
        mortgage_status: MortgageStatus,
        rate_stats: Dict[int, RateStatistics],
        min_monthly_savings: float = 50.0,
        max_break_even_months: int = 36
    ) -> List[Dict]:
        """
        Find refinancing opportunities that meet savings criteria.

        Args:
            mortgage_status: Current mortgage status.
            rate_stats: Rate statistics by term.
            min_monthly_savings: Minimum monthly savings threshold.
            max_break_even_months: Maximum acceptable break-even period.

        Returns:
            List of savings opportunity dictionaries.
        """
        opportunities = []

        for term_months, stats in rate_stats.items():
            # Only consider if new rate is lower than current
            if stats.current_rate >= mortgage_status.original_rate:
                continue

            savings = self.calculate_savings(
                mortgage_status,
                stats.current_rate,
                term_months
            )

            # Check if meets criteria
            if (savings.monthly_savings >= min_monthly_savings and
                    0 < savings.break_even_months <= max_break_even_months):
                opportunities.append({
                    'term_months': term_months,
                    'term_years': term_months // 12,
                    'current_rate': stats.current_rate,
                    'rate_trend': 'down' if stats.rate_change_30d < 0 else 'up',
                    'rate_change_30d': stats.rate_change_30d,
                    'savings': savings
                })

        # Sort by total interest savings (highest first)
        opportunities.sort(
            key=lambda x: x['savings'].total_interest_savings,
            reverse=True
        )

        return opportunities

    def generate_user_report(self, user_id: int) -> Optional[ReportData]:
        """
        Generate a complete report for a user.

        Args:
            user_id: The user's ID.

        Returns:
            ReportData object or None if user not found.
        """
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return None

        # Get all mortgages
        mortgages = self.get_user_mortgages(user_id)
        if not mortgages:
            logger.info(f"No mortgages found for user {user_id}")
            return ReportData(
                user_id=user_id,
                user_name=user.name,
                user_email=user.email,
                generated_at=datetime.utcnow(),
                rate_statistics={},
                mortgages=[],
                savings_opportunities=[]
            )

        # Aggregate rate data for each unique zip code
        zip_codes = set(m.zip_code for m in mortgages)
        all_rate_stats = {}
        for zip_code in zip_codes:
            stats = self.aggregate_rate_data_bulk(zip_code)
            all_rate_stats[zip_code] = stats

        # Find savings opportunities for each mortgage
        all_opportunities = []
        for mortgage in mortgages:
            rate_stats = all_rate_stats.get(mortgage.zip_code, {})
            opportunities = self.find_savings_opportunities(mortgage, rate_stats)
            for opp in opportunities:
                opp['mortgage_id'] = mortgage.mortgage_id
                opp['mortgage_name'] = mortgage.name
            all_opportunities.extend(opportunities)

        # Use the first mortgage's zip code for primary rate stats
        primary_zip = mortgages[0].zip_code if mortgages else None
        primary_rate_stats = all_rate_stats.get(primary_zip, {})

        return ReportData(
            user_id=user_id,
            user_name=user.name,
            user_email=user.email,
            generated_at=datetime.utcnow(),
            rate_statistics=primary_rate_stats,
            mortgages=mortgages,
            savings_opportunities=all_opportunities
        )

    def generate_bulk_reports(
        self, user_ids: Optional[List[int]] = None
    ) -> List[ReportData]:
        """
        Generate reports for multiple users.

        Args:
            user_ids: List of user IDs, or None for all users with active alerts.

        Returns:
            List of ReportData objects.
        """
        if user_ids is None:
            # Get users with active paid alerts
            active_alerts = Alert.query.filter(
                Alert.payment_status == 'paid'
            ).all()
            user_ids = list(set(a.user_id for a in active_alerts))

        reports = []
        for user_id in user_ids:
            try:
                report = self.generate_user_report(user_id)
                if report:
                    reports.append(report)
            except Exception as e:
                logger.error(f"Failed to generate report for user {user_id}: {e}")
                continue

        logger.info(f"Generated {len(reports)} reports for {len(user_ids)} users")
        return reports
