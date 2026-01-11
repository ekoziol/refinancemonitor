# Railway Deployment Guide

## Overview
This guide covers deploying the Refi Alert application to Railway.

## Prerequisites
- Railway account (https://railway.app)
- Railway CLI (optional): `npm install -g @railway/cli`
- PostgreSQL database (can be provisioned through Railway)

## Quick Deploy

### Option 1: Deploy from GitHub/GitLab
1. Connect your repository to Railway
2. Railway will auto-detect the configuration from `railway.json` and `Procfile`
3. Add required environment variables (see below)
4. Deploy!

### Option 2: Deploy with Railway CLI
```bash
# Login to Railway
railway login

# Initialize project
railway init

# Link to existing project (if applicable)
railway link

# Add PostgreSQL database
railway add

# Set environment variables
railway variables set FLASK_APP=wsgi.py
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=<your-secret-key>
railway variables set STRIPE_API_KEY=<your-stripe-key>

# Deploy
railway up
```

## Required Environment Variables

Configure these in your Railway project dashboard or via CLI:

### Essential Variables
- `FLASK_APP` - Application entry point (set to `wsgi.py`)
- `FLASK_ENV` - Environment mode (set to `production`)
- `SECRET_KEY` - Flask secret key for session management (generate a random string)
- `SQLALCHEMY_DATABASE_URI` - PostgreSQL connection string
  - If you add a PostgreSQL database through Railway, it will automatically set `DATABASE_URL`
  - You may need to copy this to `SQLALCHEMY_DATABASE_URI` or update your config
- `STRIPE_API_KEY` - Your Stripe API key for payment processing

### Optional Variables
- `FLASK_PROD` - Set to `production` for CSS optimization
- `ASSETS_DEBUG` - Set to `False` for production
- `LESS_RUN_IN_DEBUG` - Set to `False` for production
- `COMPRESSOR_DEBUG` - Set to `False` for production

## Database Setup

### Adding PostgreSQL
1. In Railway dashboard, click "New" > "Database" > "Add PostgreSQL"
2. Railway will automatically set the `DATABASE_URL` environment variable
3. Either:
   - Update `config.py` to use `DATABASE_URL` instead of `SQLALCHEMY_DATABASE_URI`, or
   - Copy the `DATABASE_URL` value to `SQLALCHEMY_DATABASE_URI` variable

### Running Migrations
After deployment, you'll need to run database migrations:

```bash
# Using Railway CLI
railway run flask db upgrade

# Or via Railway dashboard
# Add a one-time deployment command in the settings
```

## Build Process

The build process is configured in `railway.json`:

1. **Install Python dependencies**: `pip install -r requirements.txt`
2. **Install Node dependencies**: `npm install`
3. **Build CSS assets**: `npm run build:css` (processes Tailwind CSS)

## Application Startup

The application starts using the command defined in `Procfile`:
```
web: gunicorn wsgi:app
```

## Health Checks

Railway will automatically health check your application at the root path (`/`).

## Troubleshooting

### Build Failures
- Check that all dependencies are properly listed in `requirements.txt` and `package.json`
- Verify Python version in `runtime.txt` matches Railway's supported versions
- Check build logs in Railway dashboard

### Runtime Errors
- Verify all environment variables are set correctly
- Check application logs in Railway dashboard
- Ensure database migrations have been run
- Verify database connection string is correct

### CSS Not Loading
- Ensure `npm run build:css` completed successfully during build
- Check that static files are being served correctly
- Verify `FLASK_ENV` is set to `production`

## Monitoring

Railway provides:
- Real-time logs in the dashboard
- Metrics and usage statistics
- Deployment history
- Automatic HTTPS certificates

## Scaling

To scale your application:
1. Go to your service settings in Railway dashboard
2. Adjust the number of replicas
3. Configure resource limits if needed

## Custom Domain

To add a custom domain:
1. Go to service settings
2. Click "Generate Domain" for a Railway subdomain
3. Or add your custom domain and configure DNS

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
