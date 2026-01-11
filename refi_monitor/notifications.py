"""Notification service for sending alerts to users."""
from flask import current_app, render_template_string
from flask_mail import Message
from . import mail, db
from .models import User, Alert, Mortgage, Trigger, MortgageRate
from .calc import calc_loan_monthly_payment, total_payment, time_to_even, ipmt_total
from datetime import datetime
from decimal import Decimal


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


def calculate_opportunity_score(monthly_savings, break_even_months, total_savings, rate_reduction):
    """
    Calculate an opportunity score from 0-100 based on refinancing metrics.

    Args:
        monthly_savings: Monthly payment reduction in dollars
        break_even_months: Months until refinance costs are recouped
        total_savings: Total lifetime savings in dollars
        rate_reduction: Reduction in interest rate (as percentage points)

    Returns:
        Tuple of (score, rating_label, rating_description)
    """
    score = 0

    # Monthly savings component (0-30 points)
    if monthly_savings >= 500:
        score += 30
    elif monthly_savings >= 300:
        score += 25
    elif monthly_savings >= 200:
        score += 20
    elif monthly_savings >= 100:
        score += 15
    elif monthly_savings >= 50:
        score += 10
    elif monthly_savings > 0:
        score += 5

    # Break-even time component (0-30 points) - lower is better
    if break_even_months <= 12:
        score += 30
    elif break_even_months <= 18:
        score += 25
    elif break_even_months <= 24:
        score += 20
    elif break_even_months <= 36:
        score += 15
    elif break_even_months <= 48:
        score += 10
    elif break_even_months <= 60:
        score += 5

    # Total savings component (0-25 points)
    if total_savings >= 50000:
        score += 25
    elif total_savings >= 30000:
        score += 20
    elif total_savings >= 15000:
        score += 15
    elif total_savings >= 5000:
        score += 10
    elif total_savings > 0:
        score += 5

    # Rate reduction component (0-15 points)
    if rate_reduction >= 1.5:
        score += 15
    elif rate_reduction >= 1.0:
        score += 12
    elif rate_reduction >= 0.75:
        score += 9
    elif rate_reduction >= 0.5:
        score += 6
    elif rate_reduction >= 0.25:
        score += 3

    # Determine rating label
    if score >= 85:
        rating_label = "Excellent"
        rating_description = "This is an exceptional refinancing opportunity. Acting now could lead to significant long-term savings."
    elif score >= 70:
        rating_label = "Very Good"
        rating_description = "This is a strong refinancing opportunity with favorable terms and solid savings potential."
    elif score >= 55:
        rating_label = "Good"
        rating_description = "This refinancing opportunity offers meaningful savings and is worth serious consideration."
    elif score >= 40:
        rating_label = "Fair"
        rating_description = "This opportunity offers moderate savings. Consider your plans to stay in the home."
    elif score >= 25:
        rating_label = "Marginal"
        rating_description = "Savings are modest. May be worth pursuing if you plan to stay long-term."
    else:
        rating_label = "Poor"
        rating_description = "Current conditions don't favor refinancing. Consider waiting for better rates."

    return score, rating_label, rating_description


