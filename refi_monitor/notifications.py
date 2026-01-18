"""Notification service for sending alerts to users."""
from flask import current_app, render_template, render_template_string, url_for
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, EmailLog
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .report_aggregator import ReportData


def log_email(email_type, recipient_email, subject, recipient_user_id=None,
              related_entity_type=None, related_entity_id=None):
    """Create an EmailLog entry for tracking email sends.

    Args:
        email_type: Type of email (verification, alert, payment, password_reset, cancellation)
        recipient_email: Email address of recipient
        subject: Email subject line
        recipient_user_id: Optional user ID of recipient
        related_entity_type: Optional type of related entity (e.g., 'alert', 'trigger')
        related_entity_id: Optional ID of related entity

    Returns:
        EmailLog instance
    """
    email_log = EmailLog(
        email_type=email_type,
        recipient_email=recipient_email,
        recipient_user_id=recipient_user_id,
        subject=subject,
        status='pending',
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        created_on=datetime.utcnow()
    )
    db.session.add(email_log)
    db.session.flush()  # Get the ID without committing
    return email_log


def send_verification_email(user_id, verification_token):
    """
    Send email verification link to newly registered user.

    Args:
        user_id: ID of the User record
        verification_token: The verification token to include in the link
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"User {user_id} not found")
        return False

    try:
        verification_url = url_for(
            'auth_bp.verify_email',
            token=verification_token,
            _external=True
        )

        subject = "RefiAlert: Verify Your Email Address"

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
                .btn { display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
                .warning { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to RefiAlert!</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ user_name }},</h2>
                    <p>Thank you for signing up for RefiAlert! To complete your registration and start creating mortgage alerts, please verify your email address.</p>

                    <p style="text-align: center;">
                        <a href="{{ verification_url }}" class="btn">Verify Email Address</a>
                    </p>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 4px;">{{ verification_url }}</p>

                    <div class="warning">
                        <strong>Note:</strong> This link will expire in 24 hours. If you didn't create an account with RefiAlert, you can safely ignore this email.
                    </div>
                </div>
                <div class="footer">
                    <p>This email was sent by RefiAlert. If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        user_name=user.name,
        verification_url=verification_url
        )

        text_body = f"""
Welcome to RefiAlert!

Hi {user.name},

Thank you for signing up for RefiAlert! To complete your registration and start creating mortgage alerts, please verify your email address.

Click here to verify: {verification_url}

Note: This link will expire in 24 hours. If you didn't create an account with RefiAlert, you can safely ignore this email.

---
This email was sent by RefiAlert.
"""

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        # Log the email before sending
        email_log = log_email(
            email_type='verification',
            recipient_email=user.email,
            subject=subject,
            recipient_user_id=user.id,
            related_entity_type='user',
            related_entity_id=user.id
        )

        mail.send(msg)
        email_log.mark_sent()
        db.session.commit()
        current_app.logger.info(f"Verification email sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        # Log failure if email_log was created
        try:
            if 'email_log' in dir():
                email_log.mark_failed(str(e))
                db.session.commit()
        except Exception:
            db.session.rollback()
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

        # Log the email before sending
        email_log = log_email(
            email_type='alert',
            recipient_email=user.email,
            subject=subject,
            recipient_user_id=user.id,
            related_entity_type='trigger',
            related_entity_id=trigger_id
        )

        mail.send(msg)
        email_log.mark_sent()
        db.session.commit()
        current_app.logger.info(f"Alert notification sent to {user.email} for trigger {trigger_id}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send notification for trigger {trigger_id}: {str(e)}")
        # Log failure if email_log was created
        try:
            if 'email_log' in dir():
                email_log.mark_failed(str(e))
                db.session.commit()
        except Exception:
            db.session.rollback()
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

        # Log the email before sending
        email_log = log_email(
            email_type='payment',
            recipient_email=user_email,
            subject=subject,
            related_entity_type='alert',
            related_entity_id=alert_id
        )

        mail.send(msg)
        email_log.mark_sent()
        db.session.commit()
        current_app.logger.info(f"Payment confirmation sent to {user_email} for alert {alert_id}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send payment confirmation to {user_email}: {str(e)}")
        # Log failure if email_log was created
        try:
            if 'email_log' in dir():
                email_log.mark_failed(str(e))
                db.session.commit()
        except Exception:
            db.session.rollback()
        return False


def send_password_reset_email(user, token):
    """
    Send password reset email to user.

    Args:
        user: User object
        token: Password reset token string
    """
    try:
        reset_url = url_for('auth_bp.reset_password', token=token, _external=True)
        subject = "RefiAlert: Password Reset Request"

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
                .btn { display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                .warning { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hello {{ user_name }},</h2>
                    <p>We received a request to reset your password for your RefiAlert account.</p>

                    <p>Click the button below to reset your password:</p>

                    <p style="text-align: center;">
                        <a href="{{ reset_url }}" class="btn">Reset Password</a>
                    </p>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 5px;">{{ reset_url }}</p>

                    <div class="warning">
                        <strong>Important:</strong> This link will expire in 1 hour for security reasons.
                    </div>

                    <p>If you did not request a password reset, please ignore this email. Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>This email was sent by RefiAlert. If you have any questions, please contact support.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        user_name=user.name,
        reset_url=reset_url
        )

        text_body = f"""
