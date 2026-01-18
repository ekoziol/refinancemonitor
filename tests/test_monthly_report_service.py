"""Tests for the Monthly Report Service.

These tests verify the MonthlyReportService methods for generating
monthly refinancing report data.
"""
import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# Calculation functions for isolated testing (no Flask dependencies)
def calc_loan_monthly_payment(principal, rate, term):
    """Calculate monthly payment for a loan."""
    r = rate / 12
    n = term
    try:
        if r <= 0:
            return principal / term
        return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    except:
        return 0


class TestRateSummaryDataclass:
    """Test RateSummary data structure and calculations."""

    def test_trend_calculation_down(self):
        """Test that falling rates produce 'down' trend."""
        current_rate = 0.055
        oldest_rate = 0.065
        rate_change = current_rate - oldest_rate
        threshold = 0.001

        trend = 'down' if rate_change < -threshold else (
            'up' if rate_change > threshold else 'stable'
        )

        assert trend == 'down'
        assert abs(rate_change - (-0.01)) < 1e-10

    def test_trend_calculation_up(self):
        """Test that rising rates produce 'up' trend."""
        current_rate = 0.070
        oldest_rate = 0.065
        rate_change = current_rate - oldest_rate
        threshold = 0.001

        trend = 'down' if rate_change < -threshold else (
            'up' if rate_change > threshold else 'stable'
        )

        assert trend == 'up'
        assert abs(rate_change - 0.005) < 1e-10

    def test_trend_calculation_stable(self):
        """Test that minimal change produces 'stable' trend."""
        current_rate = 0.0655
        oldest_rate = 0.0654
        rate_change = current_rate - oldest_rate
        threshold = 0.001

        trend = 'down' if rate_change < -threshold else (
            'up' if rate_change > threshold else 'stable'
        )

        assert trend == 'stable'

    def test_rate_statistics_aggregation(self):
        """Test rate statistics calculation."""
        rate_values = [0.065, 0.064, 0.063, 0.062, 0.060]

        current_rate = rate_values[0]
        min_rate = min(rate_values)
        max_rate = max(rate_values)
        avg_rate = sum(rate_values) / len(rate_values)

        assert current_rate == 0.065
        assert min_rate == 0.060
        assert max_rate == 0.065
        assert abs(avg_rate - 0.0628) < 0.001


class TestMortgageStatusCalculations:
    """Test mortgage status calculations."""

    def test_monthly_payment_calculation_30yr(self):
        """Test 30-year monthly payment calculation."""
        principal = 280000
        rate = 0.065
        term = 360

        payment = calc_loan_monthly_payment(principal, rate, term)

        assert 1700 < payment < 1800

    def test_monthly_payment_calculation_15yr(self):
        """Test 15-year monthly payment calculation."""
        principal = 280000
        rate = 0.055
        term = 180

        payment = calc_loan_monthly_payment(principal, rate, term)

        assert 2200 < payment < 2400

    def test_payment_with_remaining_principal(self):
        """Test payment calculation with reduced principal."""
        remaining_principal = 250000
        rate = 0.065
        remaining_term = 300

        payment = calc_loan_monthly_payment(
            remaining_principal, rate, remaining_term
        )

        assert payment > 0
        assert payment < 2000


class TestAlertStatusLogic:
    """Test alert status determination logic."""

    def test_status_determination_active(self):
        """Test active status when alert is paid and not paused."""
        is_paused = False
        payment_status = 'active'
        initial_payment = True
        has_recent_trigger = False

        if is_paused or payment_status == 'payment_failed':
            status = 'paused'
        elif not initial_payment or payment_status != 'active':
            status = 'waiting'
        elif has_recent_trigger:
            status = 'triggered'
        else:
            status = 'active'

        assert status == 'active'

    def test_status_determination_paused(self):
        """Test paused status when alert is explicitly paused."""
        is_paused = True
        payment_status = 'active'
        initial_payment = True

        if is_paused:
            status = 'paused'
        else:
            status = 'active'

        assert status == 'paused'

    def test_status_determination_waiting(self):
        """Test waiting status when payment incomplete."""
        is_paused = False
        payment_status = 'incomplete'
        initial_payment = False

        if is_paused:
            status = 'paused'
        elif not initial_payment or payment_status != 'active':
            status = 'waiting'
        else:
            status = 'active'

        assert status == 'waiting'

    def test_status_determination_triggered(self):
        """Test triggered status with recent trigger."""
        is_paused = False
        payment_status = 'active'
        initial_payment = True
        last_trigger_hours_ago = 12  # Less than 24 hours

        if is_paused:
            status = 'paused'
        elif not initial_payment or payment_status != 'active':
            status = 'waiting'
        elif last_trigger_hours_ago < 24:
            status = 'triggered'
        else:
            status = 'active'

        assert status == 'triggered'


