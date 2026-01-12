# Deployment Guide

This guide covers deploying refi_alert to production environments.

## Prerequisites

- Python 3.9+
- Node.js 18+ (for React frontend build)
- PostgreSQL database
- Git

## Environment Variables

### Required Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key for session security |
| `DATABASE_URL` | PostgreSQL connection URL |
| `MAIL_USERNAME` | Email sender username (for alerts) |
| `MAIL_PASSWORD` | Email sender password |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Set to `production` for prod |
| `SENTRY_DSN` | - | Sentry DSN for error tracking |
| `SENTRY_ENVIRONMENT` | `development` | Environment name for Sentry |
| `ENABLE_SCHEDULER` | `true` | Enable/disable rate update scheduler |
| `RATE_UPDATE_HOUR` | `9` | Hour (EST) to run rate updates |
| `RATE_UPDATE_MINUTE` | `0` | Minute to run rate updates |
| `STRIPE_API_KEY` | - | Stripe API key for payments |

## Deployment Platforms

### Railway (Recommended)

1. **Create Railway Project**
   ```bash
   railway login
   railway init
   ```

2. **Add PostgreSQL**
   - In Railway dashboard, click "New" → "Database" → "PostgreSQL"
   - Railway automatically sets `DATABASE_URL`

3. **Set Environment Variables**
   ```bash
   railway variables set SECRET_KEY="your-secure-secret-key"
   railway variables set FLASK_ENV="production"
   railway variables set SENTRY_DSN="your-sentry-dsn"
   railway variables set SENTRY_ENVIRONMENT="production"
   ```

4. **Deploy**
   ```bash
   railway up
   ```

5. **Configure Custom Domain**
   - In Railway dashboard → Settings → Domains
   - Add your custom domain
   - Configure DNS: CNAME record pointing to `*.up.railway.app`

### Heroku

1. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

2. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY="your-secure-secret-key"
   heroku config:set FLASK_ENV="production"
   heroku config:set SENTRY_DSN="your-sentry-dsn"
   heroku config:set SENTRY_ENVIRONMENT="production"
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Run Migrations**
   ```bash
   heroku run flask db upgrade
   ```

6. **Configure Custom Domain**
   ```bash
   heroku domains:add www.yourdomain.com
   ```
   Then configure DNS with the provided target.

## SSL/TLS Configuration

### Railway
- SSL is automatically enabled for all domains
- HTTPS is enforced by default

### Heroku
- Enable ACM (Automated Certificate Management):
  ```bash
  heroku certs:auto:enable
  ```
- Force HTTPS in Flask config (already handled in production)

## Database Migrations

Run migrations after deployment:

```bash
# Railway
railway run flask db upgrade

# Heroku
heroku run flask db upgrade

# Local/Direct
flask db upgrade
```

## Monitoring Setup

### Sentry (Error Tracking)

1. Create a project at [sentry.io](https://sentry.io)
2. Get your DSN from Project Settings → Client Keys
3. Set `SENTRY_DSN` environment variable

### Health Check

The app exposes `/health` endpoint for monitoring:
- Returns `200 OK` with JSON status when healthy
- Returns `503` if database is unreachable

Example response:
```json
{
  "status": "ok",
  "database": "healthy",
  "timestamp": "2025-01-12T00:00:00.000000"
}
```

### Uptime Monitoring

Recommended services:
- [UptimeRobot](https://uptimerobot.com) - Free tier available
- [Pingdom](https://pingdom.com)
- [Better Uptime](https://betteruptime.com)

Configure to check `/health` endpoint every 5 minutes.

## Backup & Recovery

### Railway PostgreSQL
- Automatic daily backups included
- Point-in-time recovery available

### Heroku PostgreSQL
Enable backups:
```bash
heroku pg:backups:schedule --at '02:00 America/New_York'
```

Restore from backup:
```bash
heroku pg:backups:restore 'backup-url' DATABASE_URL
```

## CI/CD Pipeline

The project includes GitLab CI/CD configuration in `.gitlab-ci.yml`:

### Stages
1. **review** - Automated code review on merge requests
2. **deploy** - GitHub mirroring on main branch

### Setup
1. Set `GITHUB_TOKEN` in GitLab CI/CD variables for mirroring
2. Set `RAILWAY_TOKEN` for Railway deployments (if using Railway CI)

## Troubleshooting

### App Won't Start
- Check `flask db upgrade` ran successfully
- Verify `DATABASE_URL` is set correctly
- Check logs: `railway logs` or `heroku logs --tail`

### Database Connection Issues
- Verify PostgreSQL addon is provisioned
- Check connection URL format: `postgresql://user:pass@host:5432/db`
- For Railway: ensure using internal URL for speed

### Static Assets Not Loading
- Ensure `npm run build:css` ran during deploy
- Check build command in `railway.json` or `Procfile`

## Security Checklist

- [ ] `SECRET_KEY` is unique and secure (min 32 chars)
- [ ] `FLASK_ENV=production` is set
- [ ] HTTPS is enforced
- [ ] Database backups are configured
- [ ] Sentry error tracking is enabled
- [ ] Sensitive env vars are not in git
