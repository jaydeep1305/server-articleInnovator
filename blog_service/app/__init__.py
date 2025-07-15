"""
Application factory for the Blog Microservice.

This module creates and configures the Flask application with all
necessary extensions, blueprints, and error handlers.

Functions:
    create_app: Application factory function
    register_blueprints: Register all route blueprints
    register_error_handlers: Register global error handlers
"""

import os
from typing import Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

from config.config import get_config
from app.models.base import db


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Configured Flask application instance
        
    Example:
        app = create_app('development')
    """
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Configure CORS
    CORS(app, origins=getattr(config_class, 'CORS_ORIGINS', ['*']))
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        if config_name == 'testing':
            db.create_all()
    
    return app


def register_blueprints(app: Flask) -> None:
    """
    Register all application blueprints.
    
    Args:
        app: Flask application instance
    """
    from app.routes.user_routes import user_bp
    from app.routes.article_routes import article_bp
    from app.routes.comment_routes import comment_bp
    from app.routes.health_routes import health_bp
    
    # API version prefix
    api_prefix = f"/api/{app.config.get('API_VERSION', 'v1')}"
    
    # Register blueprints with API versioning
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(user_bp, url_prefix=f"{api_prefix}/users")
    app.register_blueprint(article_bp, url_prefix=f"{api_prefix}/articles")
    app.register_blueprint(comment_bp, url_prefix=f"{api_prefix}/comments")


def register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers for the application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors."""
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was invalid or malformed',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized errors."""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden errors."""
        return jsonify({
            'error': 'Forbidden',
            'message': 'Access denied',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle method not allowed errors."""
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The HTTP method is not allowed for this endpoint',
            'status_code': 405
        }), 405
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle validation errors."""
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': 'Validation failed',
            'status_code': 422
        }), 422
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle rate limit errors."""
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests',
            'status_code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle internal server errors."""
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    
    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle ValueError exceptions."""
        return jsonify({
            'error': 'Validation Error',
            'message': str(error),
            'status_code': 400
        }), 400
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle generic exceptions."""
        # Log the error for debugging
        app.logger.error(f"Unhandled exception: {str(error)}")
        
        # Don't expose internal error details in production
        if app.config.get('DEBUG'):
            message = str(error)
        else:
            message = 'An unexpected error occurred'
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': message,
            'status_code': 500
        }), 500
    
    @app.before_request
    def log_request_info():
        """Log request information for debugging."""
        if app.config.get('DEBUG'):
            app.logger.debug(f"Request: {request.method} {request.url}")
            if request.is_json:
                app.logger.debug(f"Request JSON: {request.get_json()}")
    
    @app.after_request
    def after_request(response):
        """Add headers to response."""
        # Add CORS headers if not already added
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response