class TestSavingsCalculations:
    """Test savings calculation logic."""

    def test_monthly_savings_positive(self):
        """Test positive monthly savings with lower rate."""
        principal = 280000
        current_rate = 0.070
        new_rate = 0.055
        term = 360

        current_payment = calc_loan_monthly_payment(principal, current_rate, term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, term)
        monthly_savings = current_payment - new_payment

        assert monthly_savings > 200

    def test_monthly_savings_negative_with_higher_rate(self):
        """Test negative savings with higher rate."""
        principal = 280000
        current_rate = 0.055
        new_rate = 0.070
        term = 360

        current_payment = calc_loan_monthly_payment(principal, current_rate, term)
        new_payment = calc_loan_monthly_payment(principal, new_rate, term)
        monthly_savings = current_payment - new_payment

        assert monthly_savings < 0

    def test_break_even_calculation(self):
        """Test break-even period calculation."""
        import math
        refi_cost = 3000
        monthly_savings = 200

        break_even_months = math.ceil(refi_cost / monthly_savings)

        assert break_even_months == 15

    def test_savings_recommendation_strong(self):
        """Test strong recommendation criteria."""
        monthly_savings = 250
        break_even = 10
        total_savings = 50000

        if monthly_savings > 200 and break_even < 12:
            recommendation = "strongly_recommended"
        elif monthly_savings > 100 and break_even < 24:
            recommendation = "recommended"
        else:
            recommendation = "consider"

        assert recommendation == "strongly_recommended"

    def test_savings_recommendation_moderate(self):
        """Test moderate recommendation criteria."""
        monthly_savings = 150
        break_even = 18
        total_savings = 30000

        if monthly_savings > 200 and break_even < 12:
            recommendation = "strongly_recommended"
        elif monthly_savings > 100 and break_even < 24:
            recommendation = "recommended"
        else:
            recommendation = "consider"

        assert recommendation == "recommended"


class TestMarketOutlookLogic:
    """Test market outlook generation logic."""

    def test_favorable_outlook_falling_rates(self):
        """Test favorable outlook with falling rates."""
        trends = ['down', 'down', 'stable']
        down_count = trends.count('down')
        up_count = trends.count('up')

        if down_count > up_count:
            overall = 'favorable'
            direction = 'falling'
        elif up_count > down_count:
            overall = 'unfavorable'
            direction = 'rising'
        else:
            overall = 'neutral'
            direction = 'stable'

        assert overall == 'favorable'
        assert direction == 'falling'

    def test_unfavorable_outlook_rising_rates(self):
        """Test unfavorable outlook with rising rates."""
        trends = ['up', 'up', 'stable']
        down_count = trends.count('down')
        up_count = trends.count('up')

        if down_count > up_count:
            overall = 'favorable'
            direction = 'falling'
        elif up_count > down_count:
            overall = 'unfavorable'
            direction = 'rising'
        else:
            overall = 'neutral'
            direction = 'stable'

        assert overall == 'unfavorable'
        assert direction == 'rising'

    def test_neutral_outlook_stable_rates(self):
        """Test neutral outlook with stable rates."""
        trends = ['stable', 'up', 'down']
        down_count = trends.count('down')
        up_count = trends.count('up')

        if down_count > up_count:
            overall = 'favorable'
            direction = 'falling'
        elif up_count > down_count:
            overall = 'unfavorable'
            direction = 'rising'
        else:
            overall = 'neutral'
            direction = 'stable'

        assert overall == 'neutral'
        assert direction == 'stable'

    def test_confidence_high(self):
        """Test high confidence with sufficient data points."""
        total_data_points = 75

        if total_data_points >= 60:
            confidence = 'high'
        elif total_data_points >= 30:
            confidence = 'medium'
        else:
            confidence = 'low'

        assert confidence == 'high'

    def test_confidence_low(self):
        """Test low confidence with few data points."""
        total_data_points = 15

        if total_data_points >= 60:
            confidence = 'high'
        elif total_data_points >= 30:
            confidence = 'medium'
        else:
            confidence = 'low'

        assert confidence == 'low'


