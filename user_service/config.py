"""
Configuration module for the User Management Microservice.

This module provides configuration classes for different environments
(development, testing, production) with proper type hints and validation.
"""

import os
from typing import Type, Dict, Any
from dataclasses import dataclass


@dataclass
class BaseConfig:
    """
    Base configuration class containing common settings.
    
    This class serves as the foundation for environment-specific configurations
    and includes security, database, and application settings.
    """
    
    # Application Settings
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = False
    TESTING: bool = False
    
    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = None
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600  # 1 hour in seconds
    
    # Redis Configuration for caching and sessions
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # API Configuration
    API_VERSION: str = 'v1'
    API_PREFIX: str = f'/api/{API_VERSION}'
    
    # Email Configuration
    MAIL_SERVER: str = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT: int = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS: bool = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME: str = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD: str = os.environ.get('MAIL_PASSWORD', '')
    
    def __post_init__(self) -> None:
        """Post-initialization hook for additional configuration setup."""
        if self.SQLALCHEMY_ENGINE_OPTIONS is None:
            self.SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_pre_ping': True,
                'pool_recycle': 300,
            }


@dataclass
class DevelopmentConfig(BaseConfig):
    """
    Development environment configuration.
    
    Optimized for local development with debug mode enabled
    and verbose logging.
    """
    
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DEV_DATABASE_URL',
        'postgresql://user:password@localhost:5432/user_service_dev'
    )
    
    # Development-specific logging
    LOG_LEVEL: str = 'DEBUG'


@dataclass
class TestingConfig(BaseConfig):
    """
    Testing environment configuration.
    
    Uses in-memory database and disables unnecessary features
    for faster test execution.
    """
    
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'TEST_DATABASE_URL',
        'postgresql://user:password@localhost:5432/user_service_test'
    )
    
    # Testing-specific settings
    WTF_CSRF_ENABLED: bool = False
    LOG_LEVEL: str = 'WARNING'


@dataclass
class ProductionConfig(BaseConfig):
    """
    Production environment configuration.
    
    Optimized for performance and security with proper error handling
    and monitoring capabilities.
    """
    
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/user_service_prod'
    )
    
    # Production-specific logging and monitoring
    LOG_LEVEL: str = 'INFO'
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Production-specific post-initialization."""
        super().__post_init__()
        self.SQLALCHEMY_ENGINE_OPTIONS.update({
            'pool_size': 20,
            'max_overflow': 30,
            'pool_timeout': 20,
        })


# Configuration mapping for easy environment switching
config_mapping: Dict[str, Type[BaseConfig]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(environment: str = None) -> BaseConfig:
    """
    Factory function to get configuration based on environment.
    
    Args:
        environment: The target environment ('development', 'testing', 'production')
                    If None, uses FLASK_ENV environment variable or defaults to 'development'
    
    Returns:
        Configured instance of the appropriate configuration class
        
    Raises:
        ValueError: If an invalid environment is specified
    """
    if environment is None:
        environment = os.environ.get('FLASK_ENV', 'development')
    
    if environment not in config_mapping:
        raise ValueError(f"Invalid environment: {environment}. "
                        f"Must be one of: {list(config_mapping.keys())}")
    
    config_class = config_mapping[environment]
    return config_class()