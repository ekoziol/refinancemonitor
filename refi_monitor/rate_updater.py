"""Rate updater module for fetching and updating mortgage rates."""
import logging
from datetime import datetime
from typing import Dict, List
import requests
from .models import Mortgage_Tracking, Alert, Trigger, Mortgage, MortgageRate
from . import db
from decimal import Decimal
from datetime import date

logger = logging.getLogger(__name__)


class RateFetcher:
    """Fetches current mortgage rates from external API."""

    def __init__(self):
        # TODO: Replace with actual API configuration
        # Options: Freddie Mac API, Mortgage News Daily, etc.
        self.api_url = None
        self.api_key = None

    def fetch_current_rates(self) -> Dict[str, float]:
        """
        Fetch current mortgage rates from external source.

        Returns:
            Dict mapping rate types to current rates (as decimals, e.g., 0.0294 = 2.94%)
            Example: {'30 YR FRM': 0.0294, '15 YR FRM': 0.0245, ...}

        TODO: Implement actual API integration
        Current implementation returns mock data for testing.
        """
        # TODO: Replace this mock implementation with actual API call
        # Example with Freddie Mac:
        # response = requests.get(
        #     f"{self.api_url}/pmms/pmms30.json",
        #     headers={'Authorization': f'Bearer {self.api_key}'}
        # )
        # return self._parse_api_response(response.json())

        # Mock data for testing (simulates small rate changes)
        import random
        base_rates = {
            '30 YR FRM': 0.0294,
            '15 YR FRM': 0.0245,
            '5/1 YR ARM': 0.0268,
            'FHA 30 YR': 0.0285,
            'JUMBO 30 YR': 0.0305
        }

        # Add small random variation (-0.05% to +0.05%)
        return {
            rate_type: round(rate + random.uniform(-0.0005, 0.0005), 5)
            for rate_type, rate in base_rates.items()
        }

    def store_rate(self, rate_type: str, rate: float, points: float = None,
                   apr: float = None, change_from_previous: float = None) -> MortgageRate:
        """
        Store a rate in the MortgageRate table.

        Args:
            rate_type: Type of rate (e.g., '30_year_fixed')
            rate: The interest rate as a percentage (e.g., 6.875)
            points: Optional discount points
            apr: Optional APR
            change_from_previous: Optional change from previous day

        Returns:
            MortgageRate object that was created/updated
        """
        today = date.today()

        # Check if rate already exists for this date/type
        existing = MortgageRate.query.filter_by(
            date=today,
            rate_type=rate_type
        ).first()

        if existing:
            existing.rate = Decimal(str(rate))
            if points is not None:
                existing.points = Decimal(str(points))
            if apr is not None:
                existing.apr = Decimal(str(apr))
            if change_from_previous is not None:
                existing.change_from_previous = Decimal(str(change_from_previous))
            existing.updated_at = datetime.utcnow()
            logger.info(f"Updated existing rate for {rate_type} on {today}: {rate}%")
            return existing
        else:
            new_rate = MortgageRate(
                date=today,
                rate_type=rate_type,
                rate=Decimal(str(rate)),
                points=Decimal(str(points)) if points is not None else None,
                apr=Decimal(str(apr)) if apr is not None else None,
                change_from_previous=Decimal(str(change_from_previous)) if change_from_previous is not None else None,
                source='mortgagenewsdaily'
            )
            db.session.add(new_rate)
            logger.info(f"Stored new rate for {rate_type} on {today}: {rate}%")
            return new_rate

    def get_latest_rate(self, rate_type: str = '30_year_fixed') -> MortgageRate:
        """
        Get the most recent rate for a given type.

        Args:
            rate_type: Type of rate to retrieve

        Returns:
            MortgageRate object or None
        """
        return MortgageRate.query.filter_by(
            rate_type=rate_type
        ).order_by(MortgageRate.date.desc()).first()

    def get_rate_history(self, rate_type: str = '30_year_fixed', days: int = 30) -> List[MortgageRate]:
        """
        Get rate history for a given type.

        Args:
            rate_type: Type of rate to retrieve
            days: Number of days of history to retrieve

        Returns:
            List of MortgageRate objects
        """
        from datetime import timedelta
        cutoff_date = date.today() - timedelta(days=days)
        return MortgageRate.query.filter(
            MortgageRate.rate_type == rate_type,
            MortgageRate.date >= cutoff_date
        ).order_by(MortgageRate.date.desc()).all()


