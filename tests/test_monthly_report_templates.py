"""Tests for Monthly Report Email Templates.

These tests verify that the email templates render correctly with various
data scenarios including full data, empty sections, and edge cases.
"""
import pytest
import os
import sys
from dataclasses import dataclass
from typing import Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


# Mock dataclasses matching report_aggregator.py structure
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


def has_flask():
    """Check if Flask is available."""
    try:
        import flask
        import jinja2
        return True
    except ImportError:
        return False


@pytest.fixture
def template_app():
    """Create minimal Flask app for template testing."""
    if not has_flask():
        pytest.skip("Flask not available")

    from flask import Flask

    app = Flask(__name__, template_folder=os.path.join(project_root, 'refi_monitor', 'templates'))
    app.config['TESTING'] = True
    return app


@pytest.fixture
def sample_rate_statistics():
    """Create sample rate statistics for testing."""
    return {
        360: RateStatistics(
            current_rate=0.065,
            min_rate=0.060,
            max_rate=0.070,
            avg_rate=0.065,
            rate_change_30d=-0.005,
            data_points=30
        ),
        180: RateStatistics(
            current_rate=0.055,
            min_rate=0.050,
            max_rate=0.060,
            avg_rate=0.055,
            rate_change_30d=0.002,
            data_points=30
        )
    }


@pytest.fixture
def sample_mortgages():
    """Create sample mortgage data for testing."""
    return [
        MortgageStatus(
            mortgage_id=1,
            name="Primary Home",
            zip_code="90210",
            original_principal=400000,
            original_rate=0.07,
            original_term=360,
            remaining_principal=350000,
            remaining_term=336,
            current_monthly_payment=2661.21,
            current_rate=0.065
        ),
        MortgageStatus(
            mortgage_id=2,
            name="Investment Property",
            zip_code="90210",
            original_principal=250000,
            original_rate=0.075,
            original_term=360,
            remaining_principal=240000,
            remaining_term=348,
            current_monthly_payment=1748.04,
            current_rate=0.065
        )
    ]


@pytest.fixture
def sample_savings_opportunities():
    """Create sample savings opportunities for testing."""
    return [
        {
            'term_months': 360,
            'term_years': 30,
            'current_rate': 0.055,
            'rate_trend': 'down',
            'rate_change_30d': -0.005,
            'mortgage_name': 'Primary Home',
            'savings': SavingsCalculation(
                new_rate=0.055,
                new_term=360,
                new_monthly_payment=1987.26,
                monthly_savings=673.95,
                total_interest_savings=89425.00,
                break_even_months=5,
                refi_cost=3000.00
            )
        },
        {
            'term_months': 180,
            'term_years': 15,
            'current_rate': 0.045,
            'rate_trend': 'down',
            'rate_change_30d': -0.002,
            'mortgage_name': 'Primary Home',
            'savings': SavingsCalculation(
                new_rate=0.045,
                new_term=180,
                new_monthly_payment=2677.27,
                monthly_savings=-16.06,
                total_interest_savings=125000.00,
                break_even_months=12,
                refi_cost=3000.00
            )
        }
    ]


