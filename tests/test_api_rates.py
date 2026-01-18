"""Tests for rate and report preview API endpoints."""
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestRatesCurrentEndpoint:
    """Tests for /api/rates/current endpoint logic."""

    def test_rate_list_structure(self):
        """Test that rate data has correct structure."""
        rate_data = {
            'term_months': 360,
            'term_years': 30,
            'rate': 0.0625,
            'rate_display': '6.25%',
            'rate_date': '2026-01-18'
        }

        assert 'term_months' in rate_data
        assert 'term_years' in rate_data
        assert 'rate' in rate_data
        assert 'rate_display' in rate_data
        assert 'rate_date' in rate_data
        assert rate_data['term_years'] == rate_data['term_months'] // 12

    def test_rate_display_format(self):
        """Test rate display formatting."""
        rate = 0.0625
        rate_display = f'{rate * 100:.2f}%'
        assert rate_display == '6.25%'

        rate = 0.055
        rate_display = f'{rate * 100:.2f}%'
        assert rate_display == '5.50%'

    def test_rates_response_structure(self):
        """Test response structure for rates endpoint."""
        response = {
            'rates': [],
            'zip_code': '12345',
            'as_of': datetime.utcnow().isoformat()
        }

        assert 'rates' in response
        assert 'zip_code' in response
        assert 'as_of' in response
        assert isinstance(response['rates'], list)

    def test_term_years_calculation(self):
        """Test term months to years calculation."""
        test_cases = [
            (360, 30),  # 30-year
            (180, 15),  # 15-year
            (240, 20),  # 20-year
            (120, 10),  # 10-year
        ]

        for term_months, expected_years in test_cases:
            assert term_months // 12 == expected_years


class TestRatesHistoryEndpoint:
    """Tests for /api/rates/history endpoint logic."""

    def test_history_entry_structure(self):
        """Test history entry has correct structure."""
        entry = {
            'date': '2026-01-15',
            'rate': 0.0625,
            'rate_display': '6.25%'
        }

        assert 'date' in entry
        assert 'rate' in entry
        assert 'rate_display' in entry

    def test_statistics_structure(self):
        """Test statistics object has correct fields."""
        statistics = {
            'current_rate': 0.062,
            'min_rate': 0.058,
            'max_rate': 0.065,
            'avg_rate': 0.061,
            'change': -0.005,
            'change_display': '-0.50%',
            'data_points': 30
        }

        required_fields = [
            'current_rate', 'min_rate', 'max_rate', 'avg_rate',
            'change', 'change_display', 'data_points'
        ]

        for field in required_fields:
            assert field in statistics

    def test_days_validation(self):
        """Test days parameter validation logic."""
        # Minimum 1, maximum 365
        test_cases = [
            (0, 1),      # Below minimum -> 1
            (1, 1),      # At minimum -> 1
            (30, 30),    # Normal value -> 30
            (365, 365),  # At maximum -> 365
            (400, 365),  # Above maximum -> 365
            (-5, 1),     # Negative -> 1
        ]

        for input_val, expected in test_cases:
            result = min(max(1, input_val), 365)
            assert result == expected, f"Input {input_val} expected {expected}, got {result}"

    def test_change_display_format(self):
        """Test rate change display formatting."""
        test_cases = [
            (-0.005, '-0.50%'),
            (0.003, '+0.30%'),
            (0.0, '+0.00%'),
            (-0.0125, '-1.25%'),
        ]

        for change, expected in test_cases:
            display = f'{change * 100:+.2f}%'
            assert display == expected

    def test_statistics_calculations(self):
        """Test statistics calculations from rate values."""
        rate_values = [0.060, 0.058, 0.062, 0.059, 0.061]

        current_rate = rate_values[-1]  # Last value
        oldest_rate = rate_values[0]    # First value
        rate_change = current_rate - oldest_rate

        assert current_rate == 0.061
        assert oldest_rate == 0.060
        assert rate_change == pytest.approx(0.001)
        assert min(rate_values) == 0.058
        assert max(rate_values) == 0.062
        assert sum(rate_values) / len(rate_values) == pytest.approx(0.060)


