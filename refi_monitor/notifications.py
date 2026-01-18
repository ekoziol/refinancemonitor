"""Notification service for sending alerts to users."""
from flask import current_app, render_template_string, render_template
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, MortgageRate
from .calc import calc_loan_monthly_payment
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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


def get_rate_trends(zip_code=None):
    """
    Get current mortgage rate trends compared to last month.

    Args:
        zip_code: Optional zip code to filter rates. If None, uses average rates.

    Returns:
        List of dicts with term_label, current_rate, previous_rate, and change.
    """
    trends = []
    term_configs = [
        (180, "15-Year Fixed"),
        (360, "30-Year Fixed"),
    ]

    now = datetime.utcnow()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = current_month_start - relativedelta(months=1)

    for term_months, term_label in term_configs:
        # Get current month's latest rate
        current_query = db.session.query(func.avg(MortgageRate.rate)).filter(
            MortgageRate.term_months == term_months,
            MortgageRate.rate_date >= current_month_start
        )
        if zip_code:
            current_query = current_query.filter(MortgageRate.zip_code == zip_code)
        current_rate = current_query.scalar()

        # Get last month's average rate
        last_month_query = db.session.query(func.avg(MortgageRate.rate)).filter(
            MortgageRate.term_months == term_months,
            MortgageRate.rate_date >= last_month_start,
            MortgageRate.rate_date < current_month_start
        )
        if zip_code:
            last_month_query = last_month_query.filter(MortgageRate.zip_code == zip_code)
        previous_rate = last_month_query.scalar()

        if current_rate is not None:
            change = 0
            if previous_rate is not None:
                change = current_rate - previous_rate

            trends.append({
                'term_label': term_label,
                'term_months': term_months,
                'current_rate': current_rate * 100,  # Convert to percentage
                'previous_rate': (previous_rate * 100) if previous_rate else None,
                'change': change * 100 if previous_rate else 0
            })

    return trends


def calculate_savings_opportunities(user_id, rate_trends):
    """
    Calculate potential savings opportunities for a user's mortgages.

    Args:
        user_id: User ID to calculate savings for
        rate_trends: Current rate trends from get_rate_trends()

    Returns:
        List of savings opportunity dicts
    """
    opportunities = []
    mortgages = Mortgage.query.filter_by(user_id=user_id).all()

    # Build a lookup of current rates by term
    rate_lookup = {trend['term_months']: trend['current_rate'] / 100 for trend in rate_trends}

    for mortgage in mortgages:
        # Find the closest term for comparison
        closest_term = min(rate_lookup.keys(), key=lambda x: abs(x - mortgage.remaining_term), default=None)

        if closest_term is None or closest_term not in rate_lookup:
            continue

        current_market_rate = rate_lookup[closest_term]
        current_mortgage_rate = mortgage.original_interest_rate

        # Only show opportunity if market rate is lower
        if current_market_rate >= current_mortgage_rate:
            continue

        # Calculate current monthly payment
        current_payment = calc_loan_monthly_payment(
            mortgage.remaining_principal,
            current_mortgage_rate,
            mortgage.remaining_term
        )

        # Calculate new monthly payment at market rate
        new_payment = calc_loan_monthly_payment(
            mortgage.remaining_principal,
            current_market_rate,
            closest_term
        )

        monthly_savings = current_payment - new_payment

        # Only show if savings are meaningful (at least $25/month)
        if monthly_savings < 25:
            continue

        lifetime_savings = monthly_savings * closest_term

        term_label = "15-Year Fixed" if closest_term == 180 else "30-Year Fixed"

        opportunities.append({
            'mortgage_name': mortgage.name,
            'mortgage_id': mortgage.id,
            'term_label': term_label,
            'current_rate': current_mortgage_rate * 100,
            'current_market_rate': current_market_rate * 100,
            'current_monthly_payment': current_payment,
            'new_monthly_payment': new_payment,
            'monthly_savings': monthly_savings,
            'lifetime_savings': lifetime_savings
        })

    return opportunities


def send_monthly_digest(user_id, dashboard_url=None):
    """
    Send monthly digest email to a user with rate trends, mortgage status, and savings opportunities.

    Args:
        user_id: ID of the user to send the digest to
        dashboard_url: URL to the user's dashboard (optional)

    Returns:
        True if email sent successfully, False otherwise
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"User {user_id} not found for monthly digest")
        return False

    if not user.email:
        current_app.logger.error(f"User {user_id} has no email address")
        return False

    try:
        # Get user's mortgages
        mortgages = Mortgage.query.filter_by(user_id=user_id).all()

        # Calculate monthly payments for each mortgage
        mortgages_data = []
        for mortgage in mortgages:
            monthly_payment = calc_loan_monthly_payment(
                mortgage.remaining_principal,
                mortgage.original_interest_rate,
                mortgage.remaining_term
            )
            mortgages_data.append({
                'id': mortgage.id,
                'name': mortgage.name,
                'remaining_principal': mortgage.remaining_principal,
                'original_interest_rate': mortgage.original_interest_rate,
                'remaining_term': mortgage.remaining_term,
                'monthly_payment': monthly_payment
            })

        # Get rate trends (use first mortgage's zip code if available)
        zip_code = mortgages[0].zip_code if mortgages else None
        rate_trends = get_rate_trends(zip_code)

        # Calculate savings opportunities
        opportunities = calculate_savings_opportunities(user_id, rate_trends)
        total_monthly_savings = sum(opp['monthly_savings'] for opp in opportunities)

        # Prepare template context
        now = datetime.utcnow()
        report_month = now.strftime("%B %Y")

        if dashboard_url is None:
            dashboard_url = current_app.config.get('DASHBOARD_URL', '#')

        context = {
            'user_name': user.name,
            'report_month': report_month,
            'rate_trends': rate_trends,
            'mortgages': mortgages_data,
            'opportunities': opportunities,
            'total_monthly_savings': total_monthly_savings,
            'dashboard_url': dashboard_url,
            'current_year': now.year
        }

        # Render templates
        html_body = render_template('email/monthly_digest.html', **context)
        text_body = render_template('email/monthly_digest.txt', **context)

        # Build and send email
        subject = f"RefiAlert Monthly Digest - {report_month}"

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(f"Monthly digest sent to {user.email} for user {user_id}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send monthly digest to user {user_id}: {str(e)}")
        return False


def send_monthly_digest_to_all_active_users(dashboard_url=None):
    """
    Send monthly digest to all users with active paid subscriptions.

    Args:
        dashboard_url: URL to the dashboard (optional)

    Returns:
        Tuple of (success_count, failure_count)
    """
    # Get all users with at least one active alert
    active_user_ids = db.session.query(Alert.user_id).filter(
        Alert.payment_status == 'active'
    ).distinct().all()

    success_count = 0
    failure_count = 0

    for (user_id,) in active_user_ids:
        if send_monthly_digest(user_id, dashboard_url):
            success_count += 1
        else:
            failure_count += 1

    current_app.logger.info(
        f"Monthly digest batch complete: {success_count} sent, {failure_count} failed"
    )

    return success_count, failure_count
