# RefiAlert - Automated Mortgage Refinancing Alert System

A Flask-based web application that monitors mortgage rates and automatically notifies users when favorable refinancing conditions are met.

## Repository Mirror

This repository is a read-only mirror of the primary GitLab repository.

**Primary Repository:** https://gitlab.com/ekoziol/refi-alert

Please submit issues and merge requests to the GitLab repository.

## Features

- **Mortgage Tracking**: Users can add and manage multiple mortgages with detailed information
- **Custom Alert Configuration**: Set target monthly payments or interest rates for refinancing
- **Automated Rate Monitoring**: Background scheduler checks market rates periodically
- **Email Notifications**: Automatic alerts when refinancing conditions are met
- **Payment Integration**: Stripe subscription-based alert service
- **Interactive Dashboard**: Visualize mortgage data and refinancing opportunities

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- SMTP email account (Gmail, SendGrid, etc.)
- Stripe account (for payment processing)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd refi_alert
```

2. Create virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
flask db upgrade
```

5. Run the application:
```bash
python wsgi.py
```

The application will be available at `http://localhost:5000`

## Configuration

See `.env.example` for all required environment variables. Key configurations:

### Email Setup (Required for Notifications)

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

For Gmail, create an app password: https://myaccount.google.com/apppasswords

### Stripe Setup (Required for Payments)

```bash
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Architecture

### Components

- **Flask Web Application**: User interface and API
- **PostgreSQL Database**: Data persistence
- **Flask-Mail**: Email delivery
- **APScheduler**: Background job scheduler
- **Stripe**: Payment processing
- **Plotly/Dash**: Interactive mortgage calculators

### Key Modules

- `refi_monitor/notifications.py` - Email notification service
- `refi_monitor/scheduler.py` - Background alert evaluation
- `refi_monitor/mortgage.py` - Mortgage and alert management
- `refi_monitor/calc.py` - Mortgage calculation utilities

## Usage

### For Users

1. **Sign up** and create an account
2. **Add a mortgage** with your current loan details
3. **Set an alert** with target refinancing conditions
4. **Subscribe** via Stripe to activate monitoring
5. **Receive notifications** when conditions are met

### For Administrators

Manually trigger alert checks:

```bash
curl -X POST http://localhost:5000/admin/trigger-alerts \
  -H "Content-Type: application/json" \
  --cookie "session=<session-cookie>"
```

## Automated Distribution System

The application includes a comprehensive automated publishing and distribution system:

- **Scheduled Monitoring**: Checks alerts daily at 9 AM and every 4 hours
- **Smart Evaluation**: Accounts for refinance costs and prevents duplicate notifications
- **Rich Email Templates**: HTML emails with detailed refinancing information
- **Payment Integration**: Automatic payment confirmations

For detailed documentation, see [DISTRIBUTION.md](DISTRIBUTION.md)

## Development

### Project Structure

```
refi_alert/
├── refi_monitor/          # Main application package
│   ├── __init__.py       # App initialization
│   ├── models.py         # Database models
│   ├── routes.py         # Main routes
│   ├── auth.py          # Authentication
│   ├── mortgage.py      # Mortgage/alert routes
│   ├── notifications.py # Email service (NEW)
│   ├── scheduler.py     # Background jobs (NEW)
│   ├── calc.py          # Calculation utilities
│   ├── forms.py         # WTForms
│   ├── plots.py         # Plotly charts
│   └── dash/            # Dash apps
├── config.py            # Configuration
├── wsgi.py             # WSGI entry point
├── requirements.txt    # Dependencies
└── migrations/         # Database migrations
```

### Running Tests

```bash
# TODO: Add test suite
pytest
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade

# Rollback
flask db downgrade
```

## Production Deployment

### Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up production email service (SendGrid/SES)
- [ ] Configure Stripe production keys
- [ ] Integrate real mortgage rate API
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (nginx)
- [ ] Set up monitoring and logging
- [ ] Add proper admin role checking

### Deployment Platforms

- **Heroku**: Add `Procfile` and use Heroku Postgres
- **AWS**: EC2 + RDS or Elastic Beanstalk
- **Google Cloud**: App Engine or Cloud Run
- **DigitalOcean**: App Platform or Droplet

## API Integration

The system is ready to integrate with real mortgage rate APIs:

### Recommended APIs

1. **Freddie Mac Primary Mortgage Market Survey** (Free)
   - Weekly rate data
   - http://www.freddiemac.com/pmms/

2. **Mortgage News Daily** (Paid)
   - Real-time rates
   - Location-specific data

3. **Zillow Mortgage API** (Paid)
   - Zip code-specific rates

To integrate, update `get_current_mortgage_rates()` in `refi_monitor/scheduler.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Check [DISTRIBUTION.md](DISTRIBUTION.md) for distribution system docs
- Review application logs
- Open an issue on GitHub
