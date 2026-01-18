# Automated Publishing and Distribution System

## Overview

The RefiAlert application now includes a comprehensive automated publishing and distribution system that monitors mortgage rates and sends notifications to users when their refinancing conditions are met.

## Architecture

### Components

1. **Email Notification Service** (`refi_monitor/notifications.py`)
   - Flask-Mail integration for sending HTML and plain text emails
   - Alert trigger notifications with detailed refinancing information
   - Payment confirmation emails for successful subscriptions

2. **Background Scheduler** (`refi_monitor/scheduler.py`)
   - APScheduler-based background job system
   - Automatic alert evaluation on a recurring schedule
   - Manual trigger endpoint for testing and admin operations

3. **Alert Evaluation Engine** (`refi_monitor/scheduler.py`)
   - Evaluates alerts against current market rates
   - Supports two alert types:
     - **Monthly Payment Alerts**: Triggers when current rates allow target monthly payment
     - **Interest Rate Alerts**: Triggers when market rates reach target interest rate
   - Prevents duplicate notifications within 24-hour windows

4. **Payment Webhook Integration** (`refi_monitor/mortgage.py`)
   - Enhanced Stripe webhook handler
   - Automatic payment confirmation emails
   - Payment status tracking (active, payment_failed)

## How It Works

### Alert Lifecycle

1. **User Creates Alert**
   - User adds a mortgage to their account
   - User sets up an alert with target conditions (monthly payment or interest rate)
   - User completes payment via Stripe

2. **Payment Processing**
   - Stripe webhook receives `invoice.paid` event
   - Alert status updated to `active`
   - Payment confirmation email sent to user

3. **Scheduled Monitoring**
   - Background scheduler runs:
     - Daily at 9:00 AM
     - Every 4 hours throughout the day
   - All active (paid) alerts are evaluated

4. **Alert Evaluation**
   - Current market rates fetched (currently mock data, ready for API integration)
   - For each alert:
     - Calculate what monthly payment would be at current rates
     - Compare against user's target conditions
     - Account for estimated refinance costs

5. **Notification Delivery**
   - If conditions met and no recent notification:
     - Create Trigger record in database
     - Send detailed email notification to user
     - Include next steps and refinancing guidance

### Email Templates

#### Alert Notification Email
- Personalized greeting with user name
- Alert type and trigger reason
- Current mortgage details (principal, rate, term)
- Target refinancing goals
- Next steps checklist for user action

#### Payment Confirmation Email
- Payment success confirmation
- Alert activation notice
- What to expect next

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@refialert.com
```

### Gmail Setup (Example)

If using Gmail:
1. Enable 2-factor authentication on your Google account
2. Generate an "App Password" at https://myaccount.google.com/apppasswords
3. Use the app password as `MAIL_PASSWORD`

### Other Email Providers

The system supports any SMTP server:
- **SendGrid**: Set `MAIL_SERVER=smtp.sendgrid.net`, `MAIL_PORT=587`
- **Mailgun**: Set `MAIL_SERVER=smtp.mailgun.org`, `MAIL_PORT=587`
- **AWS SES**: Set `MAIL_SERVER=email-smtp.us-east-1.amazonaws.com`, `MAIL_PORT=587`

## Schedule Configuration

Current schedule (in `scheduler.py`):

```python
# Daily check at 9 AM
scheduler.add_job(
    func=check_and_trigger_alerts,
    trigger=CronTrigger(hour=9, minute=0),
    id='daily_alert_check'
)

# Every 4 hours
scheduler.add_job(
    func=check_and_trigger_alerts,
    trigger=CronTrigger(hour='*/4'),
    id='frequent_alert_check'
)

# Monthly reports on 1st of each month at 8 AM
scheduler.add_job(
    func=scheduled_monthly_report,
    trigger=CronTrigger(day=1, hour=8, minute=0),
    id='monthly_report'
)
```

To customize the schedule, modify the `CronTrigger` parameters:
- `hour='*/4'` - every 4 hours
- `hour=9, minute=0` - daily at 9:00 AM
- `day_of_week='mon-fri'` - weekdays only
- See [APScheduler CronTrigger docs](https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html)

## Manual Testing

### Trigger Alert Check Manually

Send POST request to admin endpoint:

```bash
curl -X POST http://localhost:5000/admin/trigger-alerts \
  -H "Content-Type: application/json" \
  --cookie "session=<your-session-cookie>"