class RateUpdater:
    """Updates mortgage tracking records with latest rates."""

    def __init__(self, fetcher: RateFetcher = None):
        self.fetcher = fetcher or RateFetcher()

    def update_all_rates(self) -> Dict[str, int]:
        """
        Update all active mortgage tracking records with current rates.

        Returns:
            Dict with statistics: {'updated': count, 'alerts_triggered': count}
        """
        logger.info("Starting daily rate update...")

        # Fetch current rates
        try:
            current_rates = self.fetcher.fetch_current_rates()
            logger.info(f"Fetched current rates: {current_rates}")
        except Exception as e:
            logger.error(f"Failed to fetch rates: {e}")
            raise

        # Get the 30-year fixed rate as the primary rate
        primary_rate = current_rates.get('30 YR FRM')
        if primary_rate is None:
            logger.error("Primary rate (30 YR FRM) not found in fetched rates")
            raise ValueError("Primary rate not available")

        # Map fetched rate types to MortgageRate enum values and store
        rate_type_mapping = {
            '30 YR FRM': '30_year_fixed',
            '15 YR FRM': '15_year_fixed',
            '5/1 YR ARM': '5_1_ARM',
            'FHA 30 YR': 'FHA_30',
        }

        for fetched_type, rate_value in current_rates.items():
            if fetched_type in rate_type_mapping:
                db_rate_type = rate_type_mapping[fetched_type]
                # Convert rate from decimal (0.0294) to percentage (2.94)
                rate_as_percentage = rate_value * 100
                self.fetcher.store_rate(
                    rate_type=db_rate_type,
                    rate=rate_as_percentage
                )

        db.session.commit()
        logger.info("Stored rates to MortgageRate table")

        # Update all mortgage tracking records
        tracking_records = Mortgage_Tracking.query.all()
        updated_count = 0

        for record in tracking_records:
            try:
                # Update the current rate
                record.current_rate = primary_rate
                record.updated_on = datetime.utcnow()
                updated_count += 1
                logger.debug(f"Updated mortgage_id={record.mortgage_id} to rate={primary_rate}")
            except Exception as e:
                logger.error(f"Failed to update record {record.id}: {e}")
                continue

        db.session.commit()
        logger.info(f"Updated {updated_count} mortgage tracking records")

        # Check alerts and trigger notifications
        alerts_triggered = self._check_and_trigger_alerts(primary_rate)

        return {
            'updated': updated_count,
            'alerts_triggered': alerts_triggered,
            'current_rate': primary_rate
        }

    def _check_and_trigger_alerts(self, current_rate: float) -> int:
        """
        Check all active alerts and create triggers for those meeting conditions.

        Args:
            current_rate: Current mortgage rate to check against

        Returns:
            Number of alerts triggered
        """
        # Get all active alerts (those with paid status and target rates)
        # payment_status can be 'paid', 'unpaid', etc.
        active_alerts = Alert.query.filter(
            Alert.payment_status == 'paid',
            Alert.target_interest_rate.isnot(None)
        ).all()

        triggered_count = 0

        for alert in active_alerts:
            # Check if current rate meets or is below target rate
            if current_rate <= alert.target_interest_rate:
                # Check if we haven't already triggered this alert recently
                recent_trigger = Trigger.query.filter(
                    Trigger.alert_id == alert.id,
                    Trigger.alert_trigger_status == 1  # Successful trigger
                ).order_by(Trigger.alert_trigger_date.desc()).first()

                # Only trigger if no recent trigger or rate has changed significantly
                should_trigger = True
                if recent_trigger:
                    # Don't re-trigger if already triggered in last 24 hours
                    # unless rate has dropped by at least 0.1%
                    hours_since_trigger = (
                        datetime.utcnow() - recent_trigger.alert_trigger_date
                    ).total_seconds() / 3600

                    if hours_since_trigger < 24:
                        should_trigger = False

                if should_trigger:
                    # Create trigger record
                    trigger = Trigger(
                        alert_id=alert.id,
                        alert_type=alert.alert_type,
                        alert_trigger_status=1,  # Success
                        alert_trigger_reason=f"Rate {current_rate:.4f} met target {alert.target_interest_rate:.4f}",
                        alert_trigger_date=datetime.utcnow(),
                        created_on=datetime.utcnow(),
                        updated_on=datetime.utcnow()
                    )
                    db.session.add(trigger)
                    triggered_count += 1

                    # TODO: Send notification to user
                    # self._send_notification(alert, current_rate)
                    logger.info(f"Alert {alert.id} triggered for rate {current_rate}")

        db.session.commit()
        logger.info(f"Triggered {triggered_count} alerts")

        return triggered_count

    def _send_notification(self, alert: Alert, current_rate: float):
        """
        Send notification to user about triggered alert.

        Args:
            alert: The Alert that was triggered
            current_rate: Current rate that triggered the alert

        TODO: Implement email/SMS/webhook notification
        """
        # TODO: Implement notification logic
        # Options:
        # - Email via Flask-Mail
        # - SMS via Twilio
        # - Webhook POST to user-configured URL
        # - Push notification
        pass
