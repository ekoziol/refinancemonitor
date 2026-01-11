"""Notification service for sending alerts to users."""
from flask import current_app, render_template_string, url_for
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, EmailLog
from datetime import datetime


def _get_unsubscribe_url(user):
    """Generate unsubscribe URL for a user."""
    token = user.generate_unsubscribe_token()
    db.session.commit()
    return url_for('main_bp.unsubscribe', token=token, _external=True)


def _log_email(user_id, email_type, recipient_email, subject, alert_id=None, trigger_id=None):
    """Create an email log entry."""
    log = EmailLog(
        user_id=user_id,
        email_type=email_type,
        recipient_email=recipient_email,
        subject=subject,
        status='pending',
        alert_id=alert_id,
        trigger_id=trigger_id
    )
    db.session.add(log)
    db.session.commit()
    return log


def _update_email_log(log, status, error_message=None):
    """Update email log status after sending."""
    log.status = status
    if status == 'sent':
        log.sent_at = datetime.utcnow()
    if error_message:
        log.error_message = error_message
    db.session.commit()


def _get_base_styles():
    """Return common CSS styles for email templates."""
    return """
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
        .alert-box { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
        .success-box { background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }
        .info-box { background-color: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; }
        .details { background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }
        .btn { display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; }
        .unsubscribe { font-size: 11px; color: #999; margin-top: 15px; }
        .unsubscribe a { color: #999; }
    """


def send_welcome_email(user_id):
    """
    Send welcome email to a new user.

    Args:
        user_id: ID of the User record
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"User {user_id} not found")
        return False

    if user.email_unsubscribed:
        current_app.logger.info(f"User {user.email} has unsubscribed, skipping welcome email")
        return False

    subject = "Welcome to RefiAlert!"
    log = _log_email(user.id, 'welcome', user.email, subject)
    unsubscribe_url = _get_unsubscribe_url(user)

    try:
        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>{{ styles }}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to RefiAlert!</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ user_name }},</h2>
                    <p>Thank you for joining RefiAlert! We're excited to help you save money on your mortgage.</p>

                    <div class="info-box">
                        <h3>What is RefiAlert?</h3>
                        <p>RefiAlert monitors mortgage rates and notifies you when refinancing could save you money. Set your targets, and we'll do the watching for you.</p>
                    </div>

                    <p><strong>Getting Started:</strong></p>
                    <ol>
                        <li>Add your current mortgage details</li>
                        <li>Set up alerts for your target rate or payment</li>
                        <li>Activate your alert with a subscription</li>
                        <li>We'll notify you when opportunities arise!</li>
                    </ol>

                    <p>Questions? Just reply to this email or visit our help center.</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {{ user_email }} because you created a RefiAlert account.</p>
                    <p class="unsubscribe">
                        <a href="{{ unsubscribe_url }}">Unsubscribe from all emails</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """,
        styles=_get_base_styles(),
        user_name=user.name,
        user_email=user.email,
        unsubscribe_url=unsubscribe_url
        )

        text_body = f"""
Welcome to RefiAlert!

Hi {user.name},

Thank you for joining RefiAlert! We're excited to help you save money on your mortgage.

What is RefiAlert?
RefiAlert monitors mortgage rates and notifies you when refinancing could save you money. Set your targets, and we'll do the watching for you.

Getting Started:
1. Add your current mortgage details
2. Set up alerts for your target rate or payment
3. Activate your alert with a subscription
4. We'll notify you when opportunities arise!

Questions? Just reply to this email or visit our help center.

---
This email was sent to {user.email} because you created a RefiAlert account.
To unsubscribe: {unsubscribe_url}
"""

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        _update_email_log(log, 'sent')
        current_app.logger.info(f"Welcome email sent to {user.email}")
        return True

    except Exception as e:
        _update_email_log(log, 'failed', str(e))
        current_app.logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_alert_created_confirmation(alert_id):
    """
    Send confirmation email when an alert is created.

    Args:
        alert_id: ID of the Alert record
    """
    alert = Alert.query.get(alert_id)
    if not alert:
        current_app.logger.error(f"Alert {alert_id} not found")
        return False

    user = User.query.get(alert.user_id)
    if not user:
        current_app.logger.error(f"User {alert.user_id} not found")
        return False

    if user.email_unsubscribed:
        current_app.logger.info(f"User {user.email} has unsubscribed, skipping alert created email")
        return False

    mortgage = Mortgage.query.get(alert.mortgage_id)
    if not mortgage:
        current_app.logger.error(f"Mortgage {alert.mortgage_id} not found")
        return False

    subject = f"RefiAlert: Alert Created for {mortgage.name}"
    log = _log_email(user.id, 'alert_created', user.email, subject, alert_id=alert.id)
    unsubscribe_url = _get_unsubscribe_url(user)

    try:
        alert_type_display = alert.alert_type.replace('_', ' ').title()

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>{{ styles }}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Alert Created</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ user_name }},</h2>
                    <p>Your refinancing alert has been created for <strong>{{ mortgage_name }}</strong>.</p>

                    <div class="info-box">
                        <h3>Alert Details</h3>
                        <p><strong>Type:</strong> {{ alert_type }}</p>
                        {% if target_monthly_payment %}
                        <p><strong>Target Monthly Payment:</strong> ${{ "{:,.2f}".format(target_monthly_payment) }}</p>
                        {% endif %}
                        {% if target_interest_rate %}
                        <p><strong>Target Interest Rate:</strong> {{ "{:.2f}".format(target_interest_rate) }}%</p>
                        {% endif %}
                        <p><strong>Target Term:</strong> {{ target_term }} months</p>
                    </div>

                    <div class="details">
                        <h3>Current Mortgage:</h3>
                        <ul>
                            <li><strong>Remaining Principal:</strong> ${{ "{:,.2f}".format(remaining_principal) }}</li>
                            <li><strong>Current Interest Rate:</strong> {{ "{:.2f}".format(original_rate) }}%</li>
                            <li><strong>Remaining Term:</strong> {{ remaining_term }} months</li>
                        </ul>
                    </div>

                    {% if payment_status != 'active' %}
                    <div class="alert-box">
                        <p><strong>Action Required:</strong> Complete payment to activate this alert. Your alert won't trigger until payment is confirmed.</p>
                    </div>
                    {% else %}
                    <div class="success-box">
                        <p>Your alert is <strong>active</strong> and we're monitoring rates for you!</p>
                    </div>
                    {% endif %}
                </div>
                <div class="footer">
                    <p>Log in to your account to manage your alerts.</p>
                    <p class="unsubscribe">
                        <a href="{{ unsubscribe_url }}">Unsubscribe from all emails</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """,
        styles=_get_base_styles(),
        user_name=user.name,
        mortgage_name=mortgage.name,
        alert_type=alert_type_display,
        target_monthly_payment=alert.target_monthly_payment,
        target_interest_rate=alert.target_interest_rate,
        target_term=alert.target_term,
        remaining_principal=mortgage.remaining_principal,
        original_rate=mortgage.original_interest_rate,
        remaining_term=mortgage.remaining_term,
        payment_status=alert.payment_status,
        unsubscribe_url=unsubscribe_url
        )

        text_body = f"""
