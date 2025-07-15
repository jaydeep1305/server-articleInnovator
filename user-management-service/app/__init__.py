"""
Flask Application Factory for User Management Service.

This module creates and configures the Flask application instance with all
necessary extensions, error handlers, and blueprints. It implements the
Application Factory pattern for better testability and configuration management.

Author: AI Assistant
Date: 2024
"""

import logging
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import get_config, setup_logging, BaseConfig

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory function that creates and configures Flask app.
    
    This function implements the Application Factory pattern, allowing
    for different configurations and better testing support. It handles
    all the cognitive setup patterns for a production-ready microservice.
    
    Args:
        config_name: Configuration environment name (development, testing, production)
        
    Returns:
        Flask: Configured Flask application instance
        
    Example:
        >>> app = create_app('development')
        >>> app.run(debug=True)
        >>>
        >>> # For testing
        >>> test_app = create_app('testing')
        >>> with test_app.test_client() as client:
        ...     response = client.get('/health')
    """
    # Create Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Setup logging
    setup_logging(config)
    logger.info(f"Starting {config.SERVICE_NAME} v{config.SERVICE_VERSION}")
    
    # Validate configuration
    try:
        config.validate_config()
        logger.info("Configuration validation passed")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Configure database
    if hasattr(config, 'SQLALCHEMY_DATABASE_URI'):
        # Use SQLite for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    else:
        # Use PostgreSQL for development/production
        db_config = config.get_database_config()
        app.config['SQLALCHEMY_DATABASE_URI'] = db_config.url
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Add request/response middleware
    setup_middleware(app)
    
    logger.info("Flask application created and configured successfully")
    return app


def initialize_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions with the app instance.
    
    This function implements the extension initialization pattern,
    properly configuring each extension with cognitive error handling.
    
    Args:
        app: Flask application instance
    """
    try:
        # Initialize database
        db.init_app(app)
        logger.info("SQLAlchemy initialized")
        
        # Initialize JWT
        jwt.init_app(app)
        configure_jwt(app)
        logger.info("JWT Manager initialized")
        
        # Initialize rate limiter
        limiter.init_app(app)
        logger.info("Rate limiter initialized")
        
        # Initialize CORS
        CORS(app, resources={
            r"/api/*": {
                "origins": ["http://localhost:3000", "http://localhost:5000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
        logger.info("CORS initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize extensions: {e}")
        raise


def configure_jwt(app: Flask) -> None:
    """
    Configure JWT manager with custom handlers and settings.
    
    This function implements cognitive JWT configuration patterns
    for secure token management and proper error handling.
    
    Args:
        app: Flask application instance
    """
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header: Dict[str, Any], jwt_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle expired JWT tokens."""
        return jsonify({
            'error': 'token_expired',
            'message': 'The token has expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error: str) -> Dict[str, Any]:
        """Handle invalid JWT tokens."""
        return jsonify({
            'error': 'invalid_token',
            'message': 'The token is invalid'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error: str) -> Dict[str, Any]:
        """Handle missing JWT tokens."""
        return jsonify({
            'error': 'authorization_required',
            'message': 'Request does not contain an access token'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header: Dict[str, Any], jwt_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle revoked JWT tokens."""
        return jsonify({
            'error': 'token_revoked',
            'message': 'The token has been revoked'
        }), 401


def register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers for the application.
    
    This function implements cognitive error handling patterns
    that provide consistent error responses and proper logging.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> Dict[str, Any]:
        """Handle HTTP exceptions with consistent format."""
        logger.warning(f"HTTP {error.code}: {error.description}")
        return jsonify({
            'error': error.name.lower().replace(' ', '_'),
            'message': error.description,
            'status_code': error.code
        }), error.code
    
    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError) -> Dict[str, Any]:
        """Handle ValueError exceptions."""
        logger.error(f"ValueError: {str(error)}")
        return jsonify({
            'error': 'validation_error',
            'message': str(error)
        }), 400
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception) -> Dict[str, Any]:
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return jsonify({
            'error': 'internal_server_error',
            'message': 'An unexpected error occurred'
        }), 500


def register_blueprints(app: Flask) -> None:
    """
    Register all application blueprints.
    
    This function implements the Blueprint registration pattern
    for modular route organization and API versioning.
    
    Args:
        app: Flask application instance
    """
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.roles import roles_bp
    from app.routes.health import health_bp
    
    # Register blueprints with API prefix
    api_prefix = app.config.get('API_PREFIX', '/api/v1')
    
    app.register_blueprint(health_bp, url_prefix='/')  # Health check at root
    app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(users_bp, url_prefix=f'{api_prefix}/users')
    app.register_blueprint(roles_bp, url_prefix=f'{api_prefix}/roles')
    
    logger.info(f"Blueprints registered with prefix: {api_prefix}")


def setup_middleware(app: Flask) -> None:
    """
    Setup request/response middleware for the application.
    
    This function implements cognitive middleware patterns for
    logging, request correlation, and response standardization.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request() -> None:
        """Execute before each request."""
        # Log request details in debug mode
        if app.config.get('DEBUG'):
            logger.debug(f"Request: {request.method} {request.path}")
            if request.json:
                # Don't log sensitive data
                safe_data = {k: v for k, v in request.json.items() 
                           if k not in ['password', 'token', 'secret']}
                logger.debug(f"Request data: {safe_data}")
    
    @app.after_request
    def after_request(response):
        """Execute after each request."""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Add API version header
        response.headers['API-Version'] = app.config.get('API_VERSION', 'v1')
        response.headers['Service-Name'] = app.config.get('SERVICE_NAME', 'user-management-service')
        
        # Log response in debug mode
        if app.config.get('DEBUG'):
            logger.debug(f"Response: {response.status_code}")
        
        return response


# CLI commands for database management
def register_cli_commands(app: Flask) -> None:
    """
    Register CLI commands for database and application management.
    
    This function provides cognitive CLI commands for common
    administrative tasks and database operations.
    
    Args:
        app: Flask application instance
    """
    @app.cli.command()
    def init_db():
        """Initialize the database with all tables."""
        try:
            db.create_all()
            logger.info("Database tables created successfully")
            print("Database initialized successfully!")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            print(f"Database initialization failed: {e}")
    
    @app.cli.command()
    def seed_db():
        """Seed the database with initial data."""
        try:
            from app.utils.seed_data import seed_initial_data
            seed_initial_data()
            logger.info("Database seeded successfully")
            print("Database seeded successfully!")
        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            print(f"Database seeding failed: {e}")
    
    @app.cli.command()
    def reset_db():
        """Reset the database (drop all tables and recreate)."""
        try:
            db.drop_all()
            db.create_all()
            logger.info("Database reset successfully")
            print("Database reset successfully!")
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            print(f"Database reset failed: {e}")