class TestMonthlyReportHTMLTemplate:
    """Tests for the HTML email template."""

    def test_template_renders_with_full_data(
        self, template_app, sample_rate_statistics, sample_mortgages, sample_savings_opportunities
    ):
        """Test that HTML template renders correctly with all data."""
        with template_app.app_context():
            from flask import render_template

            html = render_template(
                'emails/monthly_report.html',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics=sample_rate_statistics,
                mortgages=sample_mortgages,
                savings_opportunities=sample_savings_opportunities,
                dashboard_url='https://refialert.com/dashboard',
                preferences_url='https://refialert.com/preferences'
            )

            # Check basic structure
            assert 'Monthly Refinancing Report' in html
            assert 'January 2026' in html
            assert 'John Doe' in html

            # Check rate statistics rendered
            assert '30-Year Fixed' in html
            assert '15-Year Fixed' in html
            assert '6.50%' in html  # current_rate for 360

            # Check mortgages rendered
            assert 'Primary Home' in html
            assert 'Investment Property' in html
            assert '$350,000' in html

            # Check savings opportunities rendered
            assert '$673.95' in html  # monthly_savings
            assert '5 months' in html  # break_even

    def test_template_renders_empty_rate_statistics(self, template_app, sample_mortgages):
        """Test template handles empty rate statistics gracefully."""
        with template_app.app_context():
            from flask import render_template

            html = render_template(
                'emails/monthly_report.html',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics={},
                mortgages=sample_mortgages,
                savings_opportunities=[],
                dashboard_url='https://refialert.com/dashboard',
                preferences_url='https://refialert.com/preferences'
            )

            assert 'Rate data not available' in html
            assert 'Monthly Refinancing Report' in html

    def test_template_renders_empty_mortgages(self, template_app, sample_rate_statistics):
        """Test template handles empty mortgages gracefully."""
        with template_app.app_context():
            from flask import render_template

            html = render_template(
                'emails/monthly_report.html',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics=sample_rate_statistics,
                mortgages=[],
                savings_opportunities=[],
                dashboard_url='https://refialert.com/dashboard',
                preferences_url='https://refialert.com/preferences'
            )

            assert 'No mortgages on file' in html
            assert 'Monthly Refinancing Report' in html

    def test_template_renders_no_savings_opportunities(
        self, template_app, sample_rate_statistics, sample_mortgages
    ):
        """Test template handles no savings opportunities gracefully."""
        with template_app.app_context():
            from flask import render_template

            html = render_template(
                'emails/monthly_report.html',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics=sample_rate_statistics,
                mortgages=sample_mortgages,
                savings_opportunities=[],
                dashboard_url='https://refialert.com/dashboard',
                preferences_url='https://refialert.com/preferences'
            )

            assert 'No refinancing opportunities' in html
            assert "We'll keep monitoring rates" in html

    def test_template_rate_change_colors(self, template_app):
        """Test that rate changes show correct color indicators."""
        with template_app.app_context():
            from flask import render_template

            rate_stats = {
                360: RateStatistics(
                    current_rate=0.065,
                    min_rate=0.060,
                    max_rate=0.070,
                    avg_rate=0.065,
                    rate_change_30d=-0.01,  # Negative = down = green
                    data_points=30
                ),
                180: RateStatistics(
                    current_rate=0.055,
                    min_rate=0.050,
                    max_rate=0.060,
                    avg_rate=0.055,
                    rate_change_30d=0.01,  # Positive = up = red
                    data_points=30
                )
            }

            html = render_template(
                'emails/monthly_report.html',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics=rate_stats,
                mortgages=[],
                savings_opportunities=[],
                dashboard_url='https://refialert.com/dashboard',
                preferences_url='https://refialert.com/preferences'
            )

            assert 'rate-down' in html  # Negative change
            assert 'rate-up' in html    # Positive change


class TestMonthlyReportTextTemplate:
    """Tests for the plain text email template."""

    def test_text_template_renders_with_full_data(
        self, template_app, sample_rate_statistics, sample_mortgages, sample_savings_opportunities
    ):
        """Test that text template renders correctly with all data."""
        with template_app.app_context():
            from flask import render_template

            text = render_template(
                'emails/monthly_report.txt',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics=sample_rate_statistics,
                mortgages=sample_mortgages,
                savings_opportunities=sample_savings_opportunities
            )

            # Check basic structure
            assert 'MONTHLY REFINANCING REPORT' in text
            assert 'January 2026' in text
            assert 'John Doe' in text

            # Check sections exist
            assert 'RATE SUMMARY' in text
            assert 'YOUR MORTGAGES' in text
            assert 'SAVINGS OPPORTUNITIES' in text

            # Check data values
            assert '30-Year Fixed' in text
            assert 'Primary Home' in text
            assert '$673.95' in text  # monthly_savings

    def test_text_template_renders_empty_data(self, template_app):
        """Test text template handles empty data gracefully."""
        with template_app.app_context():
            from flask import render_template

            text = render_template(
                'emails/monthly_report.txt',
                user_name='Jane Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics={},
                mortgages=[],
                savings_opportunities=[]
            )

            assert 'Jane Doe' in text
            assert 'Rate data not available' in text
            assert 'No mortgages on file' in text
            assert 'No refinancing opportunities' in text

    def test_text_template_no_html_tags(
        self, template_app, sample_rate_statistics, sample_mortgages, sample_savings_opportunities
    ):
        """Test that text template contains no HTML tags."""
        with template_app.app_context():
            from flask import render_template

            text = render_template(
                'emails/monthly_report.txt',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics=sample_rate_statistics,
                mortgages=sample_mortgages,
                savings_opportunities=sample_savings_opportunities
            )

            assert '<html>' not in text
            assert '<div>' not in text
            assert '<table>' not in text
            assert '<style>' not in text