Password Reset Request

Hello {user.name},

We received a request to reset your password for your RefiAlert account.

Click the link below to reset your password:
{reset_url}

Important: This link will expire in 1 hour for security reasons.

If you did not request a password reset, please ignore this email. Your password will remain unchanged.

---
This email was sent by RefiAlert.
"""

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        # Log the email before sending
        email_log = log_email(
            email_type='password_reset',
            recipient_email=user.email,
            subject=subject,
            recipient_user_id=user.id,
            related_entity_type='user',
            related_entity_id=user.id
        )

        mail.send(msg)
        email_log.mark_sent()
        db.session.commit()
        current_app.logger.info(f"Password reset email sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        # Log failure if email_log was created
        try:
            if 'email_log' in dir():
                email_log.mark_failed(str(e))
                db.session.commit()
        except Exception:
            db.session.rollback()
        return False


def send_cancellation_confirmation(user_email, alert_id):
    """
    Send cancellation confirmation email to user.

    Args:
        user_email: User's email address
        alert_id: ID of the canceled alert
    """
    try:
        subject = "RefiAlert: Subscription Canceled"

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #6c757d; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
                .info-box { background-color: #e2e3e5; border-left: 4px solid #6c757d; padding: 15px; margin: 20px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Subscription Canceled</h1>
                </div>
                <div class="content">
                    <div class="info-box">
                        <h2>Your alert has been canceled</h2>
                        <p><strong>Alert ID:</strong> #{{ alert_id }}</p>
                    </div>

                    <p>Your RefiAlert subscription has been successfully canceled. You will no longer receive notifications for this alert.</p>

                    <p>We're sorry to see you go! If you change your mind, you can always create a new alert from your dashboard.</p>

                    <p><strong>What happens now?</strong></p>
                    <ul>
                        <li>Your subscription billing has been stopped</li>
                        <li>You won't receive any more notifications for this alert</li>
                        <li>Your alert data has been archived</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>Questions? Contact us or log in to create a new alert.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        alert_id=alert_id
        )

        text_body = f"""
Subscription Canceled

Your alert has been canceled.
Alert ID: #{alert_id}

Your RefiAlert subscription has been successfully canceled. You will no longer receive notifications for this alert.

We're sorry to see you go! If you change your mind, you can always create a new alert from your dashboard.

What happens now?
- Your subscription billing has been stopped
- You won't receive any more notifications for this alert
- Your alert data has been archived

Questions? Contact us or log in to create a new alert.
"""

        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=text_body,
            html=html_body
        )

        # Log the email before sending
        email_log = log_email(
            email_type='cancellation',
            recipient_email=user_email,
            subject=subject,
            related_entity_type='alert',
            related_entity_id=alert_id
        )

        mail.send(msg)
        email_log.mark_sent()
        db.session.commit()
        current_app.logger.info(f"Cancellation confirmation sent to {user_email} for alert {alert_id}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send cancellation confirmation to {user_email}: {str(e)}")
        # Log failure if email_log was created
        try:
            if 'email_log' in dir():
                email_log.mark_failed(str(e))
                db.session.commit()
        except Exception:
            db.session.rollback()
        return False


def send_monthly_report_email(report_data: 'ReportData'):
    """
    Send monthly refinancing report email to user.

    Args:
        report_data: ReportData object containing user info, rate stats, and savings opportunities.

    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    try:
        subject = f"RefiAlert: Your Monthly Refinancing Report - {report_data.generated_at.strftime('%B %Y')}"

        # Prepare template context
        template_context = {
            'user_name': report_data.user_name,
            'report_month': report_data.generated_at.strftime('%B %Y'),
            'generated_date': report_data.generated_at.strftime('%B %d, %Y'),
            'rate_statistics': report_data.rate_statistics,
            'mortgages': report_data.mortgages,
            'savings_opportunities': report_data.savings_opportunities,
            'dashboard_url': url_for('main_bp.dashboard', _external=True),
            'preferences_url': url_for('main_bp.dashboard', _external=True),
        }

        # Render templates from files
        html_body = render_template('emails/monthly_report.html', **template_context)
        text_body = render_template('emails/monthly_report.txt', **template_context)

        msg = Message(
            subject=subject,
            recipients=[report_data.user_email],
            body=text_body,
            html=html_body
        )

        # Log the email before sending
        email_log = log_email(
            email_type='monthly_report',
            recipient_email=report_data.user_email,
            subject=subject,
            recipient_user_id=report_data.user_id,
            related_entity_type='user',
            related_entity_id=report_data.user_id
        )

        mail.send(msg)
        email_log.mark_sent()
        db.session.commit()
        current_app.logger.info(f"Monthly report sent to {report_data.user_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send monthly report to {report_data.user_email}: {str(e)}")
        try:
            if 'email_log' in dir():
                email_log.mark_failed(str(e))
                db.session.commit()
        except Exception:
            db.session.rollback()
        return False
