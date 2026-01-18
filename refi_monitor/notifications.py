"""Notification service for sending alerts to users."""
from flask import current_app, render_template, render_template_string
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, MortgageRate
from .calc import calc_loan_monthly_payment, ipmt_total
from datetime import datetime, timedelta
from sqlalchemy import func, desc


def get_email_context(user=None, alert=None):
    """Get common context variables for email templates."""
    base_url = current_app.config.get('BASE_URL', 'https://refialert.com')
    return {
        'base_url': base_url,
        'dashboard_url': f"{base_url}/dashboard",
        'unsubscribe_url': f"{base_url}/unsubscribe" + (f"?user={user.id}" if user else ""),
        'preferences_url': f"{base_url}/preferences" + (f"?user={user.id}" if user else ""),
        'current_year': datetime.now().year
    }


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

        # Get common email context
        context = get_email_context(user=user, alert=alert)

        # Add template-specific variables
        context.update({
            'user_name': user.name,
            'mortgage_name': mortgage.name,
            'alert_type': trigger.alert_type.replace('_', ' ').title(),
            'trigger_reason': trigger.alert_trigger_reason,
            'trigger_date': trigger.alert_trigger_date.strftime("%B %d, %Y at %I:%M %p") if trigger.alert_trigger_date else "N/A",
            'remaining_principal': mortgage.remaining_principal,
            'original_rate': mortgage.original_interest_rate,
            'remaining_term': mortgage.remaining_term,
            'target_monthly_payment': alert.target_monthly_payment,
            'target_interest_rate': alert.target_interest_rate,
            'target_term': alert.target_term
        })

        # Create HTML email body from template
        html_body = render_template('email/alert_notification.html', **context)

        # Create plain text version from template
        text_body = render_template('email/alert_notification.txt', **context)

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

        # Get common email context
        context = get_email_context()

        # Add template-specific variables
        context.update({
            'alert_id': alert_id,
            'payment_status': payment_status,
            'payment_date': datetime.now().strftime("%B %d, %Y")
        })

        # Create HTML email body from template
        html_body = render_template('email/payment_confirmation.html', **context)

        # Create plain text version from template
        text_body = render_template('email/payment_confirmation.txt', **context)

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