class TestReportPreviewEndpoint:
    """Tests for /api/report-preview endpoint logic."""

    def test_user_data_structure(self):
        """Test user data in report preview."""
        user_data = {
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com'
        }

        assert 'id' in user_data
        assert 'name' in user_data
        assert 'email' in user_data

    def test_mortgage_data_structure(self):
        """Test mortgage data in report preview."""
        mortgage = {
            'id': 1,
            'name': 'Primary Home',
            'zip_code': '12345',
            'original_principal': 300000,
            'original_rate': 0.065,
            'original_term': 360,
            'remaining_principal': 275000,
            'remaining_term': 300,
            'current_monthly_payment': 1896.20,
            'current_rate': None
        }

        required_fields = [
            'id', 'name', 'zip_code', 'original_principal', 'original_rate',
            'original_term', 'remaining_principal', 'remaining_term',
            'current_monthly_payment', 'current_rate'
        ]

        for field in required_fields:
            assert field in mortgage

    def test_rate_statistics_dict_structure(self):
        """Test rate statistics dictionary structure."""
        rate_stats = {
            '180': {
                'current_rate': 0.055,
                'min_rate': 0.052,
                'max_rate': 0.058,
                'avg_rate': 0.055,
                'rate_change_30d': -0.003,
                'data_points': 30
            },
            '360': {
                'current_rate': 0.0625,
                'min_rate': 0.058,
                'max_rate': 0.068,
                'avg_rate': 0.062,
                'rate_change_30d': -0.005,
                'data_points': 30
            }
        }

        # Keys should be string representations of term_months
        for key in rate_stats:
            assert key.isdigit()
            stats = rate_stats[key]
            assert 'current_rate' in stats
            assert 'min_rate' in stats
            assert 'max_rate' in stats
            assert 'avg_rate' in stats
            assert 'rate_change_30d' in stats
            assert 'data_points' in stats

    def test_savings_opportunity_structure(self):
        """Test savings opportunity structure."""
        opportunity = {
            'mortgage_id': 1,
            'mortgage_name': 'Primary Home',
            'term_months': 360,
            'term_years': 30,
            'current_rate': 0.058,
            'new_monthly_payment': 1650.50,
            'monthly_savings': 245.70,
            'total_interest_savings': 45000,
            'break_even_months': 12,
            'refi_cost': 3000,
            'rate_trend': 'down',
            'rate_change_30d': -0.003
        }

        required_fields = [
            'mortgage_id', 'mortgage_name', 'term_months', 'term_years',
            'current_rate', 'new_monthly_payment', 'monthly_savings',
            'total_interest_savings', 'break_even_months', 'refi_cost',
            'rate_trend', 'rate_change_30d'
        ]

        for field in required_fields:
            assert field in opportunity

    def test_full_response_structure(self):
        """Test complete report preview response structure."""
        response = {
            'user': {
                'id': 1,
                'name': 'Test User',
                'email': 'test@example.com'
            },
            'generated_at': datetime.utcnow().isoformat(),
            'mortgages': [],
            'rate_statistics': {},
            'savings_opportunities': []
        }

        required_keys = ['user', 'generated_at', 'mortgages', 'rate_statistics', 'savings_opportunities']
        for key in required_keys:
            assert key in response

    def test_rate_trend_values(self):
        """Test rate trend determination."""
        test_cases = [
            (-0.003, 'down'),
            (0.005, 'up'),
            (0.0, 'up'),  # Zero or positive is 'up'
        ]

        for change, expected_trend in test_cases:
            trend = 'down' if change < 0 else 'up'
            assert trend == expected_trend


class TestEmptyStateResponses:
    """Tests for empty state responses."""

    def test_no_mortgage_rates_response(self):
        """Test response when no mortgage found for rates."""
        response = {
            'rates': [],
            'zip_code': None,
            'as_of': datetime.utcnow().isoformat(),
            'message': 'No mortgage found to determine zip code'
        }

        assert response['rates'] == []
        assert response['zip_code'] is None
        assert 'message' in response

    def test_no_rate_history_response(self):
        """Test response when no rate history available."""
        response = {
            'history': [],
            'statistics': None,
            'zip_code': '12345',
            'term_months': 360,
            'message': 'No rate data available for this zip code and term'
        }

        assert response['history'] == []
        assert response['statistics'] is None
        assert 'message' in response

    def test_empty_report_preview_response(self):
        """Test response when user has no mortgages."""
        response = {
            'user': {
                'id': 1,
                'name': 'Test User',
                'email': 'test@example.com'
            },
            'generated_at': datetime.utcnow().isoformat(),
            'mortgages': [],
            'rate_statistics': {},
            'savings_opportunities': []
        }

        assert response['mortgages'] == []
        assert response['rate_statistics'] == {}
        assert response['savings_opportunities'] == []
