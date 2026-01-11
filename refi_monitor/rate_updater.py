"""Rate updater module for fetching and updating mortgage rates."""
import logging
import os
from datetime import datetime, date
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from .models import MortgageRate, Mortgage_Tracking, Alert, Trigger, Mortgage
from . import db

logger = logging.getLogger(__name__)

# Rate type mappings
RATE_TYPE_MAP = {
    '30_year_fixed': 30,
    '15_year_fixed': 15,
    'FHA_30': 30,
    'VA_30': 30,
    '5_1_ARM': 5,
    '7_1_ARM': 7,
    '10_1_ARM': 10,
}


class RateFetcher:
    """Fetches current mortgage rates from external API or web scraping."""

    def __init__(self):
        self.api_key = os.environ.get('MORTGAGE_API_KEY')
        self.api_url = 'https://api.api-ninjas.com/v1/mortgagerate'

    def fetch_current_rates(self) -> Dict[int, float]:
        """
        Fetch current mortgage rates from external source.

        Returns:
            Dict mapping term years to current rates (as decimals, e.g., 0.0694 = 6.94%)
            Example: {30: 0.0694, 15: 0.0625, 5: 0.0580}
        """
        rates = {}

        # Try API first if key is available
        if self.api_key:
            try:
                rates = self._fetch_from_api()
                if rates:
                    logger.info(f"Fetched rates from API: {rates}")
                    return rates
            except Exception as e:
                logger.warning(f"API fetch failed, trying scraper: {e}")

        # Fallback to scraping MortgageNewsDaily
        try:
            rates = self._fetch_from_mortgage_news_daily()
            if rates:
                logger.info(f"Fetched rates from MortgageNewsDaily: {rates}")
                return rates
        except Exception as e:
            logger.warning(f"MortgageNewsDaily scraping failed: {e}")

        # Final fallback: use most recent rates from database
        try:
            rates = self._fetch_from_database()
            if rates:
                logger.info(f"Using rates from database: {rates}")
                return rates
        except Exception as e:
            logger.error(f"Database fetch failed: {e}")

        raise ValueError("Failed to fetch mortgage rates from any source")

    def _fetch_from_api(self) -> Dict[int, float]:
        """Fetch rates from API Ninjas mortgage rate API."""
        response = requests.get(
            self.api_url,
            headers={'X-Api-Key': self.api_key},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        rates = {}
        # Parse API response - format may vary
        if isinstance(data, dict):
            # Map common field names to term years
            field_map = {
                'rate30Fixed': 30,
                'rate15Fixed': 15,
                'rate51Arm': 5,
                'rate71Arm': 7,
                'thirtyYearFixed': 30,
                'fifteenYearFixed': 15,
                'fiveOneArm': 5,
            }
            for field, term in field_map.items():
                if field in data and data[field]:
                    # Convert percentage to decimal (6.94 -> 0.0694)
                    rate_value = float(data[field])
                    if rate_value > 1:  # If rate is in percentage form
                        rate_value = rate_value / 100
                    rates[term] = rate_value
        elif isinstance(data, list) and len(data) > 0:
            # Handle list response (historical data)
            latest = data[0] if data else {}
            if '30_year_frm' in latest:
                rates[30] = float(latest['30_year_frm']) / 100
            if '15_year_frm' in latest:
                rates[15] = float(latest['15_year_frm']) / 100
            if '5_1_arm' in latest:
                rates[5] = float(latest['5_1_arm']) / 100

        return rates

    def _fetch_from_mortgage_news_daily(self) -> Dict[int, float]:
        """Scrape rates from MortgageNewsDaily website."""
        url = 'https://www.mortgagenewsdaily.com/mortgage-rates'
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; RateMonitor/1.0)'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        rates = {}

        # Look for rate display elements
        rate_selectors = [
            ('div.rate-product', 'span.rate'),
            ('tr.rate-row', 'td.rate'),
            ('[data-rate-type]', '[data-rate-value]'),
        ]

        # Try to find 30-year fixed rate
        thirty_year = soup.find(string=lambda t: t and '30' in t and 'Year' in t)
        if thirty_year:
            parent = thirty_year.find_parent(['div', 'tr', 'td'])
            if parent:
                rate_elem = parent.find_next(string=lambda t: t and '%' in t)
                if rate_elem:
                    try:
                        rate_str = rate_elem.strip().replace('%', '')
                        rates[30] = float(rate_str) / 100
                    except ValueError:
                        pass

        # Try to find 15-year fixed rate
        fifteen_year = soup.find(string=lambda t: t and '15' in t and 'Year' in t)
        if fifteen_year:
            parent = fifteen_year.find_parent(['div', 'tr', 'td'])
            if parent:
                rate_elem = parent.find_next(string=lambda t: t and '%' in t)
                if rate_elem:
                    try:
                        rate_str = rate_elem.strip().replace('%', '')
                        rates[15] = float(rate_str) / 100
                    except ValueError:
                        pass

        return rates

    def _fetch_from_database(self) -> Dict[int, float]:
        """Get most recent rates from MortgageRate table."""
        rates = {}

        # Query most recent rate for each type
        latest_30 = MortgageRate.query.filter_by(
            rate_type='30_year_fixed'
        ).order_by(MortgageRate.date.desc()).first()

        latest_15 = MortgageRate.query.filter_by(
            rate_type='15_year_fixed'
        ).order_by(MortgageRate.date.desc()).first()

        if latest_30:
            rates[30] = float(latest_30.rate) / 100  # Convert from percentage
        if latest_15:
            rates[15] = float(latest_15.rate) / 100

        return rates

    def store_rates(self, rates: Dict[int, float]) -> int:
        """
        Store fetched rates in the MortgageRate table.

        Args:
            rates: Dict mapping term years to rate decimals

        Returns:
            Number of rates stored
        """
        today = date.today()
        stored = 0

        term_to_type = {
            30: '30_year_fixed',
            15: '15_year_fixed',
            5: '5_1_ARM',
            7: '7_1_ARM',
            10: '10_1_ARM',
        }

        for term, rate in rates.items():
            rate_type = term_to_type.get(term)
            if not rate_type:
                continue

            # Check if rate for today already exists
            existing = MortgageRate.query.filter_by(
                date=today,
                rate_type=rate_type
            ).first()

            rate_percentage = rate * 100  # Convert to percentage (0.0694 -> 6.94)

            if existing:
                # Update existing rate
                old_rate = float(existing.rate)
                existing.rate = rate_percentage
                existing.change_from_previous = rate_percentage - old_rate
                existing.updated_at = datetime.utcnow()
            else:
                # Get previous rate for change calculation
                previous = MortgageRate.query.filter_by(
                    rate_type=rate_type
                ).filter(
                    MortgageRate.date < today
                ).order_by(MortgageRate.date.desc()).first()

                change = None
                if previous:
                    change = rate_percentage - float(previous.rate)

                new_rate = MortgageRate(
                    date=today,
                    rate_type=rate_type,
                    rate=rate_percentage,
                    change_from_previous=change,
                    source='api' if self.api_key else 'mortgagenewsdaily',
                    created_at=datetime.utcnow()
                )
                db.session.add(new_rate)
                stored += 1

        db.session.commit()
        return stored


