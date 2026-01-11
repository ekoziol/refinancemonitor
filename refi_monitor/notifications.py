"""Notification service for sending alerts to users."""
from flask import current_app, render_template_string
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, MortgageRate
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from decimal import Decimal


def send_alert_notification(trigger_id):
    """
    Send email notification when an alert is triggered.

    Args:
        trigger_id: ID of the Trigger record
    """
    trigger = Trigger.query.get(trigger_id)
    if not trigger:
        current_app.logger.error(f"Trigger {trigger_id} not found")
        return False

    alert = Alert.query.get(trigger.alert_id)
    if not alert:
        current_app.logger.error(f"Alert {alert.id} not found")
        return False

    user = User.query.get(alert.user_id)
    if not user:
        current_app.logger.error(f"User {alert.user_id} not found")
        return False

    mortgage = Mortgage.query.get(alert.mortgage_id)
    if not mortgage:
        current_app.logger.error(f"Mortgage {alert.mortgage_id} not found")
        return False

    # Check if user has paid subscription
    if not alert.payment_status or alert.payment_status != 'active':
        current_app.logger.info(f"Alert {alert.id} is not active, skipping notification")
        return False

    try:
        # Build email content
        subject = f"RefiAlert: Refinancing Opportunity for {mortgage.name}"

        # Create HTML email body
        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
                .alert-box { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
                .details { background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
                .btn { display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 RefiAlert Notification</h1>
                </div>
                <div class="content">
                    <h2>Great News, {{ user_name }}!</h2>
                    <p>Your refinancing alert has been triggered for <strong>{{ mortgage_name }}</strong>.</p>

                    <div class="alert-box">
                        <strong>Alert Type:</strong> {{ alert_type }}<br>
                        <strong>Reason:</strong> {{ trigger_reason }}<br>
                        <strong>Date:</strong> {{ trigger_date }}
                    </div>

                    <div class="details">
                        <h3>Current Mortgage Details:</h3>
                        <ul>
                            <li><strong>Remaining Principal:</strong> ${{ "{:,.2f}".format(remaining_principal) }}</li>
                            <li><strong>Current Interest Rate:</strong> {{ "{:.2f}".format(original_rate) }}%</li>
                            <li><strong>Remaining Term:</strong> {{ remaining_term }} months</li>
                        </ul>

                        <h3>Target Refinancing Goals:</h3>
                        <ul>
                            {% if target_monthly_payment %}
                            <li><strong>Target Monthly Payment:</strong> ${{ "{:,.2f}".format(target_monthly_payment) }}</li>
                            {% endif %}
                            {% if target_interest_rate %}
                            <li><strong>Target Interest Rate:</strong> {{ "{:.2f}".format(target_interest_rate) }}%</li>
                            {% endif %}
                            <li><strong>Target Term:</strong> {{ target_term }} months</li>
                        </ul>
                    </div>

                    <p>This is an excellent opportunity to save money on your mortgage. We recommend contacting your lender or a mortgage broker to discuss refinancing options.</p>

                    <p><strong>Next Steps:</strong></p>
                    <ol>
                        <li>Review current market rates</li>
                        <li>Calculate potential savings using our calculator</li>
                        <li>Contact lenders for refinancing quotes</li>
                        <li>Compare closing costs vs. long-term savings</li>
                    </ol>
                </div>
                <div class="footer">
                    <p>This alert was generated automatically by RefiAlert based on your alert settings.</p>
                    <p>To manage your alerts or update your preferences, please log in to your account.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        user_name=user.name,
        mortgage_name=mortgage.name,
        alert_type=trigger.alert_type.replace('_', ' ').title(),
        trigger_reason=trigger.alert_trigger_reason,
        trigger_date=trigger.alert_trigger_date.strftime("%B %d, %Y at %I:%M %p") if trigger.alert_trigger_date else "N/A",
        remaining_principal=mortgage.remaining_principal,
        original_rate=mortgage.original_interest_rate,
        remaining_term=mortgage.remaining_term,
        target_monthly_payment=alert.target_monthly_payment,
        target_interest_rate=alert.target_interest_rate,
        target_term=alert.target_term
        )

        # Create plain text version
        text_body = f"""
RefiAlert Notification

Hello {user.name},

Your refinancing alert has been triggered for {mortgage.name}.

Alert Type: {trigger.alert_type.replace('_', ' ').title()}
Reason: {trigger.alert_trigger_reason}
Date: {trigger.alert_trigger_date.strftime("%B %d, %Y at %I:%M %p") if trigger.alert_trigger_date else "N/A"}

Current Mortgage Details:
- Remaining Principal: ${mortgage.remaining_principal:,.2f}
- Current Interest Rate: {mortgage.original_interest_rate:.2f}%
- Remaining Term: {mortgage.remaining_term} months

Target Refinancing Goals:
"""
        if alert.target_monthly_payment:
            text_body += f"- Target Monthly Payment: ${alert.target_monthly_payment:,.2f}\n"
        if alert.target_interest_rate:
            text_body += f"- Target Interest Rate: {alert.target_interest_rate:.2f}%\n"
        text_body += f"- Target Term: {alert.target_term} months\n"

        text_body += """
This is an excellent opportunity to save money on your mortgage. We recommend contacting your lender or a mortgage broker to discuss refinancing options.

Next Steps:
1. Review current market rates
2. Calculate potential savings using our calculator
3. Contact lenders for refinancing quotes
4. Compare closing costs vs. long-term savings

---
This alert was generated automatically by RefiAlert based on your alert settings.
To manage your alerts or update your preferences, please log in to your account.
"""

        # Send email
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(f"Alert notification sent to {user.email} for trigger {trigger_id}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send notification for trigger {trigger_id}: {str(e)}")
        return False


def send_payment_confirmation(user_email, alert_id, payment_status):
    """
    Send payment confirmation email to user.

    Args:
        user_email: User's email address
        alert_id: ID of the alert
        payment_status: Status of the payment (e.g., 'active', 'paid')
    """
    try:
        subject = "RefiAlert: Payment Confirmation"

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
                .success-box { background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💳 Payment Confirmed</h1>
                </div>
                <div class="content">
                    <div class="success-box">
                        <h2>Thank you for your payment!</h2>
                        <p>Your RefiAlert subscription is now <strong>{{ payment_status }}</strong>.</p>
                        <p><strong>Alert ID:</strong> #{{ alert_id }}</p>
                    </div>

                    <p>Your alert is now active and we'll monitor mortgage rates for you. You'll receive email notifications when your refinancing conditions are met.</p>

                    <p><strong>What happens next?</strong></p>
                    <ul>
                        <li>We'll continuously monitor market rates</li>
                        <li>Your alert will be evaluated against current conditions</li>
                        <li>You'll receive immediate notifications when opportunities arise</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>Questions? Contact us or log in to manage your alerts.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        alert_id=alert_id,
        payment_status=payment_status
        )

        text_body = f"""
Payment Confirmed

Thank you for your payment!

Your RefiAlert subscription is now {payment_status}.
Alert ID: #{alert_id}

Your alert is now active and we'll monitor mortgage rates for you. You'll receive email notifications when your refinancing conditions are met.

What happens next?
- We'll continuously monitor market rates
- Your alert will be evaluated against current conditions
- You'll receive immediate notifications when opportunities arise

Questions? Contact us or log in to manage your alerts.
"""

        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(f"Payment confirmation sent to {user_email} for alert {alert_id}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send payment confirmation to {user_email}: {str(e)}")
        return False


def get_market_conditions_data():
    """
    Gather market data for the market conditions report.

    Returns:
        dict: Market data including current rates, trends, and historical comparisons.
    """
    today = datetime.now().date()

    # Rate type display names
    rate_type_names = {
        '30_year_fixed': '30-Year Fixed',
        '15_year_fixed': '15-Year Fixed',
        'FHA_30': 'FHA 30-Year',
        'VA_30': 'VA 30-Year',
        '5_1_ARM': '5/1 ARM',
        '7_1_ARM': '7/1 ARM',
        '10_1_ARM': '10/1 ARM'
    }

    # Get current rates (most recent date with data)
    latest_date_query = db.session.query(func.max(MortgageRate.date)).scalar()
    if not latest_date_query:
        return None

    current_rates = MortgageRate.query.filter_by(date=latest_date_query).all()
    current_rates_dict = {r.rate_type: r for r in current_rates}

    # Calculate trend periods
    periods = {
        '30_day': today - timedelta(days=30),
        '60_day': today - timedelta(days=60),
        '90_day': today - timedelta(days=90),
        '1_year': today - timedelta(days=365)
    }

    # Get historical rates for each period
    def get_rate_for_date(rate_type, target_date):
        """Get the rate closest to target_date (within 7 days)."""
        rate = MortgageRate.query.filter(
            MortgageRate.rate_type == rate_type,
            MortgageRate.date <= target_date,
            MortgageRate.date >= target_date - timedelta(days=7)
        ).order_by(desc(MortgageRate.date)).first()
        return rate

    # Build rate data with trends
    rate_data = []
    for rate_type, display_name in rate_type_names.items():
        current = current_rates_dict.get(rate_type)
        if not current:
            continue

        rate_info = {
            'type': display_name,
            'rate_type_key': rate_type,
            'current_rate': float(current.rate),
            'current_apr': float(current.apr) if current.apr else None,
            'points': float(current.points) if current.points else None,
            'daily_change': float(current.change_from_previous) if current.change_from_previous else 0,
            'trends': {}
        }

        # Calculate trends for each period
        for period_name, period_date in periods.items():
            historical = get_rate_for_date(rate_type, period_date)
            if historical:
                change = float(current.rate) - float(historical.rate)
                rate_info['trends'][period_name] = {
                    'historical_rate': float(historical.rate),
                    'change': round(change, 3),
                    'direction': 'up' if change > 0 else 'down' if change < 0 else 'flat'
                }

        rate_data.append(rate_info)

    # Determine overall market direction based on 30-year fixed trend
    market_direction = 'stable'
    thirty_year_data = next((r for r in rate_data if r['rate_type_key'] == '30_year_fixed'), None)
    if thirty_year_data and '30_day' in thirty_year_data['trends']:
        change_30d = thirty_year_data['trends']['30_day']['change']
        if change_30d <= -0.25:
            market_direction = 'falling'
        elif change_30d >= 0.25:
            market_direction = 'rising'

    return {
        'report_date': today.strftime("%B %d, %Y"),
        'data_date': latest_date_query.strftime("%B %d, %Y"),
        'rates': rate_data,
        'market_direction': market_direction,
        'primary_rate': thirty_year_data
    }


def send_market_conditions_report(user_email, user_name=None):
    """
    Send market conditions report email to a user.

    Args:
        user_email: User's email address
        user_name: Optional user's name for personalization
    """
    market_data = get_market_conditions_data()
    if not market_data:
        current_app.logger.error("No market data available for report")
        return False

    try:
        subject = f"RefiAlert Market Report - {market_data['report_date']}"

        # Build HTML email body
        html_body = render_template_string(MARKET_REPORT_HTML_TEMPLATE, **market_data, user_name=user_name)

        # Build plain text version
        text_body = render_market_report_text(market_data, user_name)

        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(f"Market conditions report sent to {user_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send market report to {user_email}: {str(e)}")
        return False


def render_market_report_text(market_data, user_name=None):
    """Render plain text version of the market conditions report."""
    greeting = f"Hello {user_name}," if user_name else "Hello,"

    text = f"""
RefiAlert Market Conditions Report
{market_data['report_date']}
{'=' * 40}

{greeting}

Here's your mortgage market update with current rates and trends.

CURRENT MORTGAGE RATES
(as of {market_data['data_date']})
{'-' * 30}
"""

    for rate in market_data['rates']:
        daily_indicator = ""
        if rate['daily_change'] > 0:
            daily_indicator = f" (+{rate['daily_change']:.3f})"
        elif rate['daily_change'] < 0:
            daily_indicator = f" ({rate['daily_change']:.3f})"

        text += f"\n{rate['type']}: {rate['current_rate']:.3f}%{daily_indicator}"
        if rate['current_apr']:
            text += f" (APR: {rate['current_apr']:.3f}%)"
        if rate['points']:
            text += f" | {rate['points']:.2f} points"

    text += f"""

RATE TRENDS
{'-' * 30}
"""

    primary = market_data.get('primary_rate')
    if primary:
        text += f"\n30-Year Fixed Mortgage Trends:"
        for period, label in [('30_day', '30-Day'), ('60_day', '60-Day'), ('90_day', '90-Day'), ('1_year', '1-Year')]:
            if period in primary['trends']:
                trend = primary['trends'][period]
                direction = "unchanged" if trend['direction'] == 'flat' else trend['direction']
                sign = "+" if trend['change'] > 0 else ""
                text += f"\n  {label}: {sign}{trend['change']:.3f}% ({direction})"

    text += f"""

MARKET OUTLOOK
{'-' * 30}
"""

    if market_data['market_direction'] == 'falling':
        text += """
Rates are FALLING - This may be a good time to consider refinancing.
Monitor rates closely for optimal timing.
"""
    elif market_data['market_direction'] == 'rising':
        text += """
Rates are RISING - If you're considering refinancing, acting sooner
rather than later may be beneficial.
"""
    else:
        text += """
Rates are STABLE - Market conditions are relatively flat.
Continue monitoring for opportunities.
"""

    text += f"""

ECONOMIC FACTORS TO WATCH
{'-' * 30}
- Federal Reserve interest rate decisions
- Inflation reports (CPI, PCE)
- Employment data and jobs reports
- Housing market indicators
- Treasury yield movements

{'-' * 40}
This report was generated by RefiAlert.
Data sourced from MortgageNewsDaily.

To manage your alerts, log in to your account.
"""

    return text


# HTML Template for Market Conditions Report
MARKET_REPORT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1a5f7a 0%, #2d8659 100%); color: white; padding: 25px; text-align: center; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 24px; }
        .header .date { font-size: 14px; opacity: 0.9; margin-top: 5px; }
        .content { background-color: #f9f9f9; padding: 25px; }
        .section { background-color: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .section-title { font-size: 18px; font-weight: bold; color: #1a5f7a; margin-bottom: 15px; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }
        .rate-table { width: 100%; border-collapse: collapse; }
        .rate-table th { text-align: left; padding: 10px; background-color: #f5f5f5; border-bottom: 2px solid #ddd; font-size: 12px; color: #666; }
        .rate-table td { padding: 12px 10px; border-bottom: 1px solid #eee; }
        .rate-table tr:hover { background-color: #f9f9f9; }
        .rate-value { font-size: 18px; font-weight: bold; color: #1a5f7a; }
        .rate-change { font-size: 12px; margin-left: 5px; }
        .change-up { color: #dc3545; }
        .change-down { color: #28a745; }
        .change-flat { color: #6c757d; }
        .trend-box { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .trend-up { background-color: #fff0f0; color: #dc3545; }
        .trend-down { background-color: #f0fff0; color: #28a745; }
        .trend-flat { background-color: #f5f5f5; color: #6c757d; }
        .outlook-box { padding: 20px; border-radius: 8px; margin: 15px 0; }
        .outlook-falling { background-color: #d4edda; border-left: 4px solid #28a745; }
        .outlook-rising { background-color: #fff3cd; border-left: 4px solid #ffc107; }
        .outlook-stable { background-color: #e2e3e5; border-left: 4px solid #6c757d; }
        .outlook-title { font-weight: bold; font-size: 16px; margin-bottom: 8px; }
        .trend-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px; }
        .trend-item { text-align: center; padding: 10px; background: #f5f5f5; border-radius: 6px; }
        .trend-item .period { font-size: 11px; color: #666; margin-bottom: 4px; }
        .trend-item .value { font-size: 14px; font-weight: bold; }
        .economic-list { list-style: none; padding: 0; margin: 0; }
        .economic-list li { padding: 8px 0; border-bottom: 1px solid #eee; display: flex; align-items: center; }
        .economic-list li:last-child { border-bottom: none; }
        .economic-list .icon { width: 24px; margin-right: 10px; text-align: center; }
        .footer { margin-top: 25px; padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #ddd; }
        .footer a { color: #1a5f7a; text-decoration: none; }
        @media (max-width: 480px) {
            .trend-grid { grid-template-columns: repeat(2, 1fr); }
            .rate-table th, .rate-table td { padding: 8px 5px; font-size: 13px; }
            .rate-value { font-size: 16px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Market Conditions Report</h1>
            <div class="date">{{ report_date }}</div>
        </div>

        <div class="content">
            {% if user_name %}
            <p>Hello {{ user_name }},</p>
            {% endif %}
            <p>Here's your mortgage market update with current rates, trends, and outlook.</p>

            <!-- Current Rates Section -->
            <div class="section">
                <div class="section-title">Current Mortgage Rates</div>
                <p style="font-size: 12px; color: #666; margin-top: -10px;">As of {{ data_date }}</p>
                <table class="rate-table">
                    <thead>
                        <tr>
                            <th>Loan Type</th>
                            <th>Rate</th>
                            <th>APR</th>
                            <th>Points</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for rate in rates %}
                        <tr>
                            <td><strong>{{ rate.type }}</strong></td>
                            <td>
                                <span class="rate-value">{{ "%.3f"|format(rate.current_rate) }}%</span>
                                {% if rate.daily_change != 0 %}
                                <span class="rate-change {% if rate.daily_change > 0 %}change-up{% elif rate.daily_change < 0 %}change-down{% else %}change-flat{% endif %}">
                                    {% if rate.daily_change > 0 %}+{% endif %}{{ "%.3f"|format(rate.daily_change) }}
                                </span>
                                {% endif %}
                            </td>
                            <td>{% if rate.current_apr %}{{ "%.3f"|format(rate.current_apr) }}%{% else %}-{% endif %}</td>
                            <td>{% if rate.points %}{{ "%.2f"|format(rate.points) }}{% else %}-{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- Rate Trends Section -->
            <div class="section">
                <div class="section-title">Rate Trends (30-Year Fixed)</div>
                {% if primary_rate %}
                <p>See how the benchmark 30-year fixed rate has changed:</p>
                <div class="trend-grid">
                    {% for period, label in [('30_day', '30 Days'), ('60_day', '60 Days'), ('90_day', '90 Days'), ('1_year', '1 Year')] %}
                    {% if period in primary_rate.trends %}
                    {% set trend = primary_rate.trends[period] %}
                    <div class="trend-item">
                        <div class="period">{{ label }}</div>
                        <div class="value {% if trend.direction == 'up' %}change-up{% elif trend.direction == 'down' %}change-down{% else %}change-flat{% endif %}">
                            {% if trend.change > 0 %}+{% endif %}{{ "%.3f"|format(trend.change) }}%
                        </div>
                        <span class="trend-box trend-{{ trend.direction }}">
                            {% if trend.direction == 'up' %}Rising{% elif trend.direction == 'down' %}Falling{% else %}Flat{% endif %}
                        </span>
                    </div>
                    {% endif %}
                    {% endfor %}
                </div>
                {% else %}
                <p>Historical trend data not available.</p>
                {% endif %}
            </div>

            <!-- Historical Comparison -->
            <div class="section">
                <div class="section-title">Historical Context</div>
                {% if primary_rate and '1_year' in primary_rate.trends %}
                {% set yr_trend = primary_rate.trends['1_year'] %}
                <p>
                    <strong>One year ago:</strong> The 30-year fixed rate was {{ "%.3f"|format(yr_trend.historical_rate) }}%.
                    <br>
                    <strong>Today:</strong> {{ "%.3f"|format(primary_rate.current_rate) }}%
                    {% if yr_trend.change > 0 %}
                    <span class="change-up">(+{{ "%.3f"|format(yr_trend.change) }}% higher)</span>
                    {% elif yr_trend.change < 0 %}
                    <span class="change-down">({{ "%.3f"|format(yr_trend.change) }}% lower)</span>
                    {% else %}
                    <span class="change-flat">(unchanged)</span>
                    {% endif %}
                </p>
                {% else %}
                <p>Year-over-year comparison data not available.</p>
                {% endif %}
            </div>

            <!-- Market Outlook Section -->
            <div class="section">
                <div class="section-title">Market Outlook</div>
                <div class="outlook-box outlook-{{ market_direction }}">
                    {% if market_direction == 'falling' %}
                    <div class="outlook-title">Rates are Falling</div>
                    <p>Market conditions show rates trending downward. This may be a favorable time to consider refinancing. Continue monitoring rates for optimal timing.</p>
                    {% elif market_direction == 'rising' %}
                    <div class="outlook-title">Rates are Rising</div>
                    <p>Market conditions show rates trending upward. If you're considering refinancing, acting sooner rather than later may help you lock in better rates.</p>
                    {% else %}
                    <div class="outlook-title">Rates are Stable</div>
                    <p>Market conditions are relatively flat. Keep monitoring for changes that could present refinancing opportunities.</p>
                    {% endif %}
                </div>
            </div>

            <!-- Economic Indicators Section -->
            <div class="section">
                <div class="section-title">Economic Factors to Watch</div>
                <p>Key indicators that influence mortgage rates:</p>
                <ul class="economic-list">
                    <li><span class="icon">📊</span> Federal Reserve interest rate decisions</li>
                    <li><span class="icon">💹</span> Inflation reports (CPI, PCE)</li>
                    <li><span class="icon">👷</span> Employment data and jobs reports</li>
                    <li><span class="icon">🏠</span> Housing market indicators</li>
                    <li><span class="icon">📈</span> Treasury yield movements</li>
                </ul>
            </div>
        </div>

        <div class="footer">
            <p>This report was generated by RefiAlert.<br>
            Data sourced from MortgageNewsDaily.</p>
            <p><a href="#">Manage your alerts</a> | <a href="#">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
"""