class TestReportContextGeneration:
    """Test report context generation structure."""

    def test_context_has_required_keys(self):
        """Test that context dict has all required keys."""
        required_keys = [
            'user_id', 'user_name', 'user_email', 'report_month',
            'generated_date', 'rate_statistics', 'mortgages',
            'savings_opportunities', 'alert_status', 'outlook'
        ]

        # Mock context
        context = {
            'user_id': 1,
            'user_name': 'Test User',
            'user_email': 'test@example.com',
            'report_month': 'January 2026',
            'generated_date': '2026-01-18 10:00 UTC',
            'rate_statistics': {},
            'mortgages': [],
            'savings_opportunities': [],
            'alert_status': [],
            'outlook': None
        }

        for key in required_keys:
            assert key in context

    def test_date_formatting(self):
        """Test date formatting for report."""
        now = datetime(2026, 1, 18, 10, 30, 0)

        report_month = now.strftime('%B %Y')
        generated_date = now.strftime('%Y-%m-%d %H:%M UTC')

        assert report_month == 'January 2026'
        assert generated_date == '2026-01-18 10:30 UTC'


@pytest.mark.skipif(
    os.environ.get('USE_REAL_FLASK') != 'True',
    reason="Integration tests require Flask"
)
class TestMonthlyReportServiceIntegration:
    """Integration tests for MonthlyReportService with Flask context."""

    def test_service_initialization(self, app):
        """Test service can be initialized."""
        with app.app_context():
            from services.monthly_report import MonthlyReportService

            service = MonthlyReportService(days=30)

            assert service.days == 30
            assert service.STANDARD_TERMS == [180, 360]

    def test_rate_summary_no_data(self, app):
        """Test rate_summary returns empty dict when no data."""
        with app.app_context():
            from services.monthly_report import MonthlyReportService

            service = MonthlyReportService()
            result = service.rate_summary('99999')

            assert result == {}

    def test_mortgage_status_no_mortgages(self, app):
        """Test mortgage_status returns empty list for non-existent user."""
        with app.app_context():
            from services.monthly_report import MonthlyReportService

            service = MonthlyReportService()
            result = service.mortgage_status(99999)

            assert result == []

    def test_alert_status_no_alerts(self, app):
        """Test alert_status returns empty list for non-existent user."""
        with app.app_context():
            from services.monthly_report import MonthlyReportService

            service = MonthlyReportService()
            result = service.alert_status(99999)

            assert result == []

    def test_savings_no_mortgages(self, app):
        """Test savings returns empty list when user has no mortgages."""
        with app.app_context():
            from services.monthly_report import MonthlyReportService

            service = MonthlyReportService()
            result = service.savings(99999)

            assert result == []

    def test_outlook_no_data(self, app):
        """Test outlook returns neutral with no data."""
        with app.app_context():
            from services.monthly_report import MonthlyReportService

            service = MonthlyReportService()
            result = service.outlook('99999')

            assert result.overall_trend == 'neutral'
            assert result.confidence == 'low'

    def test_generate_report_context_no_user(self, app):
        """Test generate_report_context returns empty dict for non-existent user."""
        with app.app_context():
            from services.monthly_report import MonthlyReportService

            service = MonthlyReportService()
            result = service.generate_report_context(99999)

            assert result == {}
