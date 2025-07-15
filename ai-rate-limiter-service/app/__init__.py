"""
Ai Rate Limiter Service - Flask Application Factory

This module contains the Flask application factory function that creates
and configures the Flask application instance with all necessary extensions,
blueprints, and middleware.

Author: AI Assistant
Date: 2024
"""

import logging
from typing import Optional
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(
    get_remote_address,
    default_limits=["1000 per hour"]
)


def create_app(config: Optional[object] = None) -> Flask:
    """
    Application factory function.
    
    Creates and configures a Flask application instance with all necessary
    extensions, blueprints, error handlers, and middleware.
    
    Args:
        config: Configuration object (optional)
        
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        from config import get_config
        app.config.from_object(get_config())
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register middleware
    register_middleware(app)
    
    # Setup logging
    setup_app_logging(app)
    
    return app


def init_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    
    # Database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # JWT
    jwt.init_app(app)
    
    # CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Rate limiting
    limiter.init_app(app)


def register_blueprints(app: Flask) -> None:
    """Register application blueprints."""
    
    # Health check routes
    from app.routes.health import health_bp
    app.register_blueprint(health_bp)
    
    # API routes will be added here as they are created
    # from app.routes.api import api_bp
    # app.register_blueprint(api_bp, url_prefix=app.config['API_PREFIX'])


def register_error_handlers(app: Flask) -> None:
    """Register application error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors."""
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized errors."""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden errors."""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource could not be found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle validation errors."""
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': 'The request was well-formed but was unable to be followed due to semantic errors',
            'status_code': 422
        }), 422
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        """Handle rate limit errors."""
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'status_code': 429,
            'retry_after': error.retry_after
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle internal server errors."""
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred',
            'status_code': 500
        }), 500


def register_middleware(app: Flask) -> None:
    """Register application middleware."""
    
    @app.before_request
    def log_request_info():
        """Log request information."""
        app.logger.info(f"{request.method} {request.url} - {request.remote_addr}")
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Add service identification header
        response.headers['X-Service'] = app.config.get('SERVICE_NAME', 'ai-rate-limiter-service')
        response.headers['X-Service-Version'] = app.config.get('SERVICE_VERSION', '1.0.0')
        
        return response


def setup_app_logging(app: Flask) -> None:
    """Setup application-specific logging."""
    
    if not app.debug and not app.testing:
        # Production logging setup
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        import os
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Setup file handler
        file_handler = RotatingFileHandler(
            'logs/ai-rate-limiter-service.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info(f'Ai Rate Limiter Service startup')