Alert Created

Hi {user.name},

Your refinancing alert has been created for {mortgage.name}.

Alert Details:
- Type: {alert_type_display}
"""
        if alert.target_monthly_payment:
            text_body += f"- Target Monthly Payment: ${alert.target_monthly_payment:,.2f}\n"
        if alert.target_interest_rate:
            text_body += f"- Target Interest Rate: {alert.target_interest_rate:.2f}%\n"
        text_body += f"- Target Term: {alert.target_term} months\n"

        text_body += f"""
Current Mortgage:
- Remaining Principal: ${mortgage.remaining_principal:,.2f}
- Current Interest Rate: {mortgage.original_interest_rate:.2f}%
- Remaining Term: {mortgage.remaining_term} months
"""

        if alert.payment_status != 'active':
            text_body += "\nAction Required: Complete payment to activate this alert.\n"
        else:
            text_body += "\nYour alert is active and we're monitoring rates for you!\n"

        text_body += f"""
---
Log in to your account to manage your alerts.
To unsubscribe: {unsubscribe_url}
"""

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        _update_email_log(log, 'sent')
        current_app.logger.info(f"Alert created confirmation sent to {user.email} for alert {alert_id}")
        return True

    except Exception as e:
        _update_email_log(log, 'failed', str(e))
        current_app.logger.error(f"Failed to send alert created confirmation to {user.email}: {str(e)}")
        return False


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

    if user.email_unsubscribed:
        current_app.logger.info(f"User {user.email} has unsubscribed, skipping alert notification")
        return False

    mortgage = Mortgage.query.get(alert.mortgage_id)
    if not mortgage:
        current_app.logger.error(f"Mortgage {alert.mortgage_id} not found")
        return False

    # Check if user has paid subscription
    if not alert.payment_status or alert.payment_status != 'active':
        current_app.logger.info(f"Alert {alert.id} is not active, skipping notification")
        return False

    subject = f"RefiAlert: Refinancing Opportunity for {mortgage.name}"
    log = _log_email(user.id, 'alert_triggered', user.email, subject, alert_id=alert.id, trigger_id=trigger.id)
    unsubscribe_url = _get_unsubscribe_url(user)

    try:
        # Create HTML email body
        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>{{ styles }}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>RefiAlert Notification</h1>
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
                    <p class="unsubscribe">
                        <a href="{{ unsubscribe_url }}">Unsubscribe from all emails</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """,
        styles=_get_base_styles(),
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
        target_term=alert.target_term,
        unsubscribe_url=unsubscribe_url
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

        text_body += f"""
This is an excellent opportunity to save money on your mortgage. We recommend contacting your lender or a mortgage broker to discuss refinancing options.

Next Steps:
1. Review current market rates
2. Calculate potential savings using our calculator
3. Contact lenders for refinancing quotes
4. Compare closing costs vs. long-term savings

---
This alert was generated automatically by RefiAlert based on your alert settings.
To manage your alerts or update your preferences, please log in to your account.
To unsubscribe: {unsubscribe_url}
"""

        # Send email
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        _update_email_log(log, 'sent')
        current_app.logger.info(f"Alert notification sent to {user.email} for trigger {trigger_id}")
        return True

    except Exception as e:
        _update_email_log(log, 'failed', str(e))
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
    user = User.query.filter_by(email=user_email).first()
    if not user:
        current_app.logger.error(f"User with email {user_email} not found")
        return False

    if user.email_unsubscribed:
        current_app.logger.info(f"User {user_email} has unsubscribed, skipping payment confirmation")
        return False

    subject = "RefiAlert: Payment Confirmation"
    log = _log_email(user.id, 'payment_confirmation', user_email, subject, alert_id=alert_id)
    unsubscribe_url = _get_unsubscribe_url(user)

    try:
        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>{{ styles }}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Payment Confirmed</h1>
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
                    <p class="unsubscribe">
                        <a href="{{ unsubscribe_url }}">Unsubscribe from all emails</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """,
        styles=_get_base_styles(),
        alert_id=alert_id,
        payment_status=payment_status,
        unsubscribe_url=unsubscribe_url
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

---
Questions? Contact us or log in to manage your alerts.
To unsubscribe: {unsubscribe_url}
"""

        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        _update_email_log(log, 'sent')
        current_app.logger.info(f"Payment confirmation sent to {user_email} for alert {alert_id}")
        return True

    except Exception as e:
        _update_email_log(log, 'failed', str(e))
        current_app.logger.error(f"Failed to send payment confirmation to {user_email}: {str(e)}")
        return False


