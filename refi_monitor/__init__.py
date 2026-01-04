"""Initialize Flask app."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_assets import Environment
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


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

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes
        from . import auth
        from . import mortgage
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
        # Compile static assets
        compile_static_assets(assets)
        db.create_all()
        return app