def send_portfolio_summary(user_id):
    """
    Send mortgage portfolio summary email to user.

    Includes: current loan details, payment history, equity position,
    principal paid vs remaining, and amortization progress.

    Args:
        user_id: ID of the user
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"User {user_id} not found")
        return False

    mortgages = Mortgage.query.filter_by(user_id=user_id).all()
    if not mortgages:
        current_app.logger.info(f"No mortgages found for user {user_id}")
        return False

    try:
        # Build mortgage data for template
        mortgage_data = []
        for mortgage in mortgages:
            # Calculate derived values
            original_monthly = calc_loan_monthly_payment(
                mortgage.original_principal,
                mortgage.original_interest_rate,
                mortgage.original_term
            )
            current_monthly = calc_loan_monthly_payment(
                mortgage.remaining_principal,
                mortgage.original_interest_rate,
                mortgage.remaining_term
            )

            # Payment history calculations
            months_elapsed = mortgage.original_term - mortgage.remaining_term
            total_payments_made = original_monthly * months_elapsed

            # Principal calculations
            principal_paid = mortgage.original_principal - mortgage.remaining_principal
            principal_paid_pct = (principal_paid / mortgage.original_principal) * 100

            # Interest calculations
            total_interest_original = ipmt_total(
                mortgage.original_interest_rate,
                mortgage.original_term,
                mortgage.original_principal
            )
            interest_paid = ipmt_total(
                mortgage.original_interest_rate,
                mortgage.original_term,
                mortgage.original_principal,
                list(range(1, months_elapsed + 1)) if months_elapsed > 0 else None
            ) if months_elapsed > 0 else 0
            interest_remaining = total_interest_original - interest_paid

            # Amortization progress
            term_progress_pct = (months_elapsed / mortgage.original_term) * 100

            mortgage_data.append({
                'mortgage': mortgage,
                'original_monthly': original_monthly,
                'current_monthly': current_monthly,
                'months_elapsed': months_elapsed,
                'total_payments_made': total_payments_made,
                'principal_paid': principal_paid,
                'principal_paid_pct': principal_paid_pct,
                'interest_paid': interest_paid,
                'interest_remaining': interest_remaining,
                'term_progress_pct': term_progress_pct,
            })

        subject = f"RefiAlert: Your Mortgage Portfolio Summary"

        html_body = render_template_string(PORTFOLIO_SUMMARY_HTML_TEMPLATE,
            user_name=user.name,
            mortgages=mortgage_data,
            report_date=datetime.now().strftime("%B %d, %Y")
        )

        text_body = render_template_string(PORTFOLIO_SUMMARY_TEXT_TEMPLATE,
            user_name=user.name,
            mortgages=mortgage_data,
            report_date=datetime.now().strftime("%B %d, %Y")
        )

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(f"Portfolio summary sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send portfolio summary to user {user_id}: {str(e)}")
        return False


PORTFOLIO_SUMMARY_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 650px; margin: 0 auto; padding: 20px; }
        .header { background-color: #2c5282; color: white; padding: 25px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 5px 0 0; opacity: 0.9; }
        .content { background-color: #f7fafc; padding: 25px; }
        .mortgage-card { background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .mortgage-header { border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; }
        .mortgage-header h2 { margin: 0; color: #2d3748; font-size: 20px; }
        .section { margin-bottom: 25px; }
        .section-title { font-size: 14px; font-weight: bold; color: #718096; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
        .detail-grid { display: table; width: 100%; }
        .detail-row { display: table-row; }
        .detail-label { display: table-cell; padding: 8px 0; color: #4a5568; width: 55%; }
        .detail-value { display: table-cell; padding: 8px 0; font-weight: bold; color: #2d3748; text-align: right; }
        .progress-bar { background-color: #e2e8f0; border-radius: 10px; height: 20px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; border-radius: 10px; transition: width 0.3s ease; }
        .progress-fill.principal { background: linear-gradient(90deg, #48bb78, #38a169); }
        .progress-fill.term { background: linear-gradient(90deg, #4299e1, #3182ce); }
        .progress-text { font-size: 13px; color: #718096; margin-top: 5px; }
        .highlight-box { background-color: #ebf8ff; border-left: 4px solid #4299e1; padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0; }
        .stat-grid { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px; }
        .stat-box { flex: 1; min-width: 140px; background-color: #f7fafc; border-radius: 8px; padding: 15px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #2c5282; }
        .stat-label { font-size: 12px; color: #718096; margin-top: 5px; }
        .footer { margin-top: 30px; padding: 20px; text-align: center; font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; }
        .green { color: #38a169; }
        .blue { color: #3182ce; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Mortgage Portfolio Summary</h1>
            <p>{{ report_date }}</p>
        </div>
        <div class="content">
            <p>Hello {{ user_name }},</p>
            <p>Here's your complete mortgage portfolio overview:</p>

            {% for item in mortgages %}
            <div class="mortgage-card">
                <div class="mortgage-header">
                    <h2>{{ item.mortgage.name }}</h2>
                </div>

                <!-- Current Loan Details -->
                <div class="section">
                    <div class="section-title">Current Loan Details</div>
                    <div class="detail-grid">
                        <div class="detail-row">
                            <span class="detail-label">Original Principal</span>
                            <span class="detail-value">${{ "{:,.2f}".format(item.mortgage.original_principal) }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Interest Rate</span>
                            <span class="detail-value">{{ "{:.3f}".format(item.mortgage.original_interest_rate * 100) }}%</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Original Term</span>
                            <span class="detail-value">{{ item.mortgage.original_term }} months ({{ (item.mortgage.original_term / 12)|round(1) }} years)</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Monthly Payment</span>
                            <span class="detail-value">${{ "{:,.2f}".format(item.original_monthly) }}</span>
                        </div>
                    </div>
                </div>

                <!-- Payment History -->
                <div class="section">
                    <div class="section-title">Payment History</div>
                    <div class="stat-grid">
                        <div class="stat-box">
                            <div class="stat-value">{{ item.months_elapsed }}</div>
                            <div class="stat-label">Payments Made</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${{ "{:,.0f}".format(item.total_payments_made) }}</div>
                            <div class="stat-label">Total Paid</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{{ item.mortgage.remaining_term }}</div>
                            <div class="stat-label">Payments Left</div>
                        </div>
                    </div>
                </div>

                <!-- Equity Position -->
                <div class="section">
                    <div class="section-title">Equity Position</div>
                    <div class="highlight-box">
                        <div class="detail-grid">
                            <div class="detail-row">
                                <span class="detail-label">Principal Paid (Your Equity)</span>
                                <span class="detail-value green">${{ "{:,.2f}".format(item.principal_paid) }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Remaining Balance</span>
                                <span class="detail-value">${{ "{:,.2f}".format(item.mortgage.remaining_principal) }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Principal Paid vs Remaining -->
                <div class="section">
                    <div class="section-title">Principal Paid vs Remaining</div>
                    <div class="progress-bar">
                        <div class="progress-fill principal" style="width: {{ item.principal_paid_pct }}%;"></div>
                    </div>
                    <div class="progress-text">
                        <span class="green">{{ "{:.1f}".format(item.principal_paid_pct) }}% paid</span> &bull;
                        <span>{{ "{:.1f}".format(100 - item.principal_paid_pct) }}% remaining</span>
                    </div>
                    <div class="detail-grid" style="margin-top: 15px;">
                        <div class="detail-row">
                            <span class="detail-label">Interest Paid to Date</span>
                            <span class="detail-value">${{ "{:,.2f}".format(item.interest_paid) }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Interest Remaining</span>
                            <span class="detail-value">${{ "{:,.2f}".format(item.interest_remaining) }}</span>
                        </div>
                    </div>
                </div>

                <!-- Amortization Progress -->
                <div class="section">
                    <div class="section-title">Amortization Progress</div>
                    <div class="progress-bar">
                        <div class="progress-fill term" style="width: {{ item.term_progress_pct }}%;"></div>
                    </div>
                    <div class="progress-text">
                        <span class="blue">{{ "{:.1f}".format(item.term_progress_pct) }}% complete</span> &bull;
                        <span>{{ item.months_elapsed }} of {{ item.mortgage.original_term }} months</span>
                    </div>
                </div>
            </div>
            {% endfor %}

            <p>This summary is generated automatically based on your current loan data. Log in to your account to view detailed amortization schedules or update your mortgage information.</p>
        </div>
        <div class="footer">
            <p>Generated by RefiAlert | {{ report_date }}</p>
            <p>To manage your mortgages or update your preferences, please log in to your account.</p>
        </div>
    </div>
</body>
</html>
"""


