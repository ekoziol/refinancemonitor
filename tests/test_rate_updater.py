"""Tests for rate updater functionality."""
import pytest
from datetime import date, datetime
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from refi_monitor import db, init_app
from refi_monitor.models import MortgageRate
from refi_monitor.rate_updater import RateFetcher, RateUpdater


@pytest.fixture
def app():
    """Create application for testing."""
    app = init_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


class TestRateFetcher:
    """Tests for RateFetcher class."""

    def test_fetch_current_rates(self, app):
        """Test fetching current rates returns expected structure."""
        with app.app_context():
            fetcher = RateFetcher()
            rates = fetcher.fetch_current_rates()

            assert '30 YR FRM' in rates
            assert '15 YR FRM' in rates
            assert isinstance(rates['30 YR FRM'], float)

    def test_store_rate(self, app):
        """Test storing a rate to the database."""
        with app.app_context():
            fetcher = RateFetcher()
            stored_rate = fetcher.store_rate(
                rate_type='30_year_fixed',
                rate=6.875,
                points=0.70,
                apr=7.125
            )
            db.session.commit()

            # Verify stored
            saved_rate = MortgageRate.query.first()
            assert saved_rate is not None
            assert saved_rate.rate == Decimal('6.875')
            assert saved_rate.points == Decimal('0.70')

    def test_store_rate_updates_existing(self, app):
        """Test storing a rate updates existing record for same date/type."""
        with app.app_context():
            fetcher = RateFetcher()

            # Store first rate
            fetcher.store_rate(rate_type='30_year_fixed', rate=6.875)
            db.session.commit()

            # Store updated rate for same day
            fetcher.store_rate(rate_type='30_year_fixed', rate=6.750)
            db.session.commit()

            # Should only be one record
            rates = MortgageRate.query.all()
            assert len(rates) == 1
            assert rates[0].rate == Decimal('6.75')

    def test_get_latest_rate(self, app):
        """Test getting the latest rate."""
        with app.app_context():
            fetcher = RateFetcher()

            # Store some rates
            fetcher.store_rate(rate_type='30_year_fixed', rate=6.875)
            db.session.commit()

            latest = fetcher.get_latest_rate('30_year_fixed')
            assert latest is not None
            assert latest.rate == Decimal('6.875')

    def test_get_latest_rate_returns_none_when_empty(self, app):
        """Test get_latest_rate returns None when no rates exist."""
        with app.app_context():
            fetcher = RateFetcher()
            latest = fetcher.get_latest_rate('30_year_fixed')
            assert latest is None

    def test_get_rate_history(self, app):
        """Test getting rate history."""
        with app.app_context():
            fetcher = RateFetcher()

            # Store a rate
            fetcher.store_rate(rate_type='30_year_fixed', rate=6.875)
            db.session.commit()

            history = fetcher.get_rate_history('30_year_fixed', days=30)
            assert len(history) == 1
            assert history[0].rate == Decimal('6.875')


class TestRateUpdater:
    """Tests for RateUpdater class."""

    def test_update_all_rates_stores_to_mortgage_rate(self, app):
        """Test that update_all_rates stores rates to MortgageRate table."""
        with app.app_context():
            updater = RateUpdater()
            result = updater.update_all_rates()

            # Should have stored rates
            rates = MortgageRate.query.all()
            assert len(rates) > 0

            # Should have 30-year fixed stored
            rate_30yr = MortgageRate.query.filter_by(
                rate_type='30_year_fixed'
            ).first()
            assert rate_30yr is not None

    def test_update_all_rates_returns_stats(self, app):
        """Test update_all_rates returns statistics."""
        with app.app_context():
            updater = RateUpdater()
            result = updater.update_all_rates()

            assert 'updated' in result
            assert 'alerts_triggered' in result
            assert 'current_rate' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
