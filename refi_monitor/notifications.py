"""Notification service for sending alerts to users."""
from flask import current_app, render_template_string
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, EmailLog
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

        email_log = EmailLog(
            recipient_email=user.email,
            subject=subject,
            email_type='alert_notification',
            trigger_id=trigger_id,
            alert_id=alert.id,
            user_id=user.id,
            status='sent',
            sent_at=datetime.utcnow(),
            created_on=datetime.utcnow(),
            updated_on=datetime.utcnow()
        )
        db.session.add(email_log)
        db.session.commit()

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send notification for trigger {trigger_id}: {str(e)}")

        try:
            email_log = EmailLog(
                recipient_email=user.email if user else 'unknown',
                subject=subject if 'subject' in locals() else f"Alert notification for trigger {trigger_id}",
                email_type='alert_notification',
                trigger_id=trigger_id,
                alert_id=alert.id if alert else None,
                user_id=user.id if user else None,
                status='failed',
                error_message=str(e),
                created_on=datetime.utcnow(),
                updated_on=datetime.utcnow()
            )
            db.session.add(email_log)
            db.session.commit()
        except Exception as log_error:
            current_app.logger.error(f"Failed to log email error: {str(log_error)}")

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

        alert = Alert.query.get(alert_id)
        email_log = EmailLog(
            recipient_email=user_email,
            subject=subject,
            email_type='payment_confirmation',
            alert_id=alert_id,
            user_id=alert.user_id if alert else None,
            status='sent',
            sent_at=datetime.utcnow(),
            created_on=datetime.utcnow(),
            updated_on=datetime.utcnow()
        )
        db.session.add(email_log)
        db.session.commit()

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send payment confirmation to {user_email}: {str(e)}")

        try:
            email_log = EmailLog(
                recipient_email=user_email,
                subject='RefiAlert: Payment Confirmation',
                email_type='payment_confirmation',
                alert_id=alert_id,
                status='failed',
                error_message=str(e),
                created_on=datetime.utcnow(),
                updated_on=datetime.utcnow()
            )
            db.session.add(email_log)
            db.session.commit()
        except Exception as log_error:
            current_app.logger.error(f"Failed to log email error: {str(log_error)}")

        return False


def send_monthly_report(user_id, report_data):
    """
    Send monthly report email to user.

    Args:
        user_id: ID of the user
        report_data: Dictionary containing report data:
            - period_start: Start date of report period
            - period_end: End date of report period
            - rate_changes: List of rate change events
            - alerts_triggered: Number of alerts triggered
            - savings_opportunities: Calculated potential savings

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"User {user_id} not found for monthly report")
        return False

    try:
        period_start = report_data.get('period_start', 'N/A')
        period_end = report_data.get('period_end', 'N/A')

        subject = f"RefiAlert: Monthly Report ({period_start} - {period_end})"

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #2196F3; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
                .summary-box { background-color: white; border-left: 4px solid #2196F3; padding: 15px; margin: 20px 0; }
                .stat { display: inline-block; width: 45%; margin: 10px 2%; padding: 15px; background: white; border-radius: 5px; text-align: center; }
                .stat-value { font-size: 24px; font-weight: bold; color: #2196F3; }
                .stat-label { font-size: 12px; color: #666; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Monthly Report</h1>
                    <p>{{ period_start }} - {{ period_end }}</p>
                </div>
                <div class="content">
                    <h2>Hello {{ user_name }},</h2>
                    <p>Here's your monthly summary of mortgage market activity and alert status.</p>

                    <div class="summary-box">
                        <div class="stat">
                            <div class="stat-value">{{ alerts_triggered }}</div>
                            <div class="stat-label">Alerts Triggered</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{{ rate_changes|length }}</div>
                            <div class="stat-label">Rate Changes</div>
                        </div>
                    </div>

                    {% if savings_opportunities %}
                    <h3>Potential Savings</h3>
                    <p>Based on current market conditions, you could potentially save <strong>${{ "{:,.2f}".format(savings_opportunities) }}</strong> by refinancing.</p>
                    {% endif %}

                    {% if rate_changes %}
                    <h3>Rate Activity</h3>
                    <ul>
                    {% for change in rate_changes[:5] %}
                        <li>{{ change }}</li>
                    {% endfor %}
                    </ul>
                    {% endif %}

                    <p>Log in to your account to view detailed analytics and manage your alerts.</p>
                </div>
                <div class="footer">
                    <p>This report was generated automatically by RefiAlert.</p>
                    <p>To update your report preferences or unsubscribe, visit your account settings.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        user_name=user.name,
        period_start=period_start,
        period_end=period_end,
        alerts_triggered=report_data.get('alerts_triggered', 0),
        rate_changes=report_data.get('rate_changes', []),
        savings_opportunities=report_data.get('savings_opportunities')
        )

        text_body = f"""
Monthly Report: {period_start} - {period_end}

Hello {user.name},

Here's your monthly summary of mortgage market activity and alert status.

Alerts Triggered: {report_data.get('alerts_triggered', 0)}
Rate Changes: {len(report_data.get('rate_changes', []))}
"""
        if report_data.get('savings_opportunities'):
            text_body += f"\nPotential Savings: ${report_data.get('savings_opportunities'):,.2f}\n"

        text_body += """
Log in to your account to view detailed analytics and manage your alerts.

---
This report was generated automatically by RefiAlert.
To update your report preferences or unsubscribe, visit your account settings.
"""

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(f"Monthly report sent to {user.email} for user {user_id}")

        email_log = EmailLog(
            recipient_email=user.email,
            subject=subject,
            email_type='monthly_report',
            user_id=user_id,
            status='sent',
            sent_at=datetime.utcnow(),
            created_on=datetime.utcnow(),
            updated_on=datetime.utcnow()
        )
        db.session.add(email_log)
        db.session.commit()

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send monthly report to user {user_id}: {str(e)}")

        try:
            email_log = EmailLog(
                recipient_email=user.email if user else 'unknown',
                subject=f"Monthly Report for user {user_id}",
                email_type='monthly_report',
                user_id=user_id,
                status='failed',
                error_message=str(e),
                created_on=datetime.utcnow(),
                updated_on=datetime.utcnow()
            )
            db.session.add(email_log)
            db.session.commit()
        except Exception as log_error:
            current_app.logger.error(f"Failed to log email error: {str(log_error)}")

        return False
