"""Initialize Flask app."""
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


def init_app():
    """Construct core Flask application."""
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
        from . import api
        from .assets import compile_static_assets
        from .models import User, Mortgage, Mortgage_Tracking, Alert, Trigger

        # import dash app
        # from .plotlydash.dashboard import init_dashboard
        from .dash.refi_calculator_dash import init_dashboard

        app = init_dashboard(app)

        # Register Blueprints
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(mortgage.mortgage_bp)
        app.register_blueprint(api.api_bp)

        # Exempt API endpoints from CSRF protection (uses token-based auth)
        csrf.exempt(api.api_bp)

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

        # Initialize background scheduler for alert checking
        from .scheduler import init_scheduler
        init_scheduler(app)

        return app
