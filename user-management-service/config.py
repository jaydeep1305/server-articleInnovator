"""
Configuration module for User Management Service.

This module provides environment-specific configuration classes that handle
database connections, JWT settings, RabbitMQ connections, and other application
configurations with strict type annotations and validation.

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
    """
    Database configuration with type safety.
    
    This dataclass encapsulates all database connection parameters
    required for PostgreSQL connectivity with proper type annotations.
    
    Attributes:
        host (str): Database host address
        port (int): Database port number
        username (str): Database username
        password (str): Database password
        database (str): Database name
        pool_size (int): Connection pool size
        max_overflow (int): Maximum connection overflow
        pool_timeout (int): Connection pool timeout in seconds
    """
    host: str
    port: int
    username: str
    password: str
    database: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    
    @property
    def url(self) -> str:
        """
        Generate SQLAlchemy database URL.
        
        Returns:
            str: Formatted PostgreSQL connection URL
            
        Example:
            >>> db_config = DatabaseConfig("localhost", 5432, "user", "pass", "db")
            >>> print(db_config.url)
            postgresql://user:pass@localhost:5432/db
        """
        return (f"postgresql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}")


@dataclass
class RabbitMQConfig:
    """
    RabbitMQ configuration for event-driven communication.
    
    This dataclass contains all necessary parameters for connecting
    to RabbitMQ message broker for inter-service communication.
    
    Attributes:
        host (str): RabbitMQ host address
        port (int): RabbitMQ port number
        username (str): RabbitMQ username
        password (str): RabbitMQ password
        virtual_host (str): RabbitMQ virtual host
        exchange_name (str): Main exchange name for events
    """
    host: str
    port: int
    username: str
    password: str
    virtual_host: str = "/"
    exchange_name: str = "events"
    
    @property
    def url(self) -> str:
        """
        Generate RabbitMQ connection URL.
        
        Returns:
            str: Formatted RabbitMQ connection URL
        """
        return (f"amqp://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.virtual_host}")


class BaseConfig:
    """
    Base configuration class with common settings.
    
    This class provides default configuration values and utility methods
    that are inherited by environment-specific configuration classes.
    It implements the Template Method pattern for configuration setup.
    """
    
    # Flask Settings with type annotations
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = False
    TESTING: bool = False
    
    # Database Settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT Settings with cognitive security considerations
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '3600'))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))  # 30 days
    JWT_ALGORITHM: str = 'HS256'
    
    # Pagination Settings - cognitive defaults for user experience
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # API Versioning Configuration
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    
    # Security Settings
    BCRYPT_LOG_ROUNDS: int = 12  # Cognitive balance between security and performance
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT_LOGIN: str = "5 per minute"
    RATE_LIMIT_GENERAL: str = "100 per minute"
    
    # Email Settings for notifications
    MAIL_SERVER: str = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT: int = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS: bool = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME: str = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD: str = os.environ.get('MAIL_PASSWORD', '')
    
    # Logging Configuration
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Service Configuration
    SERVICE_NAME: str = "user-management-service"
    SERVICE_VERSION: str = "1.0.0"
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """
        Retrieve database configuration from environment variables.
        
        This method implements the Factory pattern to create database
        configuration objects with proper validation and error handling.
        
        Returns:
            DatabaseConfig: Configured database connection parameters
            
        Raises:
            ValueError: If required database environment variables are missing
            
        Example:
            >>> config = DevelopmentConfig()
            >>> db_config = config.get_database_config()
            >>> print(db_config.host)  # "localhost"
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
            database=os.environ['DB_NAME'],
            pool_size=int(os.environ.get('DB_POOL_SIZE', '10')),
            max_overflow=int(os.environ.get('DB_MAX_OVERFLOW', '20')),
            pool_timeout=int(os.environ.get('DB_POOL_TIMEOUT', '30'))
        )
    
    @classmethod
    def get_rabbitmq_config(cls) -> RabbitMQConfig:
        """
        Retrieve RabbitMQ configuration from environment variables.
        
        Returns:
            RabbitMQConfig: Configured RabbitMQ connection parameters
            
        Raises:
            ValueError: If required RabbitMQ environment variables are missing
        """
        required_vars = ['RABBITMQ_HOST', 'RABBITMQ_USER', 'RABBITMQ_PASS']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required RabbitMQ environment variables: {missing_vars}")
        
        return RabbitMQConfig(
            host=os.environ['RABBITMQ_HOST'],
            port=int(os.environ.get('RABBITMQ_PORT', '5672')),
            username=os.environ['RABBITMQ_USER'],
            password=os.environ['RABBITMQ_PASS'],
            virtual_host=os.environ.get('RABBITMQ_VHOST', '/'),
            exchange_name=os.environ.get('RABBITMQ_EXCHANGE', 'events')
        )
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate configuration settings for completeness and correctness.
        
        This method implements cognitive validation patterns to ensure
        the configuration is safe and complete for the target environment.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration validation fails
            
        Example:
            >>> config = ProductionConfig()
            >>> is_valid = config.validate_config()
            >>> print(is_valid)  # True or raises ValueError
        """
        # Validate secret key for non-development environments
        if not cls.DEBUG and cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set for non-development environments")
        
        # Validate JWT token expiry times (cognitive security check)
        if cls.JWT_ACCESS_TOKEN_EXPIRES <= 0:
            raise ValueError("JWT_ACCESS_TOKEN_EXPIRES must be positive")
        
        if cls.JWT_ACCESS_TOKEN_EXPIRES > 86400:  # 24 hours
            raise ValueError("JWT_ACCESS_TOKEN_EXPIRES should not exceed 24 hours for security")
        
        # Validate password complexity requirements
        if cls.PASSWORD_MIN_LENGTH < 8:
            raise ValueError("PASSWORD_MIN_LENGTH should be at least 8 characters")
        
        # Validate bcrypt rounds (cognitive performance vs security balance)
        if cls.BCRYPT_LOG_ROUNDS < 10 or cls.BCRYPT_LOG_ROUNDS > 15:
            raise ValueError("BCRYPT_LOG_ROUNDS should be between 10 and 15")
        
        # Validate database and RabbitMQ configurations
        try:
            cls.get_database_config()
            cls.get_rabbitmq_config()
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")
        
        return True


class DevelopmentConfig(BaseConfig):
    """
    Development environment configuration.
    
    This configuration enables debug mode, verbose logging, and uses
    local database connections suitable for development work.
    It implements cognitive defaults that enhance developer productivity.
    """
    
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True  # Enable SQL query logging
    LOG_LEVEL: str = 'DEBUG'
    
    # Relaxed security for development
    BCRYPT_LOG_ROUNDS: int = 4  # Faster hashing for development
    JWT_ACCESS_TOKEN_EXPIRES: int = 86400  # 24 hours for convenience
    
    # Development-specific rate limiting (more permissive)
    RATE_LIMIT_LOGIN: str = "10 per minute"
    RATE_LIMIT_GENERAL: str = "1000 per minute"
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """
        Get development database configuration with sensible defaults.
        
        This method provides cognitive defaults for local development,
        reducing configuration overhead for developers.
        
        Returns:
            DatabaseConfig: Development database configuration
        """
        return DatabaseConfig(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=int(os.environ.get('DB_PORT', '5432')),
            username=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'postgres'),
            database=os.environ.get('DB_NAME', 'user_management_dev'),
            pool_size=5,  # Smaller pool for development
            max_overflow=10,
            pool_timeout=20
        )
    
    @classmethod
    def get_rabbitmq_config(cls) -> RabbitMQConfig:
        """Get development RabbitMQ configuration with defaults."""
        return RabbitMQConfig(
            host=os.environ.get('RABBITMQ_HOST', 'localhost'),
            port=int(os.environ.get('RABBITMQ_PORT', '5672')),
            username=os.environ.get('RABBITMQ_USER', 'guest'),
            password=os.environ.get('RABBITMQ_PASS', 'guest'),
            virtual_host=os.environ.get('RABBITMQ_VHOST', '/'),
            exchange_name=os.environ.get('RABBITMQ_EXCHANGE', 'events')
        )


class TestingConfig(BaseConfig):
    """
    Testing environment configuration.
    
    This configuration is optimized for running unit and integration tests
    with in-memory databases and disabled external dependencies where possible.
    It implements cognitive testing patterns for reliable test execution.
    """
    
    TESTING: bool = True
    DEBUG: bool = True
    
    # Use SQLite for faster testing
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED: bool = False
    
    # Faster hashing for tests
    BCRYPT_LOG_ROUNDS: int = 4
    
    # Shorter token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES: int = 300  # 5 minutes
    
    # Disable rate limiting for tests
    RATE_LIMIT_LOGIN: str = "1000 per minute"
    RATE_LIMIT_GENERAL: str = "10000 per minute"
    
    # Disable email sending in tests
    MAIL_SUPPRESS_SEND: bool = True
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """
        Get testing database configuration.
        
        For testing, we prefer SQLite in-memory database for speed,
        but provide PostgreSQL option for integration tests.
        
        Returns:
            DatabaseConfig: Testing database configuration
        """
        if os.environ.get('USE_POSTGRES_FOR_TESTS'):
            return DatabaseConfig(
                host=os.environ.get('TEST_DB_HOST', 'localhost'),
                port=int(os.environ.get('TEST_DB_PORT', '5432')),
                username=os.environ.get('TEST_DB_USER', 'postgres'),
                password=os.environ.get('TEST_DB_PASSWORD', 'postgres'),
                database=os.environ.get('TEST_DB_NAME', 'user_management_test'),
                pool_size=2,  # Minimal pool for testing
                max_overflow=5,
                pool_timeout=10
            )
        else:
            # Return dummy config for SQLite
            return DatabaseConfig(
                host='memory',
                port=0,
                username='',
                password='',
                database=':memory:'
            )


class ProductionConfig(BaseConfig):
    """
    Production environment configuration.
    
    This configuration provides security-focused settings, optimized
    performance parameters, and production-ready database connections.
    It implements cognitive security patterns and performance optimizations.
    """
    
    DEBUG: bool = False
    
    # Enhanced security settings
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # Production logging (less verbose)
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'WARNING')
    
    # Strict security settings
    BCRYPT_LOG_ROUNDS: int = 12
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600  # 1 hour
    
    # Production rate limiting (more restrictive)
    RATE_LIMIT_LOGIN: str = "3 per minute"
    RATE_LIMIT_GENERAL: str = "60 per minute"
    
    # Force HTTPS in production
    PREFERRED_URL_SCHEME: str = 'https'
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Enhanced validation for production environment.
        
        This method implements additional cognitive security checks
        specific to production deployments.
        
        Returns:
            bool: True if configuration is valid for production
            
        Raises:
            ValueError: If production-specific validation fails
        """
        # Call base validation first
        super().validate_config()
        
        # Additional production-specific validations
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
        
        if not os.environ.get('JWT_SECRET_KEY'):
            raise ValueError("JWT_SECRET_KEY environment variable must be set in production")
        
        # Ensure strong secret keys in production
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        
        return True