class RateUpdater:
    """Updates mortgage tracking records with latest rates."""

    def __init__(self, fetcher: RateFetcher = None):
        self.fetcher = fetcher or RateFetcher()

    def update_all_rates(self) -> Dict[str, any]:
        """
        Update all active mortgage tracking records with current rates.

        Returns:
            Dict with statistics: {'updated': count, 'alerts_triggered': count, 'current_rate': float}
        """
        logger.info("Starting daily rate update...")

        # Fetch current rates
        try:
            current_rates = self.fetcher.fetch_current_rates()
            logger.info(f"Fetched current rates: {current_rates}")
        except Exception as e:
            logger.error(f"Failed to fetch rates: {e}")
            raise

        # Store rates in database
        try:
            stored = self.fetcher.store_rates(current_rates)
            logger.info(f"Stored {stored} new rate records")
        except Exception as e:
            logger.warning(f"Failed to store rates: {e}")

        # Get the 30-year fixed rate as the primary rate
        primary_rate = current_rates.get(30)
        if primary_rate is None:
            logger.error("Primary rate (30-year fixed) not found in fetched rates")
            raise ValueError("Primary rate not available")

        # Update all mortgage tracking records
        tracking_records = Mortgage_Tracking.query.all()
        updated_count = 0

        for record in tracking_records:
            try:
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
        alerts_triggered = self._check_and_trigger_alerts(current_rates)

        return {
            'updated': updated_count,
            'alerts_triggered': alerts_triggered,
            'current_rate': primary_rate,
            'rates': current_rates
        }

    def _check_and_trigger_alerts(self, current_rates: Dict[int, float]) -> int:
        """
        Check all active alerts and create triggers for those meeting conditions.

        Args:
            current_rates: Dict mapping term years to current rate decimals

        Returns:
            Number of alerts triggered
        """
        # Get all active alerts with paid status
        active_alerts = Alert.query.filter(
            Alert.payment_status.in_(['paid', 'active']),
        ).all()

        triggered_count = 0
        primary_rate = current_rates.get(30, 0)

        for alert in active_alerts:
            # Determine which rate to use based on target term
            target_term_years = alert.target_term // 12 if alert.target_term else 30
            current_rate = current_rates.get(target_term_years, primary_rate)

            should_trigger = False
            reason = ""

            # Check interest rate alerts
            if alert.target_interest_rate is not None:
                if current_rate <= alert.target_interest_rate:
                    should_trigger = True
                    reason = f"Rate {current_rate*100:.2f}% met target {alert.target_interest_rate*100:.2f}%"

            # Check monthly payment alerts
            if alert.target_monthly_payment is not None and not should_trigger:
                from .calc import calc_loan_monthly_payment
                mortgage = Mortgage.query.get(alert.mortgage_id)
                if mortgage:
                    # Calculate monthly payment at current rate
                    adjusted_principal = mortgage.remaining_principal + alert.estimate_refinance_cost
                    potential_payment = calc_loan_monthly_payment(
                        adjusted_principal,
                        current_rate,
                        alert.target_term
                    )
                    if potential_payment <= alert.target_monthly_payment:
                        should_trigger = True
                        reason = f"Monthly payment ${potential_payment:.2f} meets target ${alert.target_monthly_payment:.2f}"

            if should_trigger:
                # Check if we already triggered recently
                recent_trigger = Trigger.query.filter(
                    Trigger.alert_id == alert.id,
                    Trigger.alert_trigger_status == 1
                ).order_by(Trigger.alert_trigger_date.desc()).first()

                create_trigger = True
                if recent_trigger and recent_trigger.alert_trigger_date:
                    hours_since = (datetime.utcnow() - recent_trigger.alert_trigger_date).total_seconds() / 3600
                    if hours_since < 24:
                        create_trigger = False
                        logger.info(f"Alert {alert.id} already triggered within 24 hours")

                if create_trigger:
                    trigger = Trigger(
                        alert_id=alert.id,
                        alert_type=alert.alert_type,
                        alert_trigger_status=1,
                        alert_trigger_reason=reason,
                        alert_trigger_date=datetime.utcnow(),
                        created_on=datetime.utcnow(),
                        updated_on=datetime.utcnow()
                    )
                    db.session.add(trigger)
                    triggered_count += 1
                    logger.info(f"Alert {alert.id} triggered: {reason}")

        db.session.commit()
        logger.info(f"Triggered {triggered_count} alerts")
        return triggered_count

    def get_current_rates(self) -> Dict[int, float]:
        """Get the current cached rates without triggering a full update."""
        return self.fetcher.fetch_current_rates()

    def get_rate_history(self, rate_type: str = '30_year_fixed', days: int = 30):
        """
        Get historical rates for a specific rate type.

        Args:
            rate_type: Type of rate to query
            days: Number of days of history

        Returns:
            List of MortgageRate records
        """
        from datetime import timedelta
        cutoff = date.today() - timedelta(days=days)

        return MortgageRate.query.filter(
            MortgageRate.rate_type == rate_type,
            MortgageRate.date >= cutoff
        ).order_by(MortgageRate.date.asc()).all()
