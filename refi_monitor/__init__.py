"""Initialize Flask app."""
from flask import Flask
from flask_assets import Environment


def init_app():
    """Construct core Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    assets = Environment()
    assets.init_app(app)

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes
        from .assets import compile_static_assets

        # import dash app
        # from .plotlydash.dashboard import init_dashboard
        from .dash.refi_calculator_dash import init_dashboard

        app = init_dashboard(app)

        # Compile static assets
        compile_static_assets(assets)

        return app
