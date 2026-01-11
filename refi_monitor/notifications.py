"""Notification service for sending alerts to users."""
from flask import current_app, render_template_string
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, MortgageRate
from .recommendations import generate_recommendation, Recommendation
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


def send_personalized_recommendation(trigger_id):
    """
    Send personalized refinancing recommendation email.

    This template provides:
    - Clear YES/NO/WAIT recommendation
    - Reasoning based on user's specific situation
    - Optimal timing advice if not recommending action now
    - Concrete action steps if recommendation is YES

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

    # Check subscription status
    if not alert.payment_status or alert.payment_status != 'active':
        current_app.logger.info(f"Alert {alert.id} is not active, skipping notification")
        return False

    try:
        # Get current market rate
        latest_rate = MortgageRate.query.filter_by(
            rate_type='30_year_fixed'
        ).order_by(MortgageRate.date.desc()).first()

        if not latest_rate:
            current_app.logger.error("No market rate data available")
            return False

        current_market_rate = latest_rate.rate / 100  # Convert from percentage

        # Generate personalized recommendation
        rec = generate_recommendation(
            mortgage=mortgage,
            alert=alert,
            current_market_rate=current_market_rate,
            credit_score=user.credit_score
        )

        # Determine recommendation styling
        if rec.recommendation == Recommendation.YES:
            rec_color = "#28a745"  # Green
            rec_icon = "✅"
            rec_bg = "#d4edda"
        elif rec.recommendation == Recommendation.NO:
            rec_color = "#dc3545"  # Red
            rec_icon = "❌"
            rec_bg = "#f8d7da"
        else:  # WAIT
            rec_color = "#ffc107"  # Yellow/Amber
            rec_icon = "⏳"
            rec_bg = "#fff3cd"

        subject = f"RefiAlert: {rec.headline} - {mortgage.name}"

        # Build reasoning list HTML
        reasoning_html = "".join(
            f"<li>{reason}</li>" for reason in rec.reasoning
        )

        # Build action steps HTML
        action_html = "".join(
            f"<li>{step}</li>" for step in rec.action_steps
        )

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #2c3e50; color: white; padding: 25px; text-align: center; }
                .header h1 { margin: 0; font-size: 24px; }
                .recommendation-box {
                    background-color: {{ rec_bg }};
                    border: 3px solid {{ rec_color }};
                    border-radius: 10px;
                    padding: 25px;
                    margin: 25px 0;
                    text-align: center;
                }
                .recommendation-badge {
                    display: inline-block;
                    background-color: {{ rec_color }};
                    color: white;
                    padding: 15px 40px;
                    border-radius: 30px;
                    font-size: 28px;
                    font-weight: bold;
                    margin-bottom: 15px;
                }
                .recommendation-headline {
                    font-size: 20px;
                    color: #333;
                    margin: 10px 0 0 0;
                }
                .content { background-color: #f9f9f9; padding: 25px; }
                .section { background-color: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
                .section h3 { margin-top: 0; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
                .savings-grid { display: table; width: 100%; margin: 15px 0; }
                .savings-row { display: table-row; }
                .savings-cell { display: table-cell; padding: 10px; text-align: center; }
                .savings-value { font-size: 24px; font-weight: bold; color: {{ rec_color }}; }
                .savings-label { font-size: 12px; color: #666; }
                .reasoning-list { padding-left: 20px; }
                .reasoning-list li { margin: 10px 0; }
                .action-list { padding-left: 20px; }
                .action-list li { margin: 12px 0; padding: 8px; background: #f8f9fa; border-radius: 4px; }
                .timing-box { background-color: #e7f3ff; border-left: 4px solid #0066cc; padding: 15px; margin: 20px 0; }
                .details-grid { display: table; width: 100%; }
                .details-row { display: table-row; }
                .details-label { display: table-cell; padding: 8px 0; color: #666; width: 50%; }
                .details-value { display: table-cell; padding: 8px 0; font-weight: bold; text-align: right; }
                .footer { margin-top: 30px; padding: 20px; background: #2c3e50; color: #aaa; font-size: 12px; text-align: center; }
                .footer a { color: #fff; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{ rec_icon }} RefiAlert Recommendation</h1>
                </div>

                <div class="content">
                    <p style="font-size: 16px;">Hi {{ user_name }},</p>
                    <p>Based on current market conditions and your specific mortgage details, here's our personalized recommendation for <strong>{{ mortgage_name }}</strong>:</p>

                    <div class="recommendation-box">
                        <div class="recommendation-badge">{{ recommendation }}</div>
                        <p class="recommendation-headline">{{ headline }}</p>
                    </div>

                    {% if savings %}
                    <div class="section">
                        <h3>Your Potential Savings</h3>
                        <div class="savings-grid">
                            <div class="savings-row">
                                <div class="savings-cell">
                                    <div class="savings-value">${{ "{:,.0f}".format(savings.monthly_savings) }}</div>
                                    <div class="savings-label">Monthly Savings</div>
                                </div>
                                <div class="savings-cell">
                                    <div class="savings-value">${{ "{:,.0f}".format(savings.annual_savings) }}</div>
                                    <div class="savings-label">Annual Savings</div>
                                </div>
                                <div class="savings-cell">
                                    <div class="savings-value">{{ savings.break_even_months }}</div>
                                    <div class="savings-label">Months to Break Even</div>
                                </div>
                            </div>
                        </div>
                        <div class="details-grid" style="margin-top: 15px;">
                            <div class="details-row">
                                <div class="details-label">Current Monthly Payment</div>
                                <div class="details-value">${{ "{:,.2f}".format(savings.current_monthly_payment) }}</div>
                            </div>
                            <div class="details-row">
                                <div class="details-label">New Monthly Payment</div>
                                <div class="details-value">${{ "{:,.2f}".format(savings.new_monthly_payment) }}</div>
                            </div>
                            <div class="details-row">
                                <div class="details-label">Estimated Refinance Cost</div>
                                <div class="details-value">${{ "{:,.0f}".format(savings.refinance_cost) }}</div>
                            </div>
                        </div>
                    </div>
                    {% endif %}

                    <div class="section">
                        <h3>Why This Recommendation?</h3>
                        <ul class="reasoning-list">
                            {{ reasoning_html | safe }}
                        </ul>
                    </div>

                    {% if timing_advice %}
                    <div class="timing-box">
                        <strong>Timing Advice:</strong><br>
                        {{ timing_advice }}
                    </div>
                    {% endif %}

                    <div class="section">
                        <h3>{{ "Recommended Next Steps" if recommendation == "YES" else "What You Can Do" }}</h3>
                        <ol class="action-list">
                            {{ action_html | safe }}
                        </ol>
                    </div>

                    <div class="section">
                        <h3>Your Mortgage Details</h3>
                        <div class="details-grid">
                            <div class="details-row">
                                <div class="details-label">Remaining Principal</div>
                                <div class="details-value">${{ "{:,.2f}".format(remaining_principal) }}</div>
                            </div>
                            <div class="details-row">
                                <div class="details-label">Current Interest Rate</div>
                                <div class="details-value">{{ "{:.2f}".format(current_rate * 100) }}%</div>
                            </div>
                            <div class="details-row">
                                <div class="details-label">Current Market Rate</div>
                                <div class="details-value">{{ "{:.2f}".format(market_rate * 100) }}%</div>
                            </div>
                            <div class="details-row">
                                <div class="details-label">Remaining Term</div>
                                <div class="details-value">{{ remaining_term }} months</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="footer">
                    <p>This recommendation was generated by RefiAlert based on your alert settings and current market conditions.</p>
                    <p>Questions? Log in to your account to adjust your preferences or contact support.</p>
                </div>
            </div>
        </body>
        </html>
        """,
        user_name=user.name,
        mortgage_name=mortgage.name,
        recommendation=rec.recommendation.value,
        headline=rec.headline,
        rec_icon=rec_icon,
        rec_color=rec_color,
        rec_bg=rec_bg,
        savings=rec.savings,
        reasoning_html=reasoning_html,
        action_html=action_html,
        timing_advice=rec.timing_advice,
        remaining_principal=mortgage.remaining_principal,
        current_rate=mortgage.original_interest_rate,
        market_rate=current_market_rate,
        remaining_term=mortgage.remaining_term
        )

        # Plain text version
        text_body = f"""
RefiAlert Personalized Recommendation
=====================================

Hi {user.name},

Based on current market conditions, here's our recommendation for {mortgage.name}:

{'='*50}
RECOMMENDATION: {rec.recommendation.value}
{rec.headline}
{'='*50}

"""
        if rec.savings:
            text_body += f"""
YOUR POTENTIAL SAVINGS
----------------------
Monthly Savings: ${rec.savings.monthly_savings:,.0f}
Annual Savings: ${rec.savings.annual_savings:,.0f}
Break-Even Period: {rec.savings.break_even_months} months
Current Payment: ${rec.savings.current_monthly_payment:,.2f}
New Payment: ${rec.savings.new_monthly_payment:,.2f}
Refinance Cost: ${rec.savings.refinance_cost:,.0f}

"""

        text_body += f"""
WHY THIS RECOMMENDATION?
------------------------
"""
        for reason in rec.reasoning:
            text_body += f"- {reason}\n"

        if rec.timing_advice:
            text_body += f"""
TIMING ADVICE
-------------
{rec.timing_advice}

"""

        text_body += f"""
{"RECOMMENDED NEXT STEPS" if rec.recommendation == Recommendation.YES else "WHAT YOU CAN DO"}
{"="*30}
"""
        for i, step in enumerate(rec.action_steps, 1):
            text_body += f"{i}. {step}\n"

        text_body += f"""

YOUR MORTGAGE DETAILS
---------------------
Remaining Principal: ${mortgage.remaining_principal:,.2f}
Current Interest Rate: {mortgage.original_interest_rate*100:.2f}%
Current Market Rate: {current_market_rate*100:.2f}%
Remaining Term: {mortgage.remaining_term} months

---
This recommendation was generated by RefiAlert based on your settings.
Log in to adjust your preferences or contact support with questions.
"""

        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(
            f"Personalized recommendation ({rec.recommendation.value}) sent to {user.email} for trigger {trigger_id}"
        )
        return True

    except Exception as e:
        current_app.logger.error(
            f"Failed to send personalized recommendation for trigger {trigger_id}: {str(e)}"
        )
        return False
