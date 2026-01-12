# Production Deployment Guide

This guide covers deploying RefiAlert to production using Railway, with DNS configuration, SSL, monitoring, and backup procedures.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Railway Setup](#railway-setup)
3. [Environment Variables](#environment-variables)
4. [Domain & DNS Configuration](#domain--dns-configuration)
5. [SSL Certificate](#ssl-certificate)
6. [Database Setup](#database-setup)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Monitoring](#monitoring)
9. [Backups & Recovery](#backups--recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

- Railway account (https://railway.app)
- Custom domain (optional)
- GitLab CI/CD variables configured
- Sentry account for error tracking (optional but recommended)

## Railway Setup

### Initial Setup

1. **Create Railway Project**
   ```bash
   # Login to Railway
   railway login

   # Create new project
   railway init
   ```

2. **Add PostgreSQL Database**
   - In Railway dashboard, click "New" > "Database" > "PostgreSQL"
   - Railway automatically sets `DATABASE_URL` environment variable

3. **Link Repository**
   - Connect your GitLab repository to Railway
   - Railway will auto-detect `railway.json` configuration

### Environments

Create two environments in Railway:

1. **Staging** (`staging`)
   - Auto-deploys from `main` branch
   - Uses staging database
   - URL: `https://refi-alert-staging.up.railway.app`

2. **Production** (`production`)
   - Manual deployment trigger
   - Uses production database
   - URL: `https://refialert.com` (custom domain)

## Environment Variables

Configure these in Railway dashboard or GitLab CI/CD variables:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_APP` | Application entry point | `wsgi.py` |
| `FLASK_ENV` | Environment mode | `production` |
| `SECRET_KEY` | Flask secret key | (generate random 32+ char string) |
| `SQLALCHEMY_DATABASE_URI` | Database connection | Auto-set by Railway |
| `STRIPE_API_KEY` | Stripe secret key | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | `whsec_...` |

### Email Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `MAIL_SERVER` | SMTP server | `smtp.sendgrid.net` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Enable TLS | `True` |
| `MAIL_USERNAME` | SMTP username | `apikey` |
| `MAIL_PASSWORD` | SMTP password/API key | (your key) |
| `MAIL_DEFAULT_SENDER` | From address | `noreply@refialert.com` |

### Monitoring

| Variable | Description | Example |
|----------|-------------|---------|
| `SENTRY_DSN` | Sentry project DSN | `https://key@sentry.io/123` |

### GitLab CI/CD Variables

Set these in GitLab > Settings > CI/CD > Variables:

| Variable | Description |
|----------|-------------|
| `RAILWAY_TOKEN` | Railway API token (from Railway dashboard) |
| `GITHUB_TOKEN` | GitHub PAT for mirroring (optional) |

## Domain & DNS Configuration

### Option 1: Railway Subdomain

Railway provides a free subdomain automatically:
- Staging: `refi-alert-staging.up.railway.app`
- Production: `refi-alert-production.up.railway.app`

### Option 2: Custom Domain

1. **Add Domain in Railway**
   - Go to your service settings
   - Click "Domains" > "Add Custom Domain"
   - Enter your domain (e.g., `refialert.com`)

2. **Configure DNS Records**

   For apex domain (`refialert.com`):
   ```
   Type: A
   Name: @
   Value: (Railway IP provided)
   TTL: 3600
   ```

   For www subdomain (`www.refialert.com`):
   ```
   Type: CNAME
   Name: www
   Value: your-app.up.railway.app
   TTL: 3600
   ```

3. **WWW Redirect**

   Add a redirect rule in Railway or use a CNAME:
   ```
   Type: CNAME
   Name: www
   Value: refialert.com
   ```

### DNS Verification

After configuring DNS, verify propagation:
```bash
# Check A record
dig refialert.com A

# Check CNAME
dig www.refialert.com CNAME

# Or use online tool
# https://dnschecker.org
```

## SSL Certificate

Railway provides automatic SSL via Let's Encrypt:

1. **Enable Automatic SSL**
   - SSL is enabled by default for Railway domains
   - For custom domains, SSL is provisioned after DNS verification

2. **Force HTTPS**
   - Railway automatically redirects HTTP to HTTPS
   - No additional configuration needed

3. **Verify SSL**
   ```bash
   curl -I https://refialert.com
   # Should show HTTP/2 200
   ```

## Database Setup

### Initial Migration

Migrations run automatically on deploy via the start command:
```bash
flask db upgrade && gunicorn ...
```

### Manual Migration (if needed)

```bash
# Via Railway CLI
railway run flask db upgrade

# Or via Railway shell
railway shell
flask db upgrade
```

### Create Admin User

```bash
railway run flask create-admin --email admin@refialert.com --password <secure-password>
```

### Database Backups

Railway PostgreSQL includes automatic daily backups.

**Manual Backup:**
```bash
# Get database URL from Railway
railway variables

# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Restore from Backup:**
```bash
psql $DATABASE_URL < backup_20260112_120000.sql
```

## CI/CD Pipeline

The GitLab CI/CD pipeline (`.gitlab-ci.yml`) handles:

### Pipeline Stages

1. **Review** - Code review on merge requests
2. **Test** - Backend and frontend tests
3. **Build** - Build CSS and React assets
4. **Deploy Staging** - Auto-deploy to staging on main
5. **Deploy Production** - Manual trigger for production

### Deployment Flow

```
Push to main
    ↓
Run Tests (pytest, vitest)
    ↓
Build Assets (Tailwind, React)
    ↓
Deploy to Staging (automatic)
    ↓
[Manual Approval]
    ↓
Deploy to Production
```

### Manual Deployment

If CI/CD fails, deploy manually:
```bash
railway login
railway link --environment production
railway up
```

## Monitoring

### Sentry (Error Tracking)

1. **Create Sentry Project**
   - Sign up at https://sentry.io
   - Create Flask project
   - Copy DSN

2. **Configure Sentry**
   - Set `SENTRY_DSN` environment variable
   - Errors auto-captured in production

3. **Features**
   - Error tracking with stack traces
   - Performance monitoring
   - Release tracking
   - User feedback collection

### Health Checks

The app exposes a health endpoint:
```bash
curl https://refialert.com/health
# Returns: {"status": "healthy", "database": "connected", ...}
```

Railway uses this for:
- Deployment verification
- Service restart on failure

### Uptime Monitoring

Set up external monitoring (recommended):

1. **UptimeRobot** (free tier)
   - Monitor: `https://refialert.com/health`
   - Check interval: 5 minutes
   - Alert via email/SMS

2. **Pingdom** or **StatusCake** (alternatives)

### Logging

View logs in Railway dashboard or CLI:
```bash
railway logs
railway logs --follow
```

## Backups & Recovery

### Automated Backups

Railway PostgreSQL provides:
- Daily automated backups
- 7-day retention
- Point-in-time recovery

### Manual Backup Procedure

```bash
# 1. Get connection string
railway variables | grep DATABASE_URL

# 2. Create backup
pg_dump "$DATABASE_URL" -F c -b -v -f "backup_$(date +%Y%m%d).dump"

# 3. Store backup securely (S3, etc.)
aws s3 cp backup_*.dump s3://your-bucket/backups/
```

### Recovery Procedure

1. **From Railway Backup**
   - Go to Railway dashboard
   - Select PostgreSQL service
   - Click "Backups"
   - Restore to point in time

2. **From Manual Backup**
   ```bash
   # Create new database if needed
   railway run createdb refi_alert_restore

   # Restore
   pg_restore -d "$DATABASE_URL" backup_20260112.dump

   # Run migrations
   railway run flask db upgrade
   ```

### Disaster Recovery Checklist

- [ ] Verify backup exists and is recent
- [ ] Test restore in staging first
- [ ] Update DNS if switching infrastructure
- [ ] Verify all environment variables set
- [ ] Run database migrations
- [ ] Test critical functionality
- [ ] Monitor error rates post-recovery

## Troubleshooting

### Common Issues

**Build Failures**
```bash
# Check build logs
railway logs --build

# Common fixes:
# - Verify Python version in runtime.txt
# - Check all dependencies in requirements.txt
# - Ensure Node version compatibility
```

**Database Connection Issues**
```bash
# Verify database URL
railway variables | grep DATABASE

# Test connection
railway run python -c "from refi_monitor import db; db.engine.connect(); print('OK')"
```

**Static Files Not Loading**
- Verify `npm run build:css` succeeded
- Check React build in `refi_monitor/static/react/`
- Clear browser cache

**Health Check Failing**
```bash
# Check application logs
railway logs

# Test locally
curl https://refialert.com/health
```

### Getting Help

- Railway docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitLab CI/CD docs: https://docs.gitlab.com/ee/ci/

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database backup taken
- [ ] DNS configured (if custom domain)
- [ ] Stripe webhooks configured
- [ ] Email credentials verified

### Post-Deployment

- [ ] Health check passing
- [ ] Can login/register
- [ ] Payment flow working
- [ ] Email notifications working
- [ ] Sentry receiving events
- [ ] Uptime monitor configured

### Production Launch

- [ ] Final testing in staging
- [ ] Announce maintenance window
- [ ] Deploy to production
- [ ] Verify all functionality
- [ ] Monitor error rates
- [ ] Update status page
