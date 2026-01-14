# """Compile static assets."""
# from flask import current_app as app
# from flask_assets import Bundle


# def compile_static_assets(assets):
#     """
#     Compile stylesheets if in development mode.
#     :param assets: Flask-Assets Environment
#     :type assets: Environment
#     """
#     assets.auto_build = True
#     assets.debug = False
#     less_bundle = Bundle(
#         "less/*.less",
#         filters="less,cssmin",
#         output="/static/dist/css/styles.css",
#         extra={"rel": "stylesheet/less"},
#     )
#     assets.register("less_all", less_bundle)
#     if app.config["FLASK_ENV"] == "development":
#         less_bundle.build()
#     return assets

"""Create and bundle CSS and JS files."""
import os
from flask_assets import Bundle, Environment


def compile_static_assets(assets):
    """Configure static asset bundles.

    In production, assets are pre-built during Docker build, so we skip
    runtime compilation. In development, we compile on startup.
    """
    # Skip compilation in production (assets are pre-built in Docker)
    if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RAILWAY_ENVIRONMENT'):
        return

    # Development only: compile LESS and JS on startup
    # Stylesheets Bundles
    account_less_bundle = Bundle(
        'src/less/account.less',
        filters='less,cssmin',
        output='dist/css/account.css',
        extra={'rel': 'stylesheet/less'},
    )
    dashboard_less_bundle = Bundle(
        'src/less/dashboard.less',
        filters='less,cssmin',
        output='dist/css/dashboard.css',
        extra={'rel': 'stylesheet/less'},
    )
    vars_less_bundle = Bundle(
        'src/less/vars.less',
        filters='less,cssmin',
        output='dist/css/vars.css',
        extra={'rel': 'stylesheet/less'},
    )
    # JavaScript Bundle
    js_bundle = Bundle('src/js/main.js', filters='jsmin', output='dist/js/main.min.js')
    # Register assets
    assets.register('account_less_bundle', account_less_bundle)
    # assets.register('dashboard_less_bundle', dashboard_less_bundle)
    assets.register('vars_less_bundle', dashboard_less_bundle)
    assets.register('js_all', js_bundle)
    # Build assets
    account_less_bundle.build()
    # dashboard_less_bundle.build()
    # vars_less_bundle.build()
    js_bundle.build()
