"""Tests for MortgageNewsDaily scraper."""

import pytest
from datetime import date
from unittest.mock import Mock, patch

from refi_monitor.scrapers.mortgage_news_daily import (
    MortgageNewsDailyScraper,
    RateData,
    FetchError,
    ParseError,
    ValidationError,
    RATE_TYPE_MAPPING,
)


# Sample HTML that matches the structure of mortgagenewsdaily.com
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<body>
<table>
    <tbody>
        <tr>
            <th></th>
            <th>Rate</th>
            <th>Points</th>
            <th>Change</th>
        </tr>
        <tr>
            <th class="rate-product" colspan="4">
                <div class="pull-right text-muted" style="font-weight: normal;">1/9/26</div>
                <a href="/mortgage-rates/mnd">Mortgage News Daily</a>
            </th>
        </tr>
        <tr>
            <td class="rate-product">
                <a href="/mortgage-rates/30-year-fixed">30 Yr. Fixed</a>
            </td>
            <td class="rate">6.06%</td>
            <td>--</td>
            <td class="text-center change">
                <span>-0.15%</span>
            </td>
        </tr>
        <tr>
            <td class="rate-product">
                <a href="/mortgage-rates/15-year-fixed">15 Yr. Fixed</a>
            </td>
            <td class="rate">5.59%</td>
            <td>--</td>
            <td class="text-center change">
                <span>-0.15%</span>
            </td>
        </tr>
        <tr>
            <td class="rate-product">
                <a href="/mortgage-rates/30-year-jumbo">30 Yr. Jumbo</a>
            </td>
            <td class="rate">6.35%</td>
            <td>0.50</td>
            <td class="text-center change">
                <span>+0.00%</span>
            </td>
        </tr>
        <tr>
            <td class="rate-product">
                <a href="/mortgage-rates/30-year-fha">30 Yr. FHA</a>
            </td>
            <td class="rate">5.69%</td>
            <td>--</td>
            <td class="text-center change">
                <span>-0.15%</span>
            </td>
        </tr>
        <tr>
            <td class="rate-product">
                <a href="/mortgage-rates/30-year-va">30 Yr. VA</a>
            </td>
            <td class="rate">5.70%</td>
            <td>--</td>
            <td class="text-center change">
                <span>-0.15%</span>
            </td>
        </tr>
        <tr>
            <td class="rate-product">
                <a href="/mortgage-rates/5-1-arm">7/6 SOFR ARM</a>
            </td>
            <td class="rate">5.72%</td>
            <td>--</td>
            <td class="text-center change">
                <span>-0.01%</span>
            </td>
        </tr>
    </tbody>
</table>
</body>
</html>
"""


class TestMortgageNewsDailyScraper:
    """Tests for MortgageNewsDailyScraper class."""

    def test_init_default_url(self):
        """Test scraper initializes with default URL."""
        scraper = MortgageNewsDailyScraper()
        assert scraper.url == 'https://www.mortgagenewsdaily.com/mortgage-rates'
        assert scraper.timeout == 30

    def test_init_custom_url(self):
        """Test scraper initializes with custom URL."""
        scraper = MortgageNewsDailyScraper(url='https://example.com', timeout=60)
        assert scraper.url == 'https://example.com'
        assert scraper.timeout == 60


class TestParseRateValue:
    """Tests for parse_rate_value method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    def test_parse_rate_with_percent(self):
        """Test parsing rate with % sign."""
        assert self.scraper.parse_rate_value('6.06%') == pytest.approx(0.0606)

    def test_parse_rate_without_percent(self):
        """Test parsing rate without % sign."""
        assert self.scraper.parse_rate_value('6.06') == pytest.approx(0.0606)

    def test_parse_rate_with_whitespace(self):
        """Test parsing rate with whitespace."""
        assert self.scraper.parse_rate_value('  6.06%  ') == pytest.approx(0.0606)

    def test_parse_invalid_rate(self):
        """Test parsing invalid rate raises error."""
        with pytest.raises(ParseError):
            self.scraper.parse_rate_value('invalid')


