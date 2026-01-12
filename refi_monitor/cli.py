"""Flask CLI commands for refi_monitor."""
import click
from flask import current_app
from .rate_updater import RateUpdater, RateFetcher
import logging

logger = logging.getLogger(__name__)


def register_commands(app):
    """Register CLI commands with Flask app."""

    @app.cli.command('update-rates')
    @click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
    def update_rates_command(verbose):
        """
        Update all mortgage rates with current market data.

        This command fetches the latest mortgage rates and updates all
        active mortgage tracking records. It also checks alerts and
        triggers notifications for users whose target rates have been met.

        Usage:
            flask update-rates
            flask update-rates --verbose
        """
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        click.echo("🏠 Starting mortgage rate update...")

        try:
            updater = RateUpdater()
            results = updater.update_all_rates()

            click.echo(f"✅ Successfully updated {results['updated']} mortgage records")
            click.echo(f"📊 Current 30-year rate: {results['current_rate']:.4f} ({results['current_rate']*100:.2f}%)")
            click.echo(f"🔔 Triggered {results['alerts_triggered']} alerts")

        except Exception as e:
            click.echo(f"❌ Error updating rates: {e}", err=True)
            logger.exception("Rate update failed")
            raise click.Abort()

    @app.cli.command('test-rate-fetch')
    def test_rate_fetch_command():
        """
        Test rate fetching without updating database.

        Usage:
            flask test-rate-fetch
        """
        click.echo("🧪 Testing rate fetcher...")

        try:
            fetcher = RateFetcher()
            rates = fetcher.fetch_current_rates()

            click.echo("\n📈 Fetched rates:")
            for rate_type, rate in rates.items():
                click.echo(f"  {rate_type:15s}: {rate:.4f} ({rate*100:.2f}%)")

        except Exception as e:
            click.echo(f"❌ Error fetching rates: {e}", err=True)
            logger.exception("Rate fetch test failed")
            raise click.Abort()

    @app.cli.command('scheduler-status')
    def scheduler_status_command():
        """
        Display the status of scheduled jobs.

        Usage:
            flask scheduler-status
        """
        from .scheduler import get_scheduler_status

        click.echo("📅 Scheduler Status\n")

        jobs = get_scheduler_status()

        if not jobs:
            click.echo("⚠️  No scheduled jobs found. Scheduler may be disabled.")
            click.echo("   Set ENABLE_SCHEDULER=true in .env to enable.")
            return

        for job in jobs:
            click.echo(f"Job: {job['name']} (ID: {job['id']})")
            click.echo(f"  Next run: {job['next_run']}")
            click.echo(f"  Trigger: {job['trigger']}")
            click.echo()

    @app.cli.command('check-alerts')
    @click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
    def check_alerts_command(verbose):
        """
        Check all active alerts and trigger notifications if conditions are met.

        This command is designed to be run by Heroku Scheduler or cron jobs.
        It evaluates all active paid alerts against current market rates.

        Usage:
            flask check-alerts
            flask check-alerts --verbose
        """
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        click.echo("🔔 Checking alerts...")

        try:
            from .scheduler import check_and_trigger_alerts
            check_and_trigger_alerts()
            click.echo("✅ Alert check completed successfully")

        except Exception as e:
            click.echo(f"❌ Error checking alerts: {e}", err=True)
            logger.exception("Alert check failed")
            raise click.Abort()
