"""Notification service for sending alerts to users."""
from flask import current_app, render_template
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger
from datetime import datetime


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