class TestParsePointsValue:
    """Tests for parse_points_value method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    def test_parse_points_number(self):
        """Test parsing points with a number."""
        assert self.scraper.parse_points_value('0.50') == pytest.approx(0.50)

    def test_parse_points_dash(self):
        """Test parsing points with --."""
        assert self.scraper.parse_points_value('--') is None

    def test_parse_points_single_dash(self):
        """Test parsing points with single -."""
        assert self.scraper.parse_points_value('-') is None

    def test_parse_points_empty(self):
        """Test parsing empty points."""
        assert self.scraper.parse_points_value('') is None


class TestParseChangeValue:
    """Tests for parse_change_value method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    def test_parse_negative_change(self):
        """Test parsing negative change."""
        assert self.scraper.parse_change_value('-0.15%') == pytest.approx(-0.0015)

    def test_parse_positive_change(self):
        """Test parsing positive change."""
        assert self.scraper.parse_change_value('+0.15%') == pytest.approx(0.0015)

    def test_parse_zero_change(self):
        """Test parsing zero change."""
        assert self.scraper.parse_change_value('+0.00%') == pytest.approx(0.0)

    def test_parse_dash_change(self):
        """Test parsing -- as no change."""
        assert self.scraper.parse_change_value('--') is None


class TestParseDate:
    """Tests for parse_date method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    def test_parse_date_short_year(self):
        """Test parsing date with 2-digit year."""
        result = self.scraper.parse_date('1/9/26')
        assert result == date(2026, 1, 9)

    def test_parse_date_full_year(self):
        """Test parsing date with 4-digit year."""
        result = self.scraper.parse_date('1/9/2026')
        assert result == date(2026, 1, 9)

    def test_parse_date_with_whitespace(self):
        """Test parsing date with whitespace."""
        result = self.scraper.parse_date('  1/9/26  ')
        assert result == date(2026, 1, 9)

    def test_parse_invalid_date(self):
        """Test parsing invalid date raises error."""
        with pytest.raises(ParseError):
            self.scraper.parse_date('invalid')


class TestParseRateData:
    """Tests for parse_rate_data method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    def test_parse_sample_html(self):
        """Test parsing sample HTML returns all rate types."""
        rates = self.scraper.parse_rate_data(SAMPLE_HTML)

        assert len(rates) == 6

        # Check that we have all expected rate types
        rate_types = {r.rate_type for r in rates}
        assert '30_yr_fixed' in rate_types
        assert '15_yr_fixed' in rate_types
        assert '30_yr_jumbo' in rate_types
        assert '30_yr_fha' in rate_types
        assert '30_yr_va' in rate_types
        assert '7_6_arm' in rate_types

    def test_parse_30yr_fixed_rate(self):
        """Test parsing 30 Yr Fixed rate."""
        rates = self.scraper.parse_rate_data(SAMPLE_HTML)
        rate_30yr = next(r for r in rates if r.rate_type == '30_yr_fixed')

        assert rate_30yr.rate == pytest.approx(0.0606)
        assert rate_30yr.points is None
        assert rate_30yr.change == pytest.approx(-0.0015)
        assert rate_30yr.rate_date == date(2026, 1, 9)
        assert rate_30yr.source == 'mortgagenewsdaily'

    def test_parse_30yr_jumbo_rate_with_points(self):
        """Test parsing 30 Yr Jumbo rate which has points."""
        rates = self.scraper.parse_rate_data(SAMPLE_HTML)
        rate_jumbo = next(r for r in rates if r.rate_type == '30_yr_jumbo')

        assert rate_jumbo.rate == pytest.approx(0.0635)
        assert rate_jumbo.points == pytest.approx(0.50)
        assert rate_jumbo.change == pytest.approx(0.0)

    def test_parse_empty_html(self):
        """Test parsing empty HTML raises error."""
        with pytest.raises(ParseError, match="No rate data found"):
            self.scraper.parse_rate_data('<html></html>')

    def test_parse_html_without_mnd_section(self):
        """Test parsing HTML without MND section raises error."""
        html = """
        <table>
            <tbody>
                <tr>
                    <th class="rate-product" colspan="4">
                        <a href="/mortgage-rates/freddie-mac">Freddie Mac</a>
                    </th>
                </tr>
            </tbody>
        </table>
        """
        with pytest.raises(ParseError, match="No rate data found"):
            self.scraper.parse_rate_data(html)


class TestValidateRateData:
    """Tests for validate_rate_data method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    def test_validate_valid_rates(self):
        """Test validating valid rates passes."""
        rates = [
            RateData(
                rate_type='30_yr_fixed',
                rate=0.0606,
                points=None,
                change=-0.0015,
                rate_date=date.today(),
            ),
            RateData(
                rate_type='15_yr_fixed',
                rate=0.0559,
                points=None,
                change=-0.0015,
                rate_date=date.today(),
            ),
        ]
        validated = self.scraper.validate_rate_data(rates)
        assert len(validated) == 2

    def test_validate_empty_rates(self):
        """Test validating empty rates raises error."""
        with pytest.raises(ValidationError, match="No rates to validate"):
            self.scraper.validate_rate_data([])

    def test_validate_rate_too_high(self):
        """Test validating rate above 15% raises error."""
        rates = [
            RateData(
                rate_type='30_yr_fixed',
                rate=0.20,  # 20% - too high
                points=None,
                change=None,
                rate_date=date.today(),
            ),
        ]
        with pytest.raises(ValidationError, match="outside reasonable range"):
            self.scraper.validate_rate_data(rates)

    def test_validate_rate_negative(self):
        """Test validating negative rate raises error."""
        rates = [
            RateData(
                rate_type='30_yr_fixed',
                rate=-0.01,
                points=None,
                change=None,
                rate_date=date.today(),
            ),
        ]
        with pytest.raises(ValidationError, match="outside reasonable range"):
            self.scraper.validate_rate_data(rates)

    def test_validate_future_date(self):
        """Test validating future date raises error."""
        from datetime import timedelta
        rates = [
            RateData(
                rate_type='30_yr_fixed',
                rate=0.0606,
                points=None,
                change=None,
                rate_date=date.today() + timedelta(days=1),
            ),
        ]
        with pytest.raises(ValidationError, match="is in the future"):
            self.scraper.validate_rate_data(rates)


class TestFetchCurrentRates:
    """Tests for fetch_current_rates method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    @patch.object(MortgageNewsDailyScraper, 'fetch_page')
    def test_fetch_current_rates_success(self, mock_fetch):
        """Test successful fetch returns validated rates."""
        mock_fetch.return_value = SAMPLE_HTML

        rates = self.scraper.fetch_current_rates()

        assert len(rates) == 6
        mock_fetch.assert_called_once()

    @patch.object(MortgageNewsDailyScraper, 'fetch_page')
    def test_fetch_current_rates_fetch_error(self, mock_fetch):
        """Test fetch error is propagated."""
        mock_fetch.side_effect = FetchError("Network error")

        with pytest.raises(FetchError):
            self.scraper.fetch_current_rates()


class TestFetchRatesAsDict:
    """Tests for fetch_rates_as_dict method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    @patch.object(MortgageNewsDailyScraper, 'fetch_page')
    def test_fetch_rates_as_dict(self, mock_fetch):
        """Test fetch returns dict with expected keys."""
        mock_fetch.return_value = SAMPLE_HTML

        rates_dict = self.scraper.fetch_rates_as_dict()

        assert '30 YR FRM' in rates_dict
        assert '15 YR FRM' in rates_dict
        assert rates_dict['30 YR FRM'] == pytest.approx(0.0606)
        assert rates_dict['15 YR FRM'] == pytest.approx(0.0559)


class TestFetchPage:
    """Tests for fetch_page method."""

    def setup_method(self):
        self.scraper = MortgageNewsDailyScraper()

    @patch('refi_monitor.scrapers.mortgage_news_daily.requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.text = '<html>content</html>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.scraper.fetch_page()

        assert result == '<html>content</html>'

    @patch('refi_monitor.scrapers.mortgage_news_daily.requests.Session.get')
    def test_fetch_page_network_error(self, mock_get):
        """Test network error raises FetchError."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection failed")

        with pytest.raises(FetchError, match="Connection failed"):
            self.scraper.fetch_page()


class TestRateTypeMapping:
    """Tests for rate type mapping constants."""

    def test_all_expected_types_mapped(self):
        """Test all expected rate types have mappings."""
        expected = [
            '30 Yr. Fixed',
            '15 Yr. Fixed',
            '30 Yr. Jumbo',
            '30 Yr. FHA',
            '30 Yr. VA',
            '7/6 SOFR ARM',
        ]
        for rate_type in expected:
            assert rate_type in RATE_TYPE_MAPPING
