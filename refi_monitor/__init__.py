"""Initialize Flask app."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_assets import Environment
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()


def init_sentry():
    """Initialize Sentry for error tracking in production."""
    sentry_dsn = os.environ.get('SENTRY_DSN')
    if sentry_dsn and os.environ.get('FLASK_ENV') == 'production':
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=os.environ.get('FLASK_ENV', 'development'),
        )


def init_app():
    """Construct core Flask application."""
    # Initialize Sentry before creating the app
    init_sentry()

    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    assets = Environment()
    assets.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes
        from . import auth
        from . import mortgage
        from .assets import compile_static_assets
        from .models import User, Mortgage, Mortgage_Tracking, Alert, Trigger

        # import dash apps
        # from .plotlydash.dashboard import init_dashboard
        from .dash.refi_calculator_dash import init_dashboard
        from .dash.rate_history_dash import init_rate_history_dashboard

        app = init_dashboard(app)
        app = init_rate_history_dashboard(app)

        # Register Blueprints
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(mortgage.mortgage_bp)

        # Register API blueprints
        from .api.rates import rates_bp
        app.register_blueprint(rates_bp)

        # Register CLI commands
        from . import cli
        cli.register_commands(app)

        # Initialize scheduler for automated tasks
        if app.config.get('ENABLE_SCHEDULER', True):
            from .scheduler import init_scheduler
            init_scheduler(app)

        # Compile static assets
        compile_static_assets(assets)
        db.create_all()

        return app
