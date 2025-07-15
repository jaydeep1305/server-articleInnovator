"""
Configuration module for Flask Microservice.

This module provides environment-specific configuration classes that handle
database connections, JWT settings, and other application configurations
with strict type annotations and validation.

Author: AI Assistant
Date: 2024
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """Enumeration for different deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration with type safety."""
    host: str
    port: int
    username: str
    password: str
    database: str
    
    @property
    def url(self) -> str:
        """Generate SQLAlchemy database URL."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class BaseConfig:
    """
    Base configuration class with common settings.
    
    This class provides default configuration values and utility methods
    that are inherited by environment-specific configuration classes.
    """
    
    # Flask Settings
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = False
    TESTING: bool = False
    
    # Database Settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '3600'))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))  # 30 days
    
    # Pagination Settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # API Versioning
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    
    # Event-Driven Architecture Settings
    MESSAGE_BROKER_URL: str = os.environ.get('MESSAGE_BROKER_URL', 'redis://localhost:6379/0')
    EVENT_STORE_URL: str = os.environ.get('EVENT_STORE_URL', 'redis://localhost:6379/1')
    
    # Logging Settings
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """
        Retrieve database configuration from environment variables.
        
        Returns:
            DatabaseConfig: Configured database connection parameters
            
        Raises:
            ValueError: If required database environment variables are missing
        """
        required_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required database environment variables: {missing_vars}")
        
        return DatabaseConfig(
            host=os.environ['DB_HOST'],
            port=int(os.environ['DB_PORT']),
            username=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            database=os.environ['DB_NAME']
        )


class DevelopmentConfig(BaseConfig):
    """
    Development environment configuration.
    
    This configuration enables debug mode, verbose logging, and uses
    local database connections suitable for development.
    """
    
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True
    LOG_LEVEL: str = 'DEBUG'
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """Get development database configuration with defaults."""
        return DatabaseConfig(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=int(os.environ.get('DB_PORT', '5432')),
            username=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'postgres'),
            database=os.environ.get('DB_NAME', 'flask_microservice_dev')
        )


class TestingConfig(BaseConfig):
    """
    Testing environment configuration.
    
    This configuration is optimized for running unit and integration tests
    with in-memory or test-specific database connections.
    """
    
    TESTING: bool = True
    DEBUG: bool = True
    
    # Use SQLite for faster testing
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED: bool = False
    
    # Shorter token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES: int = 300  # 5 minutes
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """Get testing database configuration."""
        return DatabaseConfig(
            host=os.environ.get('TEST_DB_HOST', 'localhost'),
            port=int(os.environ.get('TEST_DB_PORT', '5432')),
            username=os.environ.get('TEST_DB_USER', 'postgres'),
            password=os.environ.get('TEST_DB_PASSWORD', 'postgres'),
            database=os.environ.get('TEST_DB_NAME', 'flask_microservice_test')
        )


class ProductionConfig(BaseConfig):
    """
    Production environment configuration.
    
    This configuration provides security-focused settings, optimized
    performance parameters, and production-ready database connections.
    """
    
    DEBUG: bool = False
    
    # Enhanced security settings
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # Production logging
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'WARNING')


# Configuration mapping for easy environment switching
CONFIG_MAPPING: Dict[str, type] = {
    Environment.DEVELOPMENT.value: DevelopmentConfig,
    Environment.TESTING.value: TestingConfig,
    Environment.PRODUCTION.value: ProductionConfig
}


def get_config(environment: Optional[str] = None) -> BaseConfig:
    """
    Factory function to get configuration based on environment.
    
    Args:
        environment: Target environment name. If None, uses FLASK_ENV environment variable.
        
    Returns:
        BaseConfig: Configuration instance for the specified environment
        
    Raises:
        ValueError: If the specified environment is not supported
        
    Example:
        >>> config = get_config('development')
        >>> print(config.DEBUG)  # True
    """
    if environment is None:
        environment = os.environ.get('FLASK_ENV', Environment.DEVELOPMENT.value)
    
    config_class = CONFIG_MAPPING.get(environment)
    if config_class is None:
        raise ValueError(f"Unsupported environment: {environment}")
    
    return config_class()


def validate_config(config: BaseConfig) -> bool:
    """
    Validate configuration settings for completeness and correctness.
    
    Args:
        config: Configuration instance to validate
        
    Returns:
        bool: True if configuration is valid
        
    Raises:
        ValueError: If configuration validation fails
    """
    if not config.SECRET_KEY or config.SECRET_KEY == 'dev-secret-key-change-in-production':
        if not config.DEBUG:
            raise ValueError("SECRET_KEY must be set for non-development environments")
    
    if config.JWT_ACCESS_TOKEN_EXPIRES <= 0:
        raise ValueError("JWT_ACCESS_TOKEN_EXPIRES must be positive")
    
    try:
        db_config = config.get_database_config()
        if not all([db_config.host, db_config.username, db_config.database]):
            raise ValueError("Database configuration is incomplete")
    except Exception as e:
        raise ValueError(f"Database configuration error: {e}")
    
    return True