# Configuration mapping for easy environment switching
CONFIG_MAPPING: Dict[str, type] = {
    Environment.DEVELOPMENT.value: DevelopmentConfig,
    Environment.TESTING.value: TestingConfig,
    Environment.PRODUCTION.value: ProductionConfig
}


def get_config(environment: Optional[str] = None) -> BaseConfig:
    """
    Factory function to get configuration based on environment.
    
    This function implements the Factory pattern with cognitive defaults
    to simplify configuration management across different environments.
    
    Args:
        environment: Target environment name. If None, uses FLASK_ENV environment variable.
        
    Returns:
        BaseConfig: Configuration instance for the specified environment
        
    Raises:
        ValueError: If the specified environment is not supported
        
    Example:
        >>> config = get_config('development')
        >>> print(config.DEBUG)  # True
        >>> 
        >>> # Using environment variable
        >>> os.environ['FLASK_ENV'] = 'production'
        >>> config = get_config()
        >>> print(config.DEBUG)  # False
    """
    if environment is None:
        environment = os.environ.get('FLASK_ENV', Environment.DEVELOPMENT.value)
    
    config_class = CONFIG_MAPPING.get(environment)
    if config_class is None:
        available_envs = list(CONFIG_MAPPING.keys())
        raise ValueError(f"Unsupported environment: {environment}. "
                        f"Available environments: {available_envs}")
    
    return config_class()


def setup_logging(config: BaseConfig) -> None:
    """
    Setup logging configuration based on the provided config.
    
    This function implements cognitive logging patterns that adapt
    to different environments and provide useful debugging information.
    
    Args:
        config: Configuration instance containing logging settings
        
    Example:
        >>> config = get_config('development')
        >>> setup_logging(config)
        >>> # Logging is now configured for development
    """
    import logging
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper()),
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),  # Console output
            # Add file handler in production if needed
        ]
    )
    
    # Configure specific loggers
    if config.DEBUG:
        # Enable SQLAlchemy logging in debug mode
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)
    else:
        # Suppress noisy loggers in production
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)