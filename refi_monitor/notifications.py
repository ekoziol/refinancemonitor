"""Notification service for sending alerts to users."""
from flask import current_app, render_template, url_for
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer


def get_unsubscribe_url(user_email):
    """Generate a secure unsubscribe URL for the user."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(user_email, salt='unsubscribe')
    app_url = current_app.config.get('APP_URL', 'http://localhost:5000')
    return f"{app_url}/unsubscribe/{token}"


def get_app_url():
    """Get the application URL from config or default."""
    return current_app.config.get('APP_URL', 'http://localhost:5000')


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

        # Prepare template context
        app_url = get_app_url()
        trigger_date_str = trigger.alert_trigger_date.strftime("%B %d, %Y at %I:%M %p") if trigger.alert_trigger_date else "N/A"

        template_context = {
            'user_name': user.name,
            'user_email': user.email,
            'mortgage_name': mortgage.name,
            'alert_type': trigger.alert_type.replace('_', ' ').title(),
            'trigger_reason': trigger.alert_trigger_reason,
            'trigger_date': trigger_date_str,
            'remaining_principal': mortgage.remaining_principal,
            'original_rate': mortgage.original_interest_rate,
            'remaining_term': mortgage.remaining_term,
            'target_monthly_payment': alert.target_monthly_payment,
            'target_interest_rate': alert.target_interest_rate,
            'target_term': alert.target_term,
            'app_url': app_url,
            'unsubscribe_url': get_unsubscribe_url(user.email),
            'current_year': datetime.now().year,
            'show_rate_chart': True,
            'rate_chart_url': None,
        }

        # Create HTML email body using file-based template
        html_body = render_template('emails/alert_notification.html', **template_context)

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

To unsubscribe from RefiAlert emails, visit: {get_unsubscribe_url(user.email)}
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

        # Prepare template context
        app_url = get_app_url()
        template_context = {
            'user_email': user_email,
            'alert_id': alert_id,
            'payment_status': payment_status,
            'app_url': app_url,
            'unsubscribe_url': get_unsubscribe_url(user_email),
            'current_year': datetime.now().year,
        }

        # Create HTML email body using file-based template
        html_body = render_template('emails/payment_confirmation.html', **template_context)

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

---
To unsubscribe from RefiAlert emails, visit: {get_unsubscribe_url(user_email)}
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
