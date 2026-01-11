"""Notification service for sending alerts to users."""
from flask import current_app, render_template_string
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger
from .calc import calc_loan_monthly_payment, ipmt_total
from datetime import datetime


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
