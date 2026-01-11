"""API module for calculator endpoints."""
from flask import Blueprint

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

from . import calculator  # noqa: E402, F401
