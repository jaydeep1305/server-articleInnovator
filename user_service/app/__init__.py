"""
Flask Application Factory for User Management Microservice.

This module implements the application factory pattern for creating
Flask applications with proper configuration, extensions, and blueprints.
"""

from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

from config import get_config, BaseConfig

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


def create_app(environment: Optional[str] = None) -> Flask:
    """
    Application factory function that creates and configures Flask application.
    
    This function implements the application factory pattern, allowing for
    easy testing and deployment across different environments.
    
    Args:
        environment: Configuration environment ('development', 'testing', 'production')
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Configured Flask application instance
        
    Example:
        >>> app = create_app('development')
        >>> app.run(debug=True)
    """
    # Create Flask application instance
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(environment)
    app.config.from_object(config)
    
    # Initialize extensions with app
    _initialize_extensions(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Configure logging
    _configure_logging(app, config)
    
    # Register error handlers
    _register_error_handlers(app)
    
    return app


def _initialize_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions with the application instance.
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    migrate.init_app(app, db)


def _register_blueprints(app: Flask) -> None:
    """
    Register application blueprints for modular routing.
    
    Args:
        app: Flask application instance
    """
    from app.routes.user_routes import user_bp
    from app.routes.profile_routes import profile_bp
    from app.routes.role_routes import role_bp
    from app.routes.health_routes import health_bp
    
    # Register API blueprints with version prefix
    api_prefix = app.config.get('API_PREFIX', '/api/v1')
    
    app.register_blueprint(user_bp, url_prefix=f"{api_prefix}/users")
    app.register_blueprint(profile_bp, url_prefix=f"{api_prefix}/profiles")
    app.register_blueprint(role_bp, url_prefix=f"{api_prefix}/roles")
    app.register_blueprint(health_bp, url_prefix="/health")


def _configure_logging(app: Flask, config: BaseConfig) -> None:
    """
    Configure application logging based on environment.
    
    Args:
        app: Flask application instance
        config: Configuration object with logging settings
    """
    if not app.debug and not app.testing:
        # Configure logging for production
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL, logging.INFO),
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        
        app.logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))


def _register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers for consistent error responses.
    
    Args:
        app: Flask application instance
    """
    from app.utils.error_handlers import (
        handle_validation_error,
        handle_not_found_error,
        handle_internal_error,
        handle_bad_request
    )
    
    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(404, handle_not_found_error)
    app.register_error_handler(422, handle_validation_error)
    app.register_error_handler(500, handle_internal_error)


# Export commonly used objects for easy importing
__all__ = ['create_app', 'db']