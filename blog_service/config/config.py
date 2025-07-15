"""
Configuration module for the Blog Microservice.

This module defines configuration classes for different environments
(development, testing, production) with proper type annotations and
comprehensive documentation.

Classes:
    Config: Base configuration class
    DevelopmentConfig: Development environment configuration
    TestingConfig: Testing environment configuration
    ProductionConfig: Production environment configuration

Example:
    from config.config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Base configuration class containing common settings.
    
    This class defines default configuration values that are
    inherited by environment-specific configuration classes.
    
    Attributes:
        SECRET_KEY: Application secret key for session management
        SQLALCHEMY_TRACK_MODIFICATIONS: Disable SQLAlchemy event system
        SQLALCHEMY_RECORD_QUERIES: Enable query recording for debugging
        JSON_SORT_KEYS: Sort JSON response keys for consistency
        API_VERSION: Current API version for versioning
        MAX_CONTENT_LENGTH: Maximum request content length
    """
    
    # Security Configuration
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_RECORD_QUERIES: bool = True
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # JSON Configuration
    JSON_SORT_KEYS: bool = False
    
    # API Configuration
    API_VERSION: str = 'v1'
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # Pagination Configuration
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    @staticmethod
    def init_app(app) -> None:
        """
        Initialize application with configuration.
        
        Args:
            app: Flask application instance
            
        Note:
            This method can be overridden in subclasses to add
            environment-specific initialization logic.
        """
        pass


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    This configuration is optimized for development with
    debug mode enabled and local database settings.
    
    Attributes:
        DEBUG: Enable debug mode for development
        SQLALCHEMY_DATABASE_URI: Local PostgreSQL database URI
        SQLALCHEMY_ECHO: Enable SQL query logging
    """
    
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = (
        os.environ.get('DEV_DATABASE_URL') or
        'postgresql://blog_user:blog_password@localhost:5432/blog_dev'
    )
    SQLALCHEMY_ECHO: bool = True  # Log all SQL statements
    
    # CORS Configuration for development
    CORS_ORIGINS: list[str] = ['http://localhost:3000', 'http://localhost:8080']


class TestingConfig(Config):
    """
    Testing environment configuration.
    
    This configuration is designed for running tests with
    an in-memory or separate test database.
    
    Attributes:
        TESTING: Enable testing mode
        SQLALCHEMY_DATABASE_URI: Test database URI
        WTF_CSRF_ENABLED: Disable CSRF for testing
    """
    
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = (
        os.environ.get('TEST_DATABASE_URL') or
        'postgresql://blog_user:blog_password@localhost:5432/blog_test'
    )
    WTF_CSRF_ENABLED: bool = False
    
    # Disable query logging in tests for performance
    SQLALCHEMY_ECHO: bool = False


class ProductionConfig(Config):
    """
    Production environment configuration.
    
    This configuration is optimized for production deployment
    with security and performance considerations.
    
    Attributes:
        SQLALCHEMY_DATABASE_URI: Production database URI
        SECRET_KEY: Production secret key (must be set via environment)
    """
    
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or \
        'postgresql://blog_user:blog_password@db:5432/blog_prod'
    
    # Security enhancements for production
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # Disable debug mode and SQL echoing in production
    DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False
    
    @classmethod
    def init_app(cls, app) -> None:
        """
        Initialize production-specific application settings.
        
        Args:
            app: Flask application instance
            
        Raises:
            RuntimeError: If SECRET_KEY is not set in production
        """
        Config.init_app(app)
        
        # Ensure SECRET_KEY is set in production
        if not os.environ.get('SECRET_KEY'):
            raise RuntimeError(
                'SECRET_KEY environment variable must be set in production'
            )


# Configuration dictionary for easy access
config: Dict[str, type[Config]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> type[Config]:
    """
    Get configuration class based on environment name.
    
    Args:
        config_name: Name of the configuration environment
        
    Returns:
        Configuration class for the specified environment
        
    Example:
        config_class = get_config('development')
        app.config.from_object(config_class)
    """
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, DevelopmentConfig)