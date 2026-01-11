"""MortgageNewsDaily scraper for fetching daily mortgage rates."""

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Rate type mappings from HTML to standardized names
RATE_TYPE_MAPPING = {
    '30 Yr. Fixed': '30_yr_fixed',
    '15 Yr. Fixed': '15_yr_fixed',
    '30 Yr. Jumbo': '30_yr_jumbo',
    '30 Yr. FHA': '30_yr_fha',
    '30 Yr. VA': '30_yr_va',
    '7/6 SOFR ARM': '7_6_arm',
}

MND_RATES_URL = 'https://www.mortgagenewsdaily.com/mortgage-rates'


@dataclass
class RateData:
    """Data class for a single rate entry."""
    rate_type: str
    rate: float
    points: Optional[float]
    change: Optional[float]
    rate_date: date
    source: str = 'mortgagenewsdaily'


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class FetchError(ScraperError):
    """Error fetching the page."""
    pass


class ParseError(ScraperError):
    """Error parsing the page content."""
    pass


class ValidationError(ScraperError):
    """Error validating scraped data."""
    pass


class MortgageNewsDailyScraper:
    """Scraper for MortgageNewsDaily.com mortgage rates."""

    def __init__(self, url: str = MND_RATES_URL, timeout: int = 30):
        """
        Initialize the scraper.

        Args:
            url: URL to scrape (default: MortgageNewsDaily rates page)
            timeout: Request timeout in seconds
        """
        self.url = url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; RefiAlertBot/1.0)'
        })

    def fetch_page(self) -> str:
        """
        Fetch the mortgage rates page.

        Returns:
            HTML content of the page

        Raises:
            FetchError: If the request fails
        """
        try:
            logger.info(f"Fetching rates from {self.url}")
            response = self.session.get(self.url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page: {e}")
            raise FetchError(f"Failed to fetch {self.url}: {e}") from e

    def parse_rate_value(self, rate_str: str) -> float:
        """
        Parse a rate string like '6.06%' to a float.

        Args:
            rate_str: Rate string with optional % sign

        Returns:
            Rate as a decimal (e.g., 0.0606 for 6.06%)

        Raises:
            ParseError: If the rate cannot be parsed
        """
        try:
            # Remove % sign and whitespace
            cleaned = rate_str.strip().rstrip('%').strip()
            rate = float(cleaned)
            # Convert from percentage to decimal
            return rate / 100
        except (ValueError, AttributeError) as e:
            raise ParseError(f"Cannot parse rate value: {rate_str}") from e

    def parse_points_value(self, points_str: str) -> Optional[float]:
        """
        Parse a points string to a float.

        Args:
            points_str: Points string (e.g., '0.50' or '--')

        Returns:
            Points as a float, or None if not available
        """
        try:
            cleaned = points_str.strip()
            if cleaned in ('--', '-', '', 'N/A'):
                return None
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def parse_change_value(self, change_str: str) -> Optional[float]:
        """
        Parse a change string like '-0.15%' or '+0.00%'.

        Args:
            change_str: Change string with optional +/- and % signs

        Returns:
            Change as a decimal, or None if not available
        """
        try:
            # Remove HTML entities, % sign, and whitespace
            cleaned = change_str.strip()
            # Replace HTML entity for plus sign (&#x2B; = +)
            cleaned = cleaned.replace('&#x2B;', '+')
            cleaned = cleaned.rstrip('%').strip()
            if cleaned in ('--', '-', '', 'N/A'):
                return None
            return float(cleaned) / 100
        except (ValueError, AttributeError):
            return None

    def parse_date(self, date_str: str) -> date:
        """
        Parse a date string like '1/9/26' to a date object.

        Args:
            date_str: Date string in M/D/YY format

        Returns:
            date object

        Raises:
            ParseError: If the date cannot be parsed
        """
        try:
            # Parse M/D/YY format
            cleaned = date_str.strip()
            parsed = datetime.strptime(cleaned, '%m/%d/%y')
            return parsed.date()
        except (ValueError, AttributeError) as e:
            # Try alternative format M/D/YYYY
            try:
                parsed = datetime.strptime(cleaned, '%m/%d/%Y')
                return parsed.date()
            except (ValueError, AttributeError):
                raise ParseError(f"Cannot parse date: {date_str}") from e

    def parse_rate_data(self, html: str) -> List[RateData]:
        """
        Parse rate data from HTML content.

        Args:
            html: HTML content of the page

        Returns:
            List of RateData objects

        Raises:
            ParseError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            rates = []

            # Find all table sections - look for the MND section
            # The MND section has a header with "Mortgage News Daily" link
            tables = soup.find_all('tbody')

            for tbody in tables:
                # Find the header row that identifies the data source
                header_row = tbody.find('th', class_='rate-product')
                if not header_row:
                    continue

                # Check if this is the MND section
                mnd_link = header_row.find('a', href='/mortgage-rates/mnd')
                if not mnd_link:
                    continue

                # Get the date from the header
                date_div = header_row.find('div', class_='pull-right')
                if not date_div:
                    logger.warning("Could not find date in MND section header")
                    continue

                rate_date = self.parse_date(date_div.get_text())
                logger.info(f"Found MND rates for date: {rate_date}")

                # Find all rate rows (they have a td with class 'rate-product')
                # But stop when we hit the next source header (Freddie Mac, MBA, etc.)
                rows = tbody.find_all('tr')
                in_mnd_section = False
                for row in rows:
                    # Check if this is a header row (th with class rate-product)
                    header_th = row.find('th', class_='rate-product')
                    if header_th:
                        # Check if this is the MND header or another source
                        if header_th.find('a', href='/mortgage-rates/mnd'):
                            in_mnd_section = True
                            continue
                        else:
                            # We've hit another source's header, stop processing
                            in_mnd_section = False
                            continue

                    # Skip rows if we're not in the MND section
                    if not in_mnd_section:
                        continue

                    product_cell = row.find('td', class_='rate-product')
                    if not product_cell:
                        continue

                    # Get the product name from the link
                    product_link = product_cell.find('a')
                    if not product_link:
                        continue

                    product_name = product_link.get_text().strip()

                    # Map to standardized rate type
                    rate_type = RATE_TYPE_MAPPING.get(product_name)
                    if not rate_type:
                        logger.warning(f"Unknown rate type: {product_name}")
                        continue

                    # Get all td cells in the row
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        logger.warning(f"Unexpected row format for {product_name}")
                        continue

                    # Extract rate (second cell)
                    rate_cell = cells[1]
                    rate = self.parse_rate_value(rate_cell.get_text())

                    # Extract points (third cell)
                    points_cell = cells[2]
                    points = self.parse_points_value(points_cell.get_text())

                    # Extract change (fourth cell)
                    change_cell = cells[3]
                    change = self.parse_change_value(change_cell.get_text())

                    rate_data = RateData(
                        rate_type=rate_type,
                        rate=rate,
                        points=points,
                        change=change,
                        rate_date=rate_date,
                    )
                    rates.append(rate_data)
                    logger.debug(f"Parsed rate: {rate_data}")

                # We found the MND section, no need to continue
                break

            if not rates:
                raise ParseError("No rate data found in page")

            return rates

        except ParseError:
            raise
        except Exception as e:
            logger.error(f"Error parsing rate data: {e}")
            raise ParseError(f"Failed to parse rate data: {e}") from e

    def validate_rate_data(self, rates: List[RateData]) -> List[RateData]:
        """
        Validate scraped rate data for sanity.

        Args:
            rates: List of RateData to validate

        Returns:
            Validated list of RateData

        Raises:
            ValidationError: If validation fails
        """
        if not rates:
            raise ValidationError("No rates to validate")

        # Check for reasonable rate values (between 0% and 15%)
        for rate_data in rates:
            if not (0.0 < rate_data.rate < 0.15):
                raise ValidationError(
                    f"Rate {rate_data.rate} for {rate_data.rate_type} "
                    f"is outside reasonable range (0-15%)"
                )

            # Check for reasonable date (not in the future, not too old)
            today = date.today()
            if rate_data.rate_date > today:
                raise ValidationError(
                    f"Rate date {rate_data.rate_date} is in the future"
                )

            # Warn if date is more than 7 days old
            days_old = (today - rate_data.rate_date).days
            if days_old > 7:
                logger.warning(
                    f"Rate date {rate_data.rate_date} is {days_old} days old"
                )

        # Check that we have the expected rate types
        expected_types = {'30_yr_fixed', '15_yr_fixed'}
        found_types = {r.rate_type for r in rates}
        missing = expected_types - found_types
        if missing:
            logger.warning(f"Missing expected rate types: {missing}")

        logger.info(f"Validated {len(rates)} rates")
        return rates

    def fetch_current_rates(self) -> List[RateData]:
        """
        Fetch and parse current mortgage rates.

        Returns:
            List of validated RateData objects

        Raises:
            ScraperError: If fetching, parsing, or validation fails
        """
        html = self.fetch_page()
        rates = self.parse_rate_data(html)
        validated_rates = self.validate_rate_data(rates)
        return validated_rates

    def fetch_rates_as_dict(self) -> Dict[str, float]:
        """
        Fetch rates and return as a simple dictionary.

        This method provides a compatible interface for the RateFetcher class.

        Returns:
            Dict mapping rate type names to decimal rates
        """
        rates = self.fetch_current_rates()

        # Convert to dict format expected by RateUpdater
        result = {}
        type_display_names = {
            '30_yr_fixed': '30 YR FRM',
            '15_yr_fixed': '15 YR FRM',
            '30_yr_jumbo': 'JUMBO 30 YR',
            '30_yr_fha': 'FHA 30 YR',
            '30_yr_va': 'VA 30 YR',
            '7_6_arm': '5/1 YR ARM',
        }

        for rate_data in rates:
            display_name = type_display_names.get(rate_data.rate_type, rate_data.rate_type)
            result[display_name] = rate_data.rate

        return result

    def save_to_database(self, rates: List[RateData]) -> int:
        """
        Save rate data to the database.

        Args:
            rates: List of RateData to save

        Returns:
            Number of records saved/updated
        """
        # Import here to avoid circular imports
        from datetime import datetime
        from .. import db
        from ..models import DailyMortgageRate

        saved_count = 0

        for rate_data in rates:
            # Check if record already exists
            existing = DailyMortgageRate.query.filter_by(
                date=rate_data.rate_date,
                rate_type=rate_data.rate_type
            ).first()

            now = datetime.utcnow()

            if existing:
                # Update existing record
                existing.rate = rate_data.rate
                existing.points = rate_data.points
                existing.change_from_previous = rate_data.change
                existing.updated_at = now
                logger.debug(f"Updated rate: {rate_data.rate_type} = {rate_data.rate}")
            else:
                # Create new record
                new_rate = DailyMortgageRate(
                    date=rate_data.rate_date,
                    rate_type=rate_data.rate_type,
                    rate=rate_data.rate,
                    points=rate_data.points,
                    change_from_previous=rate_data.change,
                    source=rate_data.source,
                    created_at=now,
                    updated_at=now,
                )
                db.session.add(new_rate)
                logger.debug(f"Created rate: {rate_data.rate_type} = {rate_data.rate}")

            saved_count += 1

        db.session.commit()
        logger.info(f"Saved {saved_count} rates to database")

        return saved_count
