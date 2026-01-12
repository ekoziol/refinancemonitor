"""Flask config."""
from os import environ, path

from dotenv import load_dotenv

BASE_DIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASE_DIR, ".env"))


class Config:
    """Flask configuration variables."""

    # General Config
    FLASK_APP = environ.get("FLASK_APP")
    FLASK_ENV = environ.get("FLASK_ENV")
    SECRET_KEY = environ.get("SECRET_KEY")

    # Assets
    LESS_BIN = environ.get("LESS_BIN")
    ASSETS_DEBUG = environ.get("ASSETS_DEBUG")
    LESS_RUN_IN_DEBUG = environ.get("LESS_RUN_IN_DEBUG")

    # Static Assets
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"
    COMPRESSOR_DEBUG = environ.get("COMPRESSOR_DEBUG")

    # Database - Railway provides DATABASE_URL, fallback to SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI') or environ.get('DATABASE_URL')
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STRIPE_API_KEY = environ.get("STRIPE_API_KEY")

    # Scheduler Config
    RATE_UPDATE_HOUR = int(environ.get("RATE_UPDATE_HOUR", "9"))  # 9 AM EST default
    RATE_UPDATE_MINUTE = int(environ.get("RATE_UPDATE_MINUTE", "0"))  # 00 minutes default
    ENABLE_SCHEDULER = environ.get("ENABLE_SCHEDULER", "true").lower() == "true"

    # Email Configuration
    MAIL_SERVER = environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = environ.get("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER", "noreply@refialert.com")


class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    DATABASE_URI = environ.get('PROD_DATABASE_URI')


class DevConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
    DATABASE_URI = environ.get('DEV_DATABASE_URI')
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
