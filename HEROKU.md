# Heroku Deployment Guide

This guide covers deploying Refi Alert to Heroku.

## Prerequisites

- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
- Heroku account with billing enabled (for add-ons)
- Git repository initialized

## Quick Start

```bash
# Login to Heroku
heroku login

# Create production app
heroku create refi-alert-prod

# Add PostgreSQL database
heroku addons:create heroku-postgresql:essential-0

# Add Heroku Scheduler for background jobs
heroku addons:create scheduler:standard

# Add Papertrail for logging (optional but recommended)
heroku addons:create papertrail:choklad

# Set environment variables (see Environment Variables section)
heroku config:set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
heroku config:set FLASK_APP=wsgi.py
heroku config:set FLASK_ENV=production
# ... see full list below

# Deploy
git push heroku main

# Run migrations (automatic via release phase, but can run manually)
heroku run flask db upgrade

# Open app
heroku open
```

## Environment Variables

Set these environment variables in Heroku:

### Required

```bash
# Flask Configuration
heroku config:set SECRET_KEY="your-secure-secret-key"
heroku config:set FLASK_APP=wsgi.py
heroku config:set FLASK_ENV=production
heroku config:set FLASK_PROD=production

# Database (automatically set by Heroku Postgres add-on)
# DATABASE_URL is set automatically

# Stripe Payment Configuration
heroku config:set STRIPE_API_KEY="sk_live_your_stripe_secret_key"
heroku config:set STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret"

# Application URL (for email links and Stripe redirects)
heroku config:set APP_BASE_URL="https://your-app-name.herokuapp.com"
```

### Email Configuration

Choose one email provider:

**SendGrid (Recommended for Heroku):**
```bash
heroku addons:create sendgrid:starter
heroku config:set MAIL_SERVER=smtp.sendgrid.net
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USE_TLS=True
heroku config:set MAIL_USERNAME=apikey
heroku config:set MAIL_PASSWORD="your-sendgrid-api-key"
heroku config:set MAIL_DEFAULT_SENDER="noreply@yourdomain.com"
```

**Gmail (for testing only):**
```bash
heroku config:set MAIL_SERVER=smtp.gmail.com
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USE_TLS=True
heroku config:set MAIL_USERNAME="your-email@gmail.com"
heroku config:set MAIL_PASSWORD="your-gmail-app-password"
heroku config:set MAIL_DEFAULT_SENDER="your-email@gmail.com"
```

### Optional

```bash
# Scheduler Configuration (disable in-app scheduler, use Heroku Scheduler instead)
heroku config:set ENABLE_SCHEDULER=false

# Rate Update Schedule (if using in-app scheduler)
heroku config:set RATE_UPDATE_HOUR=9
heroku config:set RATE_UPDATE_MINUTE=0
```

## Add-ons

### Heroku Postgres

The database is provisioned automatically with the `essential-0` plan:

```bash
heroku addons:create heroku-postgresql:essential-0
```

To check database status:
```bash
heroku pg:info
```

To create a backup:
```bash
heroku pg:backups:capture
```

To schedule daily backups:
```bash
heroku pg:backups:schedule DATABASE_URL --at '02:00 America/New_York'
```

### Heroku Scheduler

Configure scheduled jobs for rate updates and alert checks:

```bash
heroku addons:create scheduler:standard
heroku addons:open scheduler
```

Add these jobs in the Scheduler dashboard:

| Job Command | Frequency | Description |
|-------------|-----------|-------------|
| `flask update-rates` | Daily at 9:00 AM EST | Update mortgage rates |
| `flask check-alerts` | Every 4 hours | Check and trigger alerts |

### Papertrail (Logging)

```bash
heroku addons:create papertrail:choklad
heroku addons:open papertrail
```

### SendGrid (Email)

```bash
heroku addons:create sendgrid:starter
```

## Deployment Configuration

### Procfile

The `Procfile` defines the web and release processes:

```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 wsgi:app
release: flask db upgrade
```

- **web**: Runs the Flask application with Gunicorn
- **release**: Automatically runs database migrations on each deploy

### runtime.txt

Specifies Python version:
```
python-3.11
```

## Stripe Webhook Configuration

1. Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
2. Add endpoint: `https://your-app-name.herokuapp.com/payment/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy the webhook signing secret
5. Set in Heroku:
   ```bash
   heroku config:set STRIPE_WEBHOOK_SECRET="whsec_..."
   ```

## Staging Environment (Optional)

Create a staging app for testing:

```bash
# Create staging app
heroku create refi-alert-staging --remote staging

# Add database
heroku addons:create heroku-postgresql:essential-0 --remote staging

# Copy config from production (modify as needed)
heroku config --remote production -s | heroku config:set --remote staging

# Set staging-specific config
heroku config:set FLASK_ENV=staging --remote staging
heroku config:set STRIPE_API_KEY="sk_test_..." --remote staging

# Deploy to staging
git push staging main
```

## Common Commands

```bash
# View logs
heroku logs --tail

# Run one-off command
heroku run flask update-rates

# Open Heroku bash
heroku run bash

# Check app status
heroku ps

# Scale dynos
heroku ps:scale web=1

# View config
heroku config

# Database console
heroku pg:psql

# Restart app
heroku restart
```

## Troubleshooting

### Database Connection Issues

If you see database connection errors:
```bash
# Check database status
heroku pg:info

# Verify DATABASE_URL is set
heroku config:get DATABASE_URL

# Reset database (WARNING: destroys all data)
heroku pg:reset DATABASE_URL --confirm your-app-name
heroku run flask db upgrade
```

### Memory Issues

If the app is running out of memory:
```bash
# Check memory usage
heroku logs --tail | grep Memory

# Reduce workers in Procfile:
# web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 wsgi:app
```

### Scheduler Not Running

1. Verify scheduler add-on is installed:
   ```bash
   heroku addons | grep scheduler
   ```
2. Check scheduler dashboard for job configuration
3. Check logs for job execution:
   ```bash
   heroku logs --tail --ps scheduler
   ```

### Email Not Sending

1. Verify email configuration:
   ```bash
   heroku config | grep MAIL
   ```
2. Check logs for email errors
3. Test email manually:
   ```bash
   heroku run flask shell
   >>> from refi_monitor import mail
   >>> from flask_mail import Message
   >>> msg = Message('Test', recipients=['your@email.com'], body='Test')
   >>> mail.send(msg)
   ```

## Security Checklist

- [ ] Set strong SECRET_KEY (use `secrets.token_hex(32)`)
- [ ] Use production Stripe keys (not test keys)
- [ ] Enable SSL (automatic on Heroku)
- [ ] Configure Stripe webhook secret
- [ ] Set up database backups
- [ ] Review Heroku access controls
