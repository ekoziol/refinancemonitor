"""Comprehensive tests for rate monitoring background service.

Tests cover:
- RateFetcher: API fetching, web scraping fallback, database fallback
- RateUpdater: Rate updates, alert evaluation, trigger creation
- Scheduler: Job scheduling and execution
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestRateFetcher:
    """Tests for RateFetcher class."""

    def test_fetch_from_api_success(self):
        """Test successful API rate fetch."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()
        fetcher.api_key = 'test-key'

        mock_response = Mock()
        mock_response.json.return_value = [
            {'30_year_frm': 6.94, '15_year_frm': 6.25, '5_1_arm': 5.80}
        ]
        mock_response.raise_for_status = Mock()

        with patch('refi_monitor.rate_updater.requests.get', return_value=mock_response):
            rates = fetcher._fetch_from_api()

        assert 30 in rates
        assert rates[30] == pytest.approx(0.0694, rel=0.01)
        assert 15 in rates
        assert rates[15] == pytest.approx(0.0625, rel=0.01)

    def test_fetch_from_api_dict_response(self):
        """Test API fetch with dict response format."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()
        fetcher.api_key = 'test-key'

        mock_response = Mock()
        mock_response.json.return_value = {
            'rate30Fixed': 6.94,
            'rate15Fixed': 6.25,
        }
        mock_response.raise_for_status = Mock()

        with patch('refi_monitor.rate_updater.requests.get', return_value=mock_response):
            rates = fetcher._fetch_from_api()

        assert 30 in rates
        assert rates[30] == pytest.approx(0.0694, rel=0.01)

    def test_fetch_from_api_failure_fallback(self):
        """Test fallback to scraping when API fails."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()
        fetcher.api_key = 'test-key'

        # Mock API failure
        with patch('refi_monitor.rate_updater.requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")

            # Mock scraping success
            with patch.object(fetcher, '_fetch_from_mortgage_news_daily', return_value={30: 0.0694}):
                rates = fetcher.fetch_current_rates()

        assert 30 in rates
        assert rates[30] == 0.0694

    def test_fetch_without_api_key(self):
        """Test fetching without API key uses scraper."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()
        fetcher.api_key = None

        with patch.object(fetcher, '_fetch_from_mortgage_news_daily', return_value={30: 0.0680, 15: 0.0620}):
            rates = fetcher.fetch_current_rates()

        assert rates[30] == 0.0680
        assert rates[15] == 0.0620

    def test_fetch_all_sources_fail(self):
        """Test error when all rate sources fail."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()
        fetcher.api_key = None

        with patch.object(fetcher, '_fetch_from_mortgage_news_daily', side_effect=Exception("Scrape failed")):
            with patch.object(fetcher, '_fetch_from_database', return_value={}):
                with pytest.raises(ValueError, match="Failed to fetch mortgage rates"):
                    fetcher.fetch_current_rates()

    def test_fetch_from_database(self):
        """Test fetching rates from database fallback."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()

        # Create mock MortgageRate objects
        mock_rate_30 = Mock()
        mock_rate_30.rate = Decimal('6.94')

        mock_rate_15 = Mock()
        mock_rate_15.rate = Decimal('6.25')

        mock_query = Mock()

        with patch('refi_monitor.rate_updater.MortgageRate') as MockMortgageRate:
            MockMortgageRate.query.filter_by.return_value.order_by.return_value.first.side_effect = [
                mock_rate_30, mock_rate_15
            ]

            rates = fetcher._fetch_from_database()

        assert 30 in rates
        assert 15 in rates

    def test_rate_conversion_percentage_to_decimal(self):
        """Test that percentage rates are correctly converted to decimals."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()
        fetcher.api_key = 'test-key'

        mock_response = Mock()
        # API returns percentage (6.94 means 6.94%)
        mock_response.json.return_value = {'rate30Fixed': 6.94}
        mock_response.raise_for_status = Mock()

        with patch('refi_monitor.rate_updater.requests.get', return_value=mock_response):
            rates = fetcher._fetch_from_api()

        # Should be converted to decimal (0.0694)
        assert rates[30] < 1
        assert rates[30] == pytest.approx(0.0694, rel=0.01)


class TestRateUpdater:
    """Tests for RateUpdater class."""

    def test_update_all_rates_success(self):
        """Test successful rate update."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0694, 15: 0.0625}
        mock_fetcher.store_rates.return_value = 2

        updater = RateUpdater(fetcher=mock_fetcher)

        with patch('refi_monitor.rate_updater.Mortgage_Tracking') as MockTracking:
            MockTracking.query.all.return_value = []

            with patch('refi_monitor.rate_updater.Alert') as MockAlert:
                MockAlert.query.filter.return_value.all.return_value = []

                with patch('refi_monitor.rate_updater.db'):
                    result = updater.update_all_rates()

        assert result['current_rate'] == 0.0694
        assert result['updated'] == 0  # No tracking records
        assert result['alerts_triggered'] == 0

    def test_update_tracking_records(self):
        """Test updating mortgage tracking records."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0694}
        mock_fetcher.store_rates.return_value = 1

        updater = RateUpdater(fetcher=mock_fetcher)

        mock_record = Mock()
        mock_record.mortgage_id = 1

        with patch('refi_monitor.rate_updater.Mortgage_Tracking') as MockTracking:
            MockTracking.query.all.return_value = [mock_record]

            with patch('refi_monitor.rate_updater.Alert') as MockAlert:
                MockAlert.query.filter.return_value.all.return_value = []

                with patch('refi_monitor.rate_updater.db'):
                    result = updater.update_all_rates()

        assert result['updated'] == 1
        assert mock_record.current_rate == 0.0694

    def test_alert_trigger_interest_rate(self):
        """Test triggering an interest rate alert."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0650}  # 6.50%
        mock_fetcher.store_rates.return_value = 1

        updater = RateUpdater(fetcher=mock_fetcher)

        # Create mock alert with target rate of 6.75% (current rate is below target)
        mock_alert = Mock()
        mock_alert.id = 1
        mock_alert.target_term = 360  # 30 years
        mock_alert.target_interest_rate = 0.0675  # 6.75%
        mock_alert.target_monthly_payment = None
        mock_alert.alert_type = 'interest_rate'
        mock_alert.mortgage_id = 1
        mock_alert.estimate_refinance_cost = 3000

        with patch('refi_monitor.rate_updater.Mortgage_Tracking') as MockTracking:
            MockTracking.query.all.return_value = []

            with patch('refi_monitor.rate_updater.Alert') as MockAlert:
                MockAlert.query.filter.return_value.all.return_value = [mock_alert]

                with patch('refi_monitor.rate_updater.Trigger') as MockTrigger:
                    MockTrigger.query.filter.return_value.order_by.return_value.first.return_value = None

                    with patch('refi_monitor.rate_updater.db') as mock_db:
                        result = updater.update_all_rates()

        assert result['alerts_triggered'] == 1

    def test_alert_trigger_monthly_payment(self):
        """Test triggering a monthly payment alert."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0500}  # 5.00%
        mock_fetcher.store_rates.return_value = 1

        updater = RateUpdater(fetcher=mock_fetcher)

        mock_alert = Mock()
        mock_alert.id = 1
        mock_alert.target_term = 360
        mock_alert.target_interest_rate = None
        mock_alert.target_monthly_payment = 2000.0  # Target $2000/month
        mock_alert.alert_type = 'monthly_payment'
        mock_alert.mortgage_id = 1
        mock_alert.estimate_refinance_cost = 3000

        mock_mortgage = Mock()
        mock_mortgage.remaining_principal = 300000

        with patch('refi_monitor.rate_updater.Mortgage_Tracking') as MockTracking:
            MockTracking.query.all.return_value = []

            with patch('refi_monitor.rate_updater.Alert') as MockAlert:
                MockAlert.query.filter.return_value.all.return_value = [mock_alert]

                with patch('refi_monitor.rate_updater.Mortgage') as MockMortgage:
                    MockMortgage.query.get.return_value = mock_mortgage

                    with patch('refi_monitor.rate_updater.Trigger') as MockTrigger:
                        MockTrigger.query.filter.return_value.order_by.return_value.first.return_value = None

                        with patch('refi_monitor.rate_updater.db') as mock_db:
                            result = updater.update_all_rates()

        assert result['alerts_triggered'] == 1

    def test_no_duplicate_triggers_within_24h(self):
        """Test that alerts are not re-triggered within 24 hours."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0650}
        mock_fetcher.store_rates.return_value = 1

        updater = RateUpdater(fetcher=mock_fetcher)

        mock_alert = Mock()
        mock_alert.id = 1
        mock_alert.target_term = 360
        mock_alert.target_interest_rate = 0.0675
        mock_alert.target_monthly_payment = None
        mock_alert.alert_type = 'interest_rate'

        # Recent trigger within 24 hours
        mock_recent_trigger = Mock()
        mock_recent_trigger.alert_trigger_date = datetime.utcnow() - timedelta(hours=12)

        with patch('refi_monitor.rate_updater.Mortgage_Tracking') as MockTracking:
            MockTracking.query.all.return_value = []

            with patch('refi_monitor.rate_updater.Alert') as MockAlert:
                MockAlert.query.filter.return_value.all.return_value = [mock_alert]

                with patch('refi_monitor.rate_updater.Trigger') as MockTrigger:
                    MockTrigger.query.filter.return_value.order_by.return_value.first.return_value = mock_recent_trigger

                    with patch('refi_monitor.rate_updater.db') as mock_db:
                        result = updater.update_all_rates()

        assert result['alerts_triggered'] == 0

    def test_allow_trigger_after_24h(self):
        """Test that alerts can be re-triggered after 24 hours."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0650}
        mock_fetcher.store_rates.return_value = 1

        updater = RateUpdater(fetcher=mock_fetcher)

        mock_alert = Mock()
        mock_alert.id = 1
        mock_alert.target_term = 360
        mock_alert.target_interest_rate = 0.0675
        mock_alert.target_monthly_payment = None
        mock_alert.alert_type = 'interest_rate'
        mock_alert.mortgage_id = 1
        mock_alert.estimate_refinance_cost = 3000

        # Old trigger more than 24 hours ago
        mock_old_trigger = Mock()
        mock_old_trigger.alert_trigger_date = datetime.utcnow() - timedelta(hours=25)

        with patch('refi_monitor.rate_updater.Mortgage_Tracking') as MockTracking:
            MockTracking.query.all.return_value = []

            with patch('refi_monitor.rate_updater.Alert') as MockAlert:
                MockAlert.query.filter.return_value.all.return_value = [mock_alert]

                with patch('refi_monitor.rate_updater.Trigger') as MockTrigger:
                    MockTrigger.query.filter.return_value.order_by.return_value.first.return_value = mock_old_trigger

                    with patch('refi_monitor.rate_updater.db') as mock_db:
                        result = updater.update_all_rates()

        assert result['alerts_triggered'] == 1

    def test_get_current_rates(self):
        """Test getting current rates without full update."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0694, 15: 0.0625}

        updater = RateUpdater(fetcher=mock_fetcher)
        rates = updater.get_current_rates()

        assert rates[30] == 0.0694
        assert rates[15] == 0.0625


class TestRateStorage:
    """Tests for rate storage functionality."""

    def test_store_new_rates(self):
        """Test storing new rates in database."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()
        rates = {30: 0.0694, 15: 0.0625}

        with patch('refi_monitor.rate_updater.MortgageRate') as MockMortgageRate:
            MockMortgageRate.query.filter_by.return_value.first.return_value = None
            MockMortgageRate.query.filter_by.return_value.filter.return_value.order_by.return_value.first.return_value = None

            with patch('refi_monitor.rate_updater.db') as mock_db:
                stored = fetcher.store_rates(rates)

        assert stored == 2

    def test_update_existing_rates(self):
        """Test updating existing rates for today."""
        from refi_monitor.rate_updater import RateFetcher

        fetcher = RateFetcher()
        rates = {30: 0.0694}

        mock_existing = Mock()
        mock_existing.rate = Decimal('6.90')

        with patch('refi_monitor.rate_updater.MortgageRate') as MockMortgageRate:
            MockMortgageRate.query.filter_by.return_value.first.return_value = mock_existing

            with patch('refi_monitor.rate_updater.db') as mock_db:
                stored = fetcher.store_rates(rates)

        assert stored == 0  # No new records, just updated
        assert mock_existing.rate == 6.94  # Updated to new rate


class TestScheduler:
    """Tests for scheduler functionality."""

    def test_init_scheduler(self):
        """Test scheduler initialization."""
        from refi_monitor.scheduler import init_scheduler

        mock_app = Mock()
        mock_app.config.get.side_effect = lambda k, d=None: {
            'RATE_UPDATE_HOUR': 9,
            'RATE_UPDATE_MINUTE': 0
        }.get(k, d)

        with patch('refi_monitor.scheduler.BackgroundScheduler') as MockScheduler:
            mock_scheduler_instance = Mock()
            MockScheduler.return_value = mock_scheduler_instance

            with patch('refi_monitor.scheduler.scheduler', None):
                result = init_scheduler(mock_app)

            mock_scheduler_instance.add_job.assert_called()
            mock_scheduler_instance.start.assert_called_once()

    def test_evaluate_alert_success(self):
        """Test evaluate_alert function."""
        from refi_monitor.scheduler import evaluate_alert

        mock_alert = Mock()
        mock_alert.mortgage_id = 1
        mock_alert.target_term = 360
        mock_alert.target_interest_rate = 0.0700  # 7.00%
        mock_alert.target_monthly_payment = None
        mock_alert.alert_type = 'interest_rate'
        mock_alert.estimate_refinance_cost = 3000

        mock_mortgage = Mock()
        mock_mortgage.remaining_principal = 300000

        mock_fetcher = Mock()
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0680}  # 6.80%, below target

        with patch('refi_monitor.scheduler.Mortgage') as MockMortgage:
            MockMortgage.query.get.return_value = mock_mortgage

            with patch('refi_monitor.scheduler.RateUpdater') as MockUpdater:
                mock_updater_instance = Mock()
                mock_updater_instance.fetcher = mock_fetcher
                MockUpdater.return_value = mock_updater_instance

                triggered, reason, rate = evaluate_alert(mock_alert)

        assert triggered is True
        assert '6.80%' in reason

    def test_evaluate_alert_mortgage_not_found(self):
        """Test evaluate_alert when mortgage not found."""
        from refi_monitor.scheduler import evaluate_alert

        mock_alert = Mock()
        mock_alert.mortgage_id = 999

        with patch('refi_monitor.scheduler.Mortgage') as MockMortgage:
            MockMortgage.query.get.return_value = None

            triggered, reason, rate = evaluate_alert(mock_alert)

        assert triggered is False
        assert reason == "Mortgage not found"

    def test_get_scheduler_status(self):
        """Test getting scheduler status."""
        from refi_monitor.scheduler import get_scheduler_status

        with patch('refi_monitor.scheduler.scheduler') as mock_scheduler:
            mock_job = Mock()
            mock_job.id = 'daily_rate_update'
            mock_job.name = 'Daily Rate Update'
            mock_job.next_run_time = datetime.utcnow()
            mock_job.trigger = 'cron'

            mock_scheduler.get_jobs.return_value = [mock_job]

            status = get_scheduler_status()

        assert len(status) == 1
        assert status[0]['id'] == 'daily_rate_update'


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_rate_update_missing_30_year(self):
        """Test error when 30-year rate is missing."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {15: 0.0625}  # Missing 30-year

        updater = RateUpdater(fetcher=mock_fetcher)

        with pytest.raises(ValueError, match="Primary rate not available"):
            updater.update_all_rates()

    def test_alert_with_zero_term(self):
        """Test handling alerts with zero or None term."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0650}
        mock_fetcher.store_rates.return_value = 1

        updater = RateUpdater(fetcher=mock_fetcher)

        mock_alert = Mock()
        mock_alert.id = 1
        mock_alert.target_term = None  # None term
        mock_alert.target_interest_rate = 0.0675
        mock_alert.target_monthly_payment = None
        mock_alert.alert_type = 'interest_rate'
        mock_alert.mortgage_id = 1
        mock_alert.estimate_refinance_cost = 3000

        with patch('refi_monitor.rate_updater.Mortgage_Tracking') as MockTracking:
            MockTracking.query.all.return_value = []

            with patch('refi_monitor.rate_updater.Alert') as MockAlert:
                MockAlert.query.filter.return_value.all.return_value = [mock_alert]

                with patch('refi_monitor.rate_updater.Trigger') as MockTrigger:
                    MockTrigger.query.filter.return_value.order_by.return_value.first.return_value = None

                    with patch('refi_monitor.rate_updater.db') as mock_db:
                        result = updater.update_all_rates()

        # Should default to 30-year term
        assert result['alerts_triggered'] == 1

    def test_empty_active_alerts(self):
        """Test handling when no active alerts exist."""
        from refi_monitor.rate_updater import RateUpdater, RateFetcher

        mock_fetcher = Mock(spec=RateFetcher)
        mock_fetcher.fetch_current_rates.return_value = {30: 0.0694}
        mock_fetcher.store_rates.return_value = 1

        updater = RateUpdater(fetcher=mock_fetcher)

        with patch('refi_monitor.rate_updater.Mortgage_Tracking') as MockTracking:
            MockTracking.query.all.return_value = []

            with patch('refi_monitor.rate_updater.Alert') as MockAlert:
                MockAlert.query.filter.return_value.all.return_value = []

                with patch('refi_monitor.rate_updater.db'):
                    result = updater.update_all_rates()

        assert result['alerts_triggered'] == 0
        assert result['updated'] == 0