def send_unsubscribe_confirmation(user_id):
    """
    Send confirmation email after user unsubscribes.

    Args:
        user_id: ID of the User record
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"User {user_id} not found")
        return False

    subject = "RefiAlert: You've Been Unsubscribed"
    log = _log_email(user.id, 'unsubscribe_confirmation', user.email, subject)

    try:
        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>{{ styles }}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Unsubscribed</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ user_name }},</h2>
                    <p>You've been successfully unsubscribed from RefiAlert emails.</p>

                    <div class="info-box">
                        <p>You will no longer receive:</p>
                        <ul>
                            <li>Alert trigger notifications</li>
                            <li>Payment confirmations</li>
                            <li>Marketing emails</li>
                        </ul>
                    </div>

                    <p><strong>Important:</strong> Your account and alerts are still active. You can still log in to view your dashboard and manage your settings.</p>

                    <p>Changed your mind? Log in to your account and update your email preferences to start receiving notifications again.</p>
                </div>
                <div class="footer">
                    <p>This is a confirmation of your unsubscribe request. You won't receive further emails unless you resubscribe.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        styles=_get_base_styles(),
        user_name=user.name
        )

        text_body = f"""
Unsubscribed

Hi {user.name},

You've been successfully unsubscribed from RefiAlert emails.

You will no longer receive:
- Alert trigger notifications
- Payment confirmations
- Marketing emails

Important: Your account and alerts are still active. You can still log in to view your dashboard and manage your settings.

Changed your mind? Log in to your account and update your email preferences to start receiving notifications again.

---
This is a confirmation of your unsubscribe request. You won't receive further emails unless you resubscribe.
"""

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        _update_email_log(log, 'sent')
        current_app.logger.info(f"Unsubscribe confirmation sent to {user.email}")
        return True

    except Exception as e:
        _update_email_log(log, 'failed', str(e))
        current_app.logger.error(f"Failed to send unsubscribe confirmation to {user.email}: {str(e)}")
        return False
