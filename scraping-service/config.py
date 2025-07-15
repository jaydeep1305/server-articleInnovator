"""
Configuration module for Scraping Service.

This module provides environment-specific configuration classes that handle
external data scraping service, database connections, event bus configuration,
and service-specific business logic configurations.

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
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    
    @property
    def url(self) -> str:
        """Generate SQLAlchemy database URL."""
        return (f"postgresql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}")


@dataclass
class EventBusConfig:
    """Event bus configuration for service events."""
    host: str
    port: int
    username: str
    password: str
    virtual_host: str = "/"
    exchange_name: str = "scraping_service_events"
    
    @property
    def url(self) -> str:
        """Generate RabbitMQ connection URL."""
        return (f"amqp://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.virtual_host}")


class BaseConfig:
    """Base configuration class for Scraping Service."""
    
    # Flask Settings
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-scraping-service-secret-key')
    DEBUG: bool = False
    TESTING: bool = False
    
    # Database Settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    JWT_ALGORITHM: str = 'HS256'
    
    # API Configuration
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    
    # Service Configuration
    SERVICE_NAME: str = "scraping-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 5010
    
    # Event Configuration
    EVENTS_ENABLED: bool = os.environ.get('EVENTS_ENABLED', 'true').lower() == 'true'
    EVENT_RETRY_ATTEMPTS: int = int(os.environ.get('EVENT_RETRY_ATTEMPTS', '3'))
    
    # Rate Limiting
    RATE_LIMIT_GENERAL: str = "100 per minute"
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """Retrieve database configuration from environment variables."""
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
    def get_event_bus_config(cls) -> EventBusConfig:
        """Retrieve event bus configuration from environment variables."""
        required_vars = ['RABBITMQ_HOST', 'RABBITMQ_USER', 'RABBITMQ_PASS']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required RabbitMQ environment variables: {missing_vars}")
        
        return EventBusConfig(
            host=os.environ['RABBITMQ_HOST'],
            port=int(os.environ.get('RABBITMQ_PORT', '5672')),
            username=os.environ['RABBITMQ_USER'],
            password=os.environ['RABBITMQ_PASS'],
            virtual_host=os.environ.get('RABBITMQ_VHOST', '/'),
            exchange_name=os.environ.get('RABBITMQ_EXCHANGE', 'scraping_service_events')
        )


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """Get development database configuration with defaults."""
        return DatabaseConfig(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=int(os.environ.get('DB_PORT', '5432')),
            username=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'postgres'),
            database=os.environ.get('DB_NAME', 'scraping_dev'),
            pool_size=5,
            max_overflow=10,
            pool_timeout=20
        )


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    TESTING: bool = True
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    
    # Disable events for testing
    EVENTS_ENABLED: bool = False
    
    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """Get testing database configuration."""
        return DatabaseConfig(
            host='memory',
            port=0,
            username='',
            password='',
            database=':memory:'
        )


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    DEBUG: bool = False
    
    # Enhanced security
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True


# Configuration mapping
CONFIG_MAPPING: Dict[str, type] = {
    Environment.DEVELOPMENT.value: DevelopmentConfig,
    Environment.TESTING.value: TestingConfig,
    Environment.PRODUCTION.value: ProductionConfig
}


def get_config(environment: Optional[str] = None) -> BaseConfig:
    """Factory function to get configuration based on environment."""
    if environment is None:
        environment = os.environ.get('FLASK_ENV', Environment.DEVELOPMENT.value)
    
    config_class = CONFIG_MAPPING.get(environment)
    if config_class is None:
        available_envs = list(CONFIG_MAPPING.keys())
        raise ValueError(f"Unsupported environment: {environment}. "
                        f"Available environments: {available_envs}")
    
    return config_class()


def setup_logging(config: BaseConfig) -> None:
    """Setup logging configuration for scraping-service."""
    import logging
    
    logging.basicConfig(
        level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