class TestTemplateNumberFormatting:
    """Tests for number formatting in templates."""

    def test_currency_formatting(self, template_app):
        """Test that currency values are formatted with commas."""
        with template_app.app_context():
            from flask import render_template

            mortgages = [
                MortgageStatus(
                    mortgage_id=1,
                    name="Test Home",
                    zip_code="90210",
                    original_principal=1250000,
                    original_rate=0.065,
                    original_term=360,
                    remaining_principal=1125000,
                    remaining_term=336,
                    current_monthly_payment=7899.32,
                    current_rate=0.065
                )
            ]

            html = render_template(
                'emails/monthly_report.html',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics={},
                mortgages=mortgages,
                savings_opportunities=[],
                dashboard_url='https://refialert.com/dashboard',
                preferences_url='https://refialert.com/preferences'
            )

            # Check comma-formatted currency
            assert '$1,125,000' in html
            assert '$7,899.32' in html

    def test_percentage_formatting(self, template_app):
        """Test that percentages are formatted correctly."""
        with template_app.app_context():
            from flask import render_template

            rate_stats = {
                360: RateStatistics(
                    current_rate=0.06875,  # 6.875%
                    min_rate=0.0625,
                    max_rate=0.07125,
                    avg_rate=0.06875,
                    rate_change_30d=-0.00125,
                    data_points=30
                )
            }

            html = render_template(
                'emails/monthly_report.html',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics=rate_stats,
                mortgages=[],
                savings_opportunities=[],
                dashboard_url='https://refialert.com/dashboard',
                preferences_url='https://refialert.com/preferences'
            )

            # Check percentage formatting (2 decimal places)
            assert '6.88%' in html or '6.87%' in html  # current_rate


class TestTemplateLimitedOpportunities:
    """Test that templates limit displayed opportunities."""

    def test_shows_only_top_3_opportunities(self, template_app):
        """Test that template shows maximum 3 opportunities."""
        with template_app.app_context():
            from flask import render_template

            # Create 5 opportunities
            opportunities = []
            for i in range(5):
                opportunities.append({
                    'term_months': 360,
                    'term_years': 30,
                    'current_rate': 0.055 + (i * 0.001),
                    'rate_trend': 'down',
                    'rate_change_30d': -0.005,
                    'mortgage_name': f'Property {i+1}',
                    'savings': SavingsCalculation(
                        new_rate=0.055,
                        new_term=360,
                        new_monthly_payment=1987.26,
                        monthly_savings=673.95 + (i * 100),
                        total_interest_savings=89425.00,
                        break_even_months=5,
                        refi_cost=3000.00
                    )
                })

            html = render_template(
                'emails/monthly_report.html',
                user_name='John Doe',
                report_month='January 2026',
                generated_date='January 18, 2026',
                rate_statistics={},
                mortgages=[],
                savings_opportunities=opportunities,
                dashboard_url='https://refialert.com/dashboard',
                preferences_url='https://refialert.com/preferences'
            )

            # Should only show first 3
            assert 'Property 1' in html
            assert 'Property 2' in html
            assert 'Property 3' in html
            assert 'Property 4' not in html
            assert 'Property 5' not in html
