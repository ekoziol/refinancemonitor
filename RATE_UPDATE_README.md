# Daily Rate Update System

This document describes the automated daily mortgage rate update system implemented for the Refi Alert application.

## Overview

The rate update system consists of three main components:

1. **Rate Fetcher**: Fetches current mortgage rates from external sources
2. **Rate Updater**: Updates database records and checks alert conditions
3. **Scheduler**: Automatically runs updates on a daily schedule

## Features

- ✅ Automated daily rate updates via APScheduler
- ✅ Manual rate updates via Flask CLI command
- ✅ Automatic alert checking and trigger creation
- ✅ Configurable schedule via environment variables
- ✅ Mock rate data for testing (easily replaceable with real API)

## Flask CLI Commands

### 1. Update Rates

Manually trigger a rate update:

```bash
flask update-rates
```

Options:
- `--verbose` or `-v`: Enable verbose logging

Example output:
```
🏠 Starting mortgage rate update...
✅ Successfully updated 15 mortgage records
📊 Current 30-year rate: 0.0298 (2.98%)
🔔 Triggered 3 alerts
```

### 2. Test Rate Fetcher

Test rate fetching without updating the database:

```bash
flask test-rate-fetch
```

Example output:
```
🧪 Testing rate fetcher...

📈 Fetched rates:
  30 YR FRM      : 0.0293 (2.93%)
  15 YR FRM      : 0.0247 (2.47%)
  5/1 YR ARM     : 0.0265 (2.65%)
  FHA 30 YR      : 0.0287 (2.87%)
  JUMBO 30 YR    : 0.0303 (3.03%)
```

### 3. Scheduler Status

Check the status of scheduled jobs:

```bash
flask scheduler-status
```

Example output:
```
📅 Scheduler Status

Job: Daily Mortgage Rate Update (ID: daily_rate_update)
  Next run: 2026-01-11T09:00:00-05:00
  Trigger: cron[hour='9', minute='0']
```

## Configuration

Add these environment variables to your `.env` file:

```bash
# Enable/disable the scheduler (default: true)
ENABLE_SCHEDULER=true

# Schedule time (default: 9:00 AM EST)
RATE_UPDATE_HOUR=9
RATE_UPDATE_MINUTE=0
```

## Automated Scheduling

The scheduler is configured to run automatically when the Flask application starts. By default, it runs daily at **9:00 AM EST**.

### How It Works

1. When the app initializes, it starts a background APScheduler instance
2. The scheduler runs the rate update task according to the cron schedule
3. Each run:
   - Fetches current mortgage rates
   - Updates all `Mortgage_Tracking` records
   - Checks all active alerts (those with `payment_status='paid'`)
   - Creates `Trigger` records when alert conditions are met
   - Logs all activity

### Disabling the Scheduler

To run the app without the scheduler (e.g., for development):

```bash
export ENABLE_SCHEDULER=false
flask run
```

## Integrating Real Rate Data

Currently, the system uses mock data for testing. To integrate a real mortgage rate API:

### Option 1: Freddie Mac PMMS API