```

Or add a button to the dashboard UI that calls this endpoint.

### Testing Email Delivery

1. Set up email credentials in `.env`
2. Create a test alert with your email
3. Mark alert as `payment_status='active'` in database
4. Trigger manual check via admin endpoint
5. Check your inbox for notification

## Rate Data Integration

### Current Implementation

The system currently uses mock rate data in `get_current_mortgage_rates()`:

```python
mock_rates = {
    15: 0.0575,  # 15-year fixed: 5.75%
    20: 0.0625,  # 20-year fixed: 6.25%
    30: 0.0675,  # 30-year fixed: 6.75%
}
```

### Production Integration

To integrate real mortgage rate data, replace `get_current_mortgage_rates()` with API calls to:

**Recommended APIs:**
1. **Freddie Mac Primary Mortgage Market Survey**
   - Free, official data
   - Weekly updates
   - URL: http://www.freddiemac.com/pmms/

2. **Mortgage News Daily API** (Paid)
   - Real-time rates
   - Location-specific data

3. **Zillow Mortgage API** (Paid)
   - Zip code-specific rates
   - Multiple lender data

**Example Integration:**

```python
def get_current_mortgage_rates(zip_code=None):
    """Fetch rates from external API."""
    try:
        response = requests.get(
            f"https://api.mortgagedata.com/rates",
            params={'zip_code': zip_code},
            headers={'Authorization': f'Bearer {API_KEY}'}
        )
        data = response.json()
        return {
            15: data['rate_15_year'],
            20: data['rate_20_year'],
            30: data['rate_30_year']
        }
    except Exception as e:
        current_app.logger.error(f"Failed to fetch rates: {e}")
        return mock_rates  # Fallback to mock data
```

## Database Schema Updates

No schema migrations required - the existing schema supports all features:

- `Alert.payment_status` - tracks subscription status
- `Trigger` table - records all alert activations
- `Trigger.alert_trigger_date` - prevents duplicate notifications

## Monitoring and Logging

### Application Logs

All notification events are logged:

```python
current_app.logger.info(f"Alert {alert.id} triggered: {reason}")
current_app.logger.info(f"Alert notification sent to {user.email}")
current_app.logger.error(f"Failed to send notification: {error}")
```

### Recommended Monitoring

1. **Email Delivery Monitoring**
   - Track bounce rates via email provider dashboard
   - Monitor SMTP errors in application logs

2. **Alert Evaluation Metrics**
   - Count of alerts evaluated per run
   - Count of alerts triggered
   - Evaluation duration

3. **Background Job Health**
   - Verify scheduler is running: check logs for "Background scheduler started"
   - Monitor job execution: check logs for "Alert check complete"

## Production Deployment Checklist

- [ ] Set up production email service (SendGrid, SES, etc.)
- [ ] Configure email credentials in production `.env`
- [ ] Integrate real mortgage rate API (replace mock data)
- [ ] Set up proper admin role checking for manual trigger endpoint
- [ ] Configure monitoring and alerting for failed email sends
- [ ] Set up log aggregation (Datadog, CloudWatch, etc.)
- [ ] Test email delivery in production environment
- [ ] Verify background scheduler starts with application
- [ ] Set appropriate notification frequency (consider rate limits)
- [ ] Add unsubscribe functionality to email templates (required by law)

## API Rate Limiting Considerations

When integrating external rate APIs:

- **Freddie Mac**: Weekly data, no rate limits
- **Paid APIs**: Check rate limits, implement caching
- **Recommendation**: Cache rate data for 1-4 hours to reduce API calls

Example caching:

```python
from functools import lru_cache
from datetime import datetime, timedelta

rate_cache = {}
CACHE_TTL = timedelta(hours=4)

def get_current_mortgage_rates(zip_code=None):
    cache_key = f"rates_{zip_code}"
    if cache_key in rate_cache:
        cached_time, cached_data = rate_cache[cache_key]
        if datetime.utcnow() - cached_time < CACHE_TTL:
            return cached_data

    # Fetch from API
    rates = fetch_from_api(zip_code)
    rate_cache[cache_key] = (datetime.utcnow(), rates)
    return rates
```

## Future Enhancements

1. **SMS Notifications**
   - Integrate Twilio for SMS alerts
   - Add phone number to User model
   - Add SMS preference to alert settings

2. **Webhook Publishing**
   - Allow users to configure webhook URLs
   - POST alert data to external systems (Zapier, IFTTT, etc.)

3. **Advanced Alert Conditions**
   - Combine multiple conditions (rate AND payment)
   - Alert on rate drops by percentage
   - Alert on savings threshold

4. **Rate Prediction**
   - Machine learning model to predict rate trends
   - "Likely to improve" notifications

5. **Multi-Channel Distribution**
   - Push notifications (web push, mobile)
   - Slack/Discord integrations
   - RSS/Atom feeds

## Troubleshooting

### Emails Not Sending

1. Check email credentials in `.env`
2. Verify SMTP server and port
3. Check application logs for errors
4. Test SMTP connection manually
5. Verify firewall allows outbound SMTP traffic

### Scheduler Not Running

1. Check logs for "Background scheduler started"
2. Verify `init_scheduler(app)` is called in `__init__.py`
3. Check for exceptions during app initialization
4. Verify APScheduler is installed: `pip list | grep APScheduler`

### Alerts Not Triggering

1. Verify alert has `payment_status='active'`
2. Check current market rates in mock data
3. Verify alert conditions are achievable with current rates
4. Check logs for evaluation errors
5. Manually trigger alert check via admin endpoint

### Duplicate Notifications

The system prevents duplicates within 24 hours. If receiving duplicates:
1. Check Trigger table for existing records
2. Verify 24-hour window logic
3. Check if multiple schedulers are running (restart app)

## Support

For issues or questions:
1. Check application logs first
2. Review this documentation
3. Test with manual trigger endpoint
4. Check email provider dashboard for delivery issues
