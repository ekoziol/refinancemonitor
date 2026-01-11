"""JSON error handlers for the API blueprint."""
from flask import jsonify
from . import api_bp


@api_bp.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    return jsonify({
        'error': 'Bad Request',
        'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
    }), 400


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    return jsonify({
        'error': 'Not Found',
        'message': str(error.description) if hasattr(error, 'description') else 'Resource not found'
    }), 404


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


@api_bp.errorhandler(422)
def unprocessable_entity(error):
    """Handle 422 Unprocessable Entity errors."""
    return jsonify({
        'error': 'Unprocessable Entity',
        'message': str(error.description) if hasattr(error, 'description') else 'Invalid data'
    }), 422
