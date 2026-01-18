"""Notification service for sending alerts to users."""
from flask import current_app, render_template_string
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, MortgageRate
from datetime import datetime, timedelta
from sqlalchemy import func


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


def send_monthly_report(user_id):
    """
    Send monthly report email to a user with summary of their alerts and market conditions.

    Args:
        user_id: ID of the user to send the report to

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"User {user_id} not found for monthly report")
        return False

    # Get user's active alerts
    active_alerts = Alert.query.filter_by(
        user_id=user_id,
        payment_status='active'
    ).all()

    if not active_alerts:
        current_app.logger.info(f"User {user_id} has no active alerts, skipping monthly report")
        return False

    # Get triggers from the last month
    last_month = datetime.utcnow() - timedelta(days=30)
    recent_triggers = Trigger.query.join(Alert).filter(
        Alert.user_id == user_id,
        Trigger.created_on >= last_month
    ).all()

    # Get current market rates
    latest_rates = {}
    for term in [180, 240, 360]:  # 15, 20, 30 year terms in months
        rate = MortgageRate.query.filter_by(
            term_months=term
        ).order_by(MortgageRate.rate_date.desc()).first()
        if rate:
            latest_rates[term // 12] = rate.rate

    # Build mortgage summaries
    mortgage_summaries = []
    for alert in active_alerts:
        mortgage = Mortgage.query.get(alert.mortgage_id)
        if mortgage:
            mortgage_summaries.append({
                'name': mortgage.name,
                'remaining_principal': mortgage.remaining_principal,
                'current_rate': mortgage.original_interest_rate,
                'remaining_term': mortgage.remaining_term,
                'alert_type': alert.alert_type,
                'target_monthly_payment': alert.target_monthly_payment,
                'target_interest_rate': alert.target_interest_rate
            })

    try:
        report_date = datetime.utcnow().strftime("%B %Y")
        subject = f"RefiAlert: Your Monthly Report for {report_date}"

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #2196F3; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
                .section { background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #2196F3; }
                .rate-box { background-color: #e3f2fd; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .trigger-alert { background-color: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
                table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f5f5f5; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Monthly Report</h1>
                    <p>{{ report_date }}</p>
                </div>
                <div class="content">
                    <h2>Hello, {{ user_name }}!</h2>
                    <p>Here's your monthly summary of mortgage alerts and market conditions.</p>

                    {% if market_rates %}
                    <div class="section">
                        <h3>Current Market Rates</h3>
                        <div class="rate-box">
                            <table>
                                <tr>
                                    <th>Term</th>
                                    <th>Rate</th>
                                </tr>
                                {% for term, rate in market_rates.items() %}
                                <tr>
                                    <td>{{ term }}-Year Fixed</td>
                                    <td>{{ "{:.2f}".format(rate * 100) }}%</td>
                                </tr>
                                {% endfor %}
                            </table>
                        </div>
                    </div>
                    {% endif %}

                    <div class="section">
                        <h3>Your Active Alerts ({{ mortgages|length }})</h3>
                        {% for m in mortgages %}
                        <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee;">
                            <strong>{{ m.name }}</strong><br>
                            <small>
                                Principal: ${{ "{:,.2f}".format(m.remaining_principal) }} |
                                Current Rate: {{ "{:.2f}".format(m.current_rate * 100) }}% |
                                Term: {{ m.remaining_term }} months<br>
                                Alert: {{ m.alert_type.replace('_', ' ').title() }}
                                {% if m.target_monthly_payment %}
                                 - Target Payment: ${{ "{:,.2f}".format(m.target_monthly_payment) }}
                                {% endif %}
                                {% if m.target_interest_rate %}
                                 - Target Rate: {{ "{:.2f}".format(m.target_interest_rate * 100) }}%
                                {% endif %}
                            </small>
                        </div>
                        {% endfor %}
                    </div>

                    {% if triggers %}
                    <div class="section">
                        <h3>Alerts Triggered This Month ({{ triggers|length }})</h3>
                        {% for t in triggers %}
                        <div class="trigger-alert">
                            <strong>{{ t.alert_type.replace('_', ' ').title() }}</strong><br>
                            <small>{{ t.alert_trigger_reason }}</small><br>
                            <small><em>{{ t.alert_trigger_date.strftime("%B %d, %Y") if t.alert_trigger_date else "N/A" }}</em></small>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="section">
                        <h3>Alerts Triggered This Month</h3>
                        <p>No alerts were triggered this month. We continue to monitor rates for you.</p>
                    </div>
                    {% endif %}

                    <p>We'll continue monitoring mortgage rates and notify you when your refinancing conditions are met.</p>
                </div>
                <div class="footer">
                    <p>This monthly report was generated automatically by RefiAlert.</p>
                    <p>To manage your alerts or update your preferences, please log in to your account.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        user_name=user.name,
        report_date=report_date,
        market_rates=latest_rates,
        mortgages=mortgage_summaries,
        triggers=recent_triggers
        )

        # Plain text version
        text_body = f"""