1. Sign up for API access at [Freddie Mac](http://www.freddiemac.com/pmms/)
2. Update `refi_monitor/rate_updater.py`:

```python
class RateFetcher:
    def __init__(self):
        self.api_url = "https://api.freddiemac.com/pmms"
        self.api_key = os.environ.get('FREDDIE_MAC_API_KEY')

    def fetch_current_rates(self) -> Dict[str, float]:
        response = requests.get(
            f"{self.api_url}/pmms30.json",
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        return self._parse_freddie_mac_response(response.json())
```

### Option 2: Other Sources

- **Mortgage News Daily**: https://www.mortgagenewsdaily.com/
- **Bankrate API**: https://www.bankrate.com/
- **Custom scraper**: Use BeautifulSoup/Scrapy to scrape rate data

## Alert Triggering Logic

Alerts are triggered when:

1. The alert has `payment_status='paid'` (active subscription)
2. The alert has a non-null `target_interest_rate`
3. The current rate is **≤** the target rate
4. No trigger has been created in the last 24 hours (prevents spam)

When triggered, a `Trigger` record is created with:
- `alert_trigger_status=1` (success)
- `alert_trigger_reason`: Description of why it was triggered
- `alert_trigger_date`: Current timestamp

## Future Enhancements

### TODO: Notification System

Currently, triggers are created but notifications are not sent. To implement:

1. **Email Notifications**: Use Flask-Mail
   ```python
   def _send_notification(self, alert: Alert, current_rate: float):
       from flask_mail import Message
       msg = Message(
           subject=f"Rate Alert: {current_rate:.2%} meets your target!",
           recipients=[alert.user.email],
           body=f"Good news! Rates have dropped to {current_rate:.2%}..."
       )
       mail.send(msg)
   ```

2. **SMS Notifications**: Use Twilio
   ```python
   from twilio.rest import Client
   client = Client(account_sid, auth_token)
   client.messages.create(
       to=alert.user.phone,
       from_=twilio_number,
       body=f"Rate alert: {current_rate:.2%}"
   )
   ```

3. **Webhook Notifications**: POST to user-configured URLs
   ```python
   requests.post(
       alert.webhook_url,
       json={'rate': current_rate, 'target': alert.target_interest_rate}
   )
   ```

### TODO: Rate History Tracking

Consider creating a separate `RateHistory` table to track historical rates:

```python
class RateHistory(db.Model):
    __tablename__ = 'rate_history'
    id = db.Column(db.Integer, primary_key=True)
    rate_type = db.Column(db.String, nullable=False)  # '30 YR FRM', etc.
    rate = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
```

This would enable:
- Historical rate charts
- Trend analysis
- Better alert logic (e.g., "notify when rate drops by 0.25%")

## Architecture

```
┌─────────────────┐
│   APScheduler   │
│  (Background)   │
└────────┬────────┘
         │ Daily at 9 AM EST
         ▼
┌─────────────────┐
│  RateUpdater    │
│  .update_all()  │
└────────┬────────┘
         │
         ├─────────────────────┐
         ▼                     ▼
┌─────────────────┐   ┌────────────────────┐
│  RateFetcher    │   │  Database Update   │
│  .fetch_rates() │   │  - Mortgage_       │
└─────────────────┘   │    Tracking        │
         │            │  - Check Alerts    │
         │            │  - Create Triggers │
         └────────────┴────────────────────┘
```

## File Structure

```
refi_monitor/
├── rate_updater.py    # Core rate update logic
├── cli.py             # Flask CLI commands
├── scheduler.py       # APScheduler configuration
└── models.py          # Database models

config.py              # Scheduler configuration
requirements.txt       # Added APScheduler and requests
.env                   # Environment variables (not in git)
```

## Dependencies

The following packages were added to `requirements.txt`:

```
APScheduler==3.8.1
requests==2.26.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Testing

To test the system:

1. **Test rate fetching**:
   ```bash
   flask test-rate-fetch
   ```

2. **Test database update** (requires database with test data):
   ```bash
   flask update-rates --verbose
   ```

3. **Check scheduler**:
   ```bash
   flask scheduler-status
   ```

4. **Watch logs** when scheduler runs:
   ```bash
   tail -f logs/app.log  # Configure logging as needed
   ```

## Troubleshooting

### Scheduler not running

- Check `ENABLE_SCHEDULER` is set to `true` in `.env`
- Verify scheduler is initialized: `flask scheduler-status`
- Check logs for errors during app initialization

### No records updated

- Verify `Mortgage_Tracking` records exist in database
- Check database connection is working
- Run with `--verbose` flag for detailed logs

### Alerts not triggering

- Verify alerts have `payment_status='paid'`
- Check `target_interest_rate` is set
- Ensure rate is actually below target
- Check if trigger already exists within 24 hours

## Production Deployment

For production deployment:

1. Use a real mortgage rate API (not mock data)
2. Set up proper logging (e.g., to file or log aggregation service)
3. Configure email/SMS notifications
4. Set up monitoring for failed updates
5. Consider using Celery instead of APScheduler for better reliability
6. Use a process manager like systemd or supervisord to keep the app running

### Using System Cron (Alternative)

Instead of APScheduler, you can use system cron:

```bash
# Add to crontab
0 9 * * * cd /path/to/refi_alert && /path/to/venv/bin/flask update-rates >> /var/log/rate-update.log 2>&1
```

Set `ENABLE_SCHEDULER=false` if using system cron.

## Support

For questions or issues, please contact the development team or check the main project README.