def send_refinance_opportunity_report(trigger_id):
    """
    Send comprehensive refinance opportunity analysis email.

    Includes:
    - Potential new rate
    - Monthly savings calculation
    - Break-even analysis
    - Total savings over loan term
    - Opportunity score/rating

    Args:
        trigger_id: ID of the Trigger record

    Returns:
        True if email sent successfully, False otherwise
    """
    trigger = Trigger.query.get(trigger_id)
    if not trigger:
        current_app.logger.error(f"Trigger {trigger_id} not found")
        return False

    alert = Alert.query.get(trigger.alert_id)
    if not alert:
        current_app.logger.error(f"Alert {trigger.alert_id} not found")
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
        # Get current market rate
        latest_rate = MortgageRate.query.filter_by(
            rate_type='30_year_fixed'
        ).order_by(MortgageRate.date.desc()).first()

        if latest_rate:
            new_rate = float(latest_rate.rate) / 100  # Convert from percentage to decimal
        else:
            # Fallback: use target rate from alert
            new_rate = alert.target_interest_rate if alert.target_interest_rate else mortgage.original_interest_rate * 0.9

        current_rate = mortgage.original_interest_rate
        remaining_principal = mortgage.remaining_principal
        remaining_term = mortgage.remaining_term
        target_term = alert.target_term or remaining_term
        refi_cost = alert.estimate_refinance_cost or 5000

        # Calculate current monthly payment
        current_monthly = calc_loan_monthly_payment(
            remaining_principal,
            current_rate,
            remaining_term
        )

        # Calculate new monthly payment with new rate
        new_monthly = calc_loan_monthly_payment(
            remaining_principal,
            new_rate,
            target_term
        )

        # Monthly savings
        monthly_savings = current_monthly - new_monthly

        # Break-even analysis
        if monthly_savings > 0:
            break_even_months = int(time_to_even(refi_cost, monthly_savings))
        else:
            break_even_months = 0

        # Total payments over loan term
        current_total = total_payment(current_monthly, remaining_term)
        new_total = total_payment(new_monthly, target_term) + refi_cost
        total_savings = current_total - new_total

        # Interest savings
        current_interest = ipmt_total(current_rate, remaining_term, remaining_principal)
        new_interest = ipmt_total(new_rate, target_term, remaining_principal)
        interest_savings = current_interest - new_interest

        # Rate reduction
        rate_reduction = (current_rate - new_rate) * 100  # Convert to percentage points

        # Calculate opportunity score
        score, rating_label, rating_description = calculate_opportunity_score(
            monthly_savings,
            break_even_months,
            total_savings,
            rate_reduction
        )

        # Determine score color based on rating
        if score >= 70:
            score_color = "#28a745"  # Green
        elif score >= 40:
            score_color = "#ffc107"  # Yellow/amber
        else:
            score_color = "#dc3545"  # Red

        # Build email content
        subject = f"RefiAlert: Refinance Opportunity Analysis for {mortgage.name}"

        html_body = render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 650px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; padding: 25px; text-align: center; border-radius: 8px 8px 0 0; }
                .content { background-color: #f9f9f9; padding: 25px; }
                .score-section { text-align: center; padding: 25px; background: white; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .score-circle { width: 120px; height: 120px; border-radius: 50%; background: {{ score_color }}; color: white; display: inline-flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; margin: 10px 0; }
                .score-label { font-size: 24px; font-weight: bold; color: {{ score_color }}; margin: 10px 0; }
                .score-description { color: #666; font-style: italic; }
                .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
                .metric-box { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric-value { font-size: 28px; font-weight: bold; color: #2c3e50; }
                .metric-label { font-size: 12px; text-transform: uppercase; color: #666; margin-top: 5px; }
                .savings-highlight { color: #28a745; }
                .comparison-table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .comparison-table th { background: #34495e; color: white; padding: 12px; text-align: left; }
                .comparison-table td { padding: 12px; border-bottom: 1px solid #eee; }
                .comparison-table tr:last-child td { border-bottom: none; }
                .current-col { background: #f8f9fa; }
                .new-col { background: #e8f5e9; }
                .break-even-section { background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }
                .cta-button { display: inline-block; padding: 12px 30px; background-color: #3498db; color: white; text-decoration: none; border-radius: 25px; margin-top: 20px; font-weight: bold; }
                .next-steps { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .next-steps ol { margin: 0; padding-left: 20px; }
                .next-steps li { margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Refinance Opportunity Analysis</h1>
                    <p>{{ mortgage_name }} | Generated {{ report_date }}</p>
                </div>
                <div class="content">
                    <div class="score-section">
                        <p style="margin: 0; color: #666; text-transform: uppercase; font-size: 12px;">Opportunity Score</p>
                        <div class="score-circle">{{ score }}</div>
                        <div class="score-label">{{ rating_label }}</div>
                        <p class="score-description">{{ rating_description }}</p>
                    </div>

                    <div class="metrics-grid">
                        <div class="metric-box">
                            <div class="metric-value savings-highlight">${{ "{:,.0f}".format(monthly_savings) }}</div>
                            <div class="metric-label">Monthly Savings</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value">{{ break_even_months }} mo</div>
                            <div class="metric-label">Break-Even Time</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value savings-highlight">${{ "{:,.0f}".format(total_savings) }}</div>
                            <div class="metric-label">Total Savings</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value savings-highlight">${{ "{:,.0f}".format(interest_savings) }}</div>
                            <div class="metric-label">Interest Savings</div>
                        </div>
                    </div>

                    <h3>Rate Comparison</h3>
                    <table class="comparison-table">
                        <tr>
                            <th>Metric</th>
                            <th class="current-col">Current Loan</th>
                            <th class="new-col">New Loan</th>
                        </tr>
                        <tr>
                            <td><strong>Interest Rate</strong></td>
                            <td class="current-col">{{ "{:.3f}".format(current_rate * 100) }}%</td>
                            <td class="new-col">{{ "{:.3f}".format(new_rate * 100) }}%</td>
                        </tr>
                        <tr>
                            <td><strong>Monthly Payment</strong></td>
                            <td class="current-col">${{ "{:,.2f}".format(current_monthly) }}</td>
                            <td class="new-col">${{ "{:,.2f}".format(new_monthly) }}</td>
                        </tr>
                        <tr>
                            <td><strong>Remaining Term</strong></td>
                            <td class="current-col">{{ remaining_term }} months</td>
                            <td class="new-col">{{ target_term }} months</td>
                        </tr>
                        <tr>
                            <td><strong>Total Cost</strong></td>
                            <td class="current-col">${{ "{:,.0f}".format(current_total) }}</td>
                            <td class="new-col">${{ "{:,.0f}".format(new_total) }}</td>
                        </tr>
                    </table>

                    <div class="break-even-section">
                        <h3 style="margin-top: 0;">Break-Even Analysis</h3>
                        <p><strong>Estimated Refinance Cost:</strong> ${{ "{:,.0f}".format(refi_cost) }}</p>
                        <p><strong>Monthly Savings:</strong> ${{ "{:,.2f}".format(monthly_savings) }}</p>
                        <p><strong>Break-Even Point:</strong> {{ break_even_months }} months ({{ "{:.1f}".format(break_even_months / 12) }} years)</p>
                        <p style="margin-bottom: 0;">{% if break_even_months <= 24 %}
                        With a break-even under 2 years, this refinance offers quick return on investment.
                        {% elif break_even_months <= 48 %}
                        You'll recoup costs within 4 years. Consider your plans to stay in the home.
                        {% else %}
                        The break-even period is extended. Best suited if you plan to stay 5+ years.
                        {% endif %}</p>
                    </div>

                    <div class="next-steps">
                        <h3 style="margin-top: 0;">Recommended Next Steps</h3>
                        <ol>
                            <li><strong>Get rate quotes</strong> from 3-5 lenders to ensure competitive terms</li>
                            <li><strong>Request Loan Estimates</strong> to compare actual closing costs</li>
                            <li><strong>Review your credit report</strong> to ensure accuracy before applying</li>
                            <li><strong>Calculate your debt-to-income ratio</strong> to understand qualification</li>
                            <li><strong>Gather documentation</strong> (pay stubs, tax returns, bank statements)</li>
                        </ol>
                    </div>

                    <p style="text-align: center; color: #666; font-size: 14px; margin-top: 25px;">
                        Questions about this analysis? Log in to your dashboard for more details.
                    </p>
                </div>
                <div class="footer">
                    <p>This analysis is for informational purposes only and does not constitute financial advice.</p>
                    <p>Actual rates and terms may vary based on credit score, lender, and market conditions.</p>
                    <p>Alert ID: #{{ alert_id }} | Trigger ID: #{{ trigger_id }}</p>
                </div>
            </div>
        </body>
        </html>
        """,
        mortgage_name=mortgage.name,
        report_date=datetime.now().strftime("%B %d, %Y"),
        score=score,
        score_color=score_color,
        rating_label=rating_label,
        rating_description=rating_description,
        monthly_savings=monthly_savings,
        break_even_months=break_even_months,
        total_savings=total_savings,
        interest_savings=interest_savings,
        current_rate=current_rate,
        new_rate=new_rate,
        current_monthly=current_monthly,
        new_monthly=new_monthly,
        remaining_term=remaining_term,
        target_term=target_term,
        current_total=current_total,
        new_total=new_total,
        refi_cost=refi_cost,
        alert_id=alert.id,
        trigger_id=trigger_id
        )

        # Create plain text version
        text_body = f"""
REFINANCE OPPORTUNITY ANALYSIS
==============================
{mortgage.name} | Generated {datetime.now().strftime("%B %d, %Y")}

OPPORTUNITY SCORE: {score}/100 - {rating_label}
{rating_description}

KEY METRICS
-----------
Monthly Savings:    ${monthly_savings:,.0f}
Break-Even Time:    {break_even_months} months ({break_even_months / 12:.1f} years)
Total Savings:      ${total_savings:,.0f}
Interest Savings:   ${interest_savings:,.0f}

RATE COMPARISON
---------------
                    Current Loan    New Loan
Interest Rate:      {current_rate * 100:.3f}%         {new_rate * 100:.3f}%
Monthly Payment:    ${current_monthly:,.2f}      ${new_monthly:,.2f}
Remaining Term:     {remaining_term} months      {target_term} months
Total Cost:         ${current_total:,.0f}       ${new_total:,.0f}

BREAK-EVEN ANALYSIS
-------------------
Estimated Refinance Cost: ${refi_cost:,.0f}
Monthly Savings: ${monthly_savings:,.2f}
Break-Even Point: {break_even_months} months

RECOMMENDED NEXT STEPS
----------------------
1. Get rate quotes from 3-5 lenders to ensure competitive terms
2. Request Loan Estimates to compare actual closing costs
3. Review your credit report to ensure accuracy before applying
4. Calculate your debt-to-income ratio to understand qualification
5. Gather documentation (pay stubs, tax returns, bank statements)

---
This analysis is for informational purposes only and does not constitute financial advice.
Actual rates and terms may vary based on credit score, lender, and market conditions.

Alert ID: #{alert.id} | Trigger ID: #{trigger_id}
"""

        # Send email
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)
        current_app.logger.info(f"Refinance opportunity report sent to {user.email} for trigger {trigger_id}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send refinance opportunity report for trigger {trigger_id}: {str(e)}")
        return False