RefiAlert Monthly Report - {report_date}

Hello, {user.name}!

Here's your monthly summary of mortgage alerts and market conditions.

"""
        if latest_rates:
            text_body += "CURRENT MARKET RATES\n"
            text_body += "-" * 30 + "\n"
            for term, rate in latest_rates.items():
                text_body += f"{term}-Year Fixed: {rate * 100:.2f}%\n"
            text_body += "\n"

        text_body += f"YOUR ACTIVE ALERTS ({len(mortgage_summaries)})\n"
        text_body += "-" * 30 + "\n"
        for m in mortgage_summaries:
            text_body += f"\n{m['name']}\n"
            text_body += f"  Principal: ${m['remaining_principal']:,.2f}\n"
            text_body += f"  Current Rate: {m['current_rate'] * 100:.2f}%\n"
            text_body += f"  Alert Type: {m['alert_type'].replace('_', ' ').title()}\n"
            if m['target_monthly_payment']:
                text_body += f"  Target Payment: ${m['target_monthly_payment']:,.2f}\n"
            if m['target_interest_rate']:
                text_body += f"  Target Rate: {m['target_interest_rate'] * 100:.2f}%\n"

        if recent_triggers:
            text_body += f"\nALERTS TRIGGERED THIS MONTH ({len(recent_triggers)})\n"
            text_body += "-" * 30 + "\n"
            for t in recent_triggers:
                text_body += f"\n{t.alert_type.replace('_', ' ').title()}\n"
                text_body += f"  {t.alert_trigger_reason}\n"
                if t.alert_trigger_date:
                    text_body += f"  Date: {t.alert_trigger_date.strftime('%B %d, %Y')}\n"
        else:
            text_body += "\nALERTS TRIGGERED THIS MONTH\n"
            text_body += "-" * 30 + "\n"
            text_body += "No alerts were triggered this month. We continue to monitor rates for you.\n"

        text_body += """
---
This monthly report was generated automatically by RefiAlert.
To manage your alerts or update your preferences, please log in to your account.
"""

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(f"Monthly report sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send monthly report to user {user_id}: {str(e)}")
        return False


def send_all_monthly_reports():
    """
    Send monthly reports to all users with active alerts.

    Returns:
        dict: Summary of reports sent
    """
    # Get all users with active alerts
    users_with_alerts = db.session.query(User.id).join(Alert).filter(
        Alert.payment_status == 'active'
    ).distinct().all()

    sent_count = 0
    failed_count = 0

    for (user_id,) in users_with_alerts:
        try:
            if send_monthly_report(user_id):
                sent_count += 1
            else:
                failed_count += 1
        except Exception as e:
            current_app.logger.error(f"Error sending monthly report to user {user_id}: {e}")
            failed_count += 1

    current_app.logger.info(
        f"Monthly reports complete: sent={sent_count}, failed={failed_count}"
    )

    return {
        'sent': sent_count,
        'failed': failed_count,
        'total': len(users_with_alerts)
    }