PORTFOLIO_SUMMARY_TEXT_TEMPLATE = """
MORTGAGE PORTFOLIO SUMMARY
{{ report_date }}
================================================================================

Hello {{ user_name }},

Here's your complete mortgage portfolio overview:

{% for item in mortgages %}
--------------------------------------------------------------------------------
{{ item.mortgage.name }}
--------------------------------------------------------------------------------

CURRENT LOAN DETAILS
--------------------
Original Principal:     ${{ "{:,.2f}".format(item.mortgage.original_principal) }}
Interest Rate:          {{ "{:.3f}".format(item.mortgage.original_interest_rate * 100) }}%
Original Term:          {{ item.mortgage.original_term }} months ({{ (item.mortgage.original_term / 12)|round(1) }} years)
Monthly Payment:        ${{ "{:,.2f}".format(item.original_monthly) }}

PAYMENT HISTORY
---------------
Payments Made:          {{ item.months_elapsed }}
Total Paid:             ${{ "{:,.2f}".format(item.total_payments_made) }}
Payments Remaining:     {{ item.mortgage.remaining_term }}

EQUITY POSITION
---------------
Principal Paid (Equity): ${{ "{:,.2f}".format(item.principal_paid) }}
Remaining Balance:       ${{ "{:,.2f}".format(item.mortgage.remaining_principal) }}

PRINCIPAL PAID VS REMAINING
---------------------------
Progress: {{ "{:.1f}".format(item.principal_paid_pct) }}% paid | {{ "{:.1f}".format(100 - item.principal_paid_pct) }}% remaining

[{{ "=" * (item.principal_paid_pct / 2)|int }}{{ "-" * ((100 - item.principal_paid_pct) / 2)|int }}]

Interest Paid to Date:  ${{ "{:,.2f}".format(item.interest_paid) }}
Interest Remaining:     ${{ "{:,.2f}".format(item.interest_remaining) }}

AMORTIZATION PROGRESS
---------------------
Term Progress: {{ "{:.1f}".format(item.term_progress_pct) }}% complete
{{ item.months_elapsed }} of {{ item.mortgage.original_term }} months

[{{ "=" * (item.term_progress_pct / 2)|int }}{{ "-" * ((100 - item.term_progress_pct) / 2)|int }}]

{% endfor %}
================================================================================

This summary is generated automatically based on your current loan data.
Log in to your account to view detailed amortization schedules or update
your mortgage information.

Generated by RefiAlert | {{ report_date }}
"""


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
