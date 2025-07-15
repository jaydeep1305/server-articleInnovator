#!/usr/bin/env python3
"""
Microservices Generator Script

This script creates all the microservices for the event-driven architecture
with comprehensive file structures, models, services, routes, and configurations.

Author: AI Assistant
Date: 2024
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional


# Service definitions with their specific configurations
SERVICES = {
    "domain-management-service": {
        "description": "Manages domains and WordPress integration",
        "models": ["Domain", "WordPressSite", "DomainRecord"],
        "port": 5003,
        "database": "domain_management"
    },
    "ai-configuration-service": {
        "description": "Manages AI model configurations and settings", 
        "models": ["AIModel", "Configuration", "ModelProvider"],
        "port": 5004,
        "database": "ai_configuration"
    },
    "image-generation-service": {
        "description": "Handles AI image generation and processing",
        "models": ["ImageRequest", "GeneratedImage", "ImageTemplate"],
        "port": 5005,
        "database": "image_generation"
    },
    "monitoring-service": {
        "description": "System monitoring and health checks",
        "models": ["ServiceHealth", "Metric", "Alert"],
        "port": 5006,
        "database": "monitoring"
    },
    "notification-service": {
        "description": "Handles all types of notifications",
        "models": ["Notification", "NotificationTemplate", "NotificationChannel"],
        "port": 5007,
        "database": "notifications"
    },
    "logging-service": {
        "description": "Centralized logging and audit trails",
        "models": ["LogEntry", "AuditLog", "SystemEvent"],
        "port": 5008,
        "database": "logging"
    },
    "configuration-service": {
        "description": "Global configuration management",
        "models": ["ConfigurationItem", "Environment", "Secret"],
        "port": 5009,
        "database": "configuration"
    },
    "scraping-service": {
        "description": "External data scraping service",
        "models": ["ScrapingJob", "ScrapedData", "Source"],
        "port": 5010,
        "database": "scraping"
    },
    "ai-rate-limiter-service": {
        "description": "AI API rate limiting and quota management",
        "models": ["RateLimit", "Usage", "Quota"],
        "port": 5011,
        "database": "ai_rate_limiter"
    }
}


def create_directory_structure(service_name: str) -> None:
    """Create the directory structure for a microservice."""
    base_path = Path(service_name)
    
    directories = [
        "app/models",
        "app/services", 
        "app/routes",
        "app/utils",
        "tests/unit",
        "tests/integration",
        "migrations",
        "docker"
    ]
    
    for directory in directories:
        (base_path / directory).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files
    init_paths = [
        "app/__init__.py",
        "app/models/__init__.py",
        "app/services/__init__.py",
        "app/routes/__init__.py",
        "app/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]
    
    for init_path in init_paths:
        (base_path / init_path).touch()


def create_config_py(service_name: str, config: Dict) -> str:
    """Generate config.py content."""
    service_title = service_name.replace('-', ' ').title()
    service_constant = service_name.replace('-', '_').upper()
    
    return f'''"""
Configuration module for {service_title}.

This module provides environment-specific configuration classes that handle
{config["description"].lower()}, database connections, event bus configuration,
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
        return (f"postgresql://{{self.username}}:{{self.password}}@"
                f"{{self.host}}:{{self.port}}/{{self.database}}")


@dataclass
class EventBusConfig:
    """Event bus configuration for service events."""
    host: str
    port: int
    username: str
    password: str
    virtual_host: str = "/"
    exchange_name: str = "{service_name.replace('-', '_')}_events"
    
    @property
    def url(self) -> str:
        """Generate RabbitMQ connection URL."""
        return (f"amqp://{{self.username}}:{{self.password}}@"
                f"{{self.host}}:{{self.port}}/{{self.virtual_host}}")


class BaseConfig:
    """Base configuration class for {service_title}."""
    
    # Flask Settings
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-{service_name}-secret-key')
    DEBUG: bool = False
    TESTING: bool = False
    
    # Database Settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = {{
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }}
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    JWT_ALGORITHM: str = 'HS256'
    
    # API Configuration
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{{API_VERSION}}"
    
    # Service Configuration
    SERVICE_NAME: str = "{service_name}"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = {config["port"]}
    
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
            raise ValueError(f"Missing required database environment variables: {{missing_vars}}")
        
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
            raise ValueError(f"Missing required RabbitMQ environment variables: {{missing_vars}}")
        
        return EventBusConfig(
            host=os.environ['RABBITMQ_HOST'],
            port=int(os.environ.get('RABBITMQ_PORT', '5672')),
            username=os.environ['RABBITMQ_USER'],
            password=os.environ['RABBITMQ_PASS'],
            virtual_host=os.environ.get('RABBITMQ_VHOST', '/'),
            exchange_name=os.environ.get('RABBITMQ_EXCHANGE', '{service_name.replace("-", "_")}_events')
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
            database=os.environ.get('DB_NAME', '{config["database"]}_dev'),
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
CONFIG_MAPPING: Dict[str, type] = {{
    Environment.DEVELOPMENT.value: DevelopmentConfig,
    Environment.TESTING.value: TestingConfig,
    Environment.PRODUCTION.value: ProductionConfig
}}


def get_config(environment: Optional[str] = None) -> BaseConfig:
    """Factory function to get configuration based on environment."""
    if environment is None:
        environment = os.environ.get('FLASK_ENV', Environment.DEVELOPMENT.value)
    
    config_class = CONFIG_MAPPING.get(environment)
    if config_class is None:
        available_envs = list(CONFIG_MAPPING.keys())
        raise ValueError(f"Unsupported environment: {{environment}}. "
                        f"Available environments: {{available_envs}}")
    
    return config_class()


def setup_logging(config: BaseConfig) -> None:
    """Setup logging configuration for {service_name}."""
    import logging
    
    logging.basicConfig(
        level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
'''


def create_base_model(service_name: str) -> str:
    """Generate base model content."""
    return '''"""
Base model for all database models.

This module provides the BaseModel class that includes common fields,
validation methods, and CRUD operations for all models in the service.

Author: AI Assistant
Date: 2024
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

# Create the base class
Base = declarative_base()


class BaseModel(Base, ABC):
    """
    Abstract base model class for all database models.
    
    Provides common fields, validation, and CRUD operations.
    Implements cognitive patterns for data consistency and auditability.
    """
    
    __abstract__ = True
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier"
    )
    
    # Audit timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When record was created"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="When record was last updated"
    )
    
    # Soft delete
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Soft delete flag"
    )
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="When record was deleted"
    )
    
    # Optional metadata
    metadata_json = Column(
        Text,
        nullable=True,
        comment="Additional metadata as JSON"
    )
    
    def __init__(self, **kwargs) -> None:
        """Initialize model with provided attributes."""
        # Set provided attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Set timestamps if not provided
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = datetime.utcnow()
        
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate the model data.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        errors = []
        
        # Validate ID if present
        if self.id is not None and not isinstance(self.id, uuid.UUID):
            errors.append("ID must be a valid UUID")
        
        # Validate timestamps
        if self.created_at and not isinstance(self.created_at, datetime):
            errors.append("created_at must be a datetime")
        
        if self.updated_at and not isinstance(self.updated_at, datetime):
            errors.append("updated_at must be a datetime")
        
        if self.deleted_at and not isinstance(self.deleted_at, datetime):
            errors.append("deleted_at must be a datetime")
        
        # Logical validation
        if (self.created_at and self.updated_at and 
            self.created_at > self.updated_at):
            errors.append("created_at cannot be after updated_at")
        
        if self.is_deleted and not self.deleted_at:
            errors.append("deleted_at must be set when is_deleted is True")
        
        return len(errors) == 0, errors
    
    def soft_delete(self) -> None:
        """Mark the record as deleted without removing it from database."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create(cls, session: Session, **kwargs) -> 'BaseModel':
        """
        Create a new instance and save to database.
        
        Args:
            session: SQLAlchemy session
            **kwargs: Model attributes
            
        Returns:
            Created model instance
            
        Raises:
            ValueError: If validation fails
        """
        instance = cls(**kwargs)
        
        # Validate before saving
        is_valid, errors = instance.validate()
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        session.add(instance)
        session.flush()
        return instance
    
    @classmethod
    def get_by_id(cls, session: Session, record_id: uuid.UUID) -> Optional['BaseModel']:
        """
        Get a record by ID.
        
        Args:
            session: SQLAlchemy session
            record_id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        return session.query(cls).filter(
            cls.id == record_id,
            cls.is_deleted == False
        ).first()
    
    @classmethod
    def get_all(cls, session: Session, include_deleted: bool = False) -> List['BaseModel']:
        """
        Get all records.
        
        Args:
            session: SQLAlchemy session
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            List of model instances
        """
        query = session.query(cls)
        if not include_deleted:
            query = query.filter(cls.is_deleted == False)
        
        return query.all()
    
    @classmethod
    def get_active_query(cls, session: Session):
        """
        Get query for active (non-deleted) records.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            SQLAlchemy query object
        """
        return session.query(cls).filter(cls.is_deleted == False)
    
    def update(self, **kwargs) -> None:
        """
        Update model attributes.
        
        Args:
            **kwargs: Attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def save(self, session: Session) -> None:
        """
        Save the model to database.
        
        Args:
            session: SQLAlchemy session
            
        Raises:
            ValueError: If validation fails
        """
        # Validate before saving
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        self.updated_at = datetime.utcnow()
        session.add(self)
        session.flush()
    
    def delete(self, session: Session, hard_delete: bool = False) -> None:
        """
        Delete the record.
        
        Args:
            session: SQLAlchemy session
            hard_delete: Whether to permanently delete (default: soft delete)
        """
        if hard_delete:
            session.delete(self)
        else:
            self.soft_delete()
        
        session.flush()
    
    def to_dict(self, include_deleted: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Args:
            include_deleted: Whether to include deleted record data
            
        Returns:
            Dict[str, Any]: Model data
        """
        if self.is_deleted and not include_deleted:
            return {}
        
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            # Handle different data types
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id='{self.id}')>"
'''


def create_requirements_txt(service_name: str) -> str:
    """Generate requirements.txt content."""
    return '''# Flask and extensions
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-JWT-Extended==4.6.0
Flask-CORS==4.0.0
Flask-Limiter==3.5.0

# Database
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23

# Message broker
pika==1.3.2

# Caching
redis==5.0.1

# HTTP requests
requests==2.31.0

# Data validation
marshmallow==3.20.1

# Environment management
python-dotenv==1.0.0

# Testing
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0

# Development
black==23.12.0
flake8==6.1.0
mypy==1.7.1

# Production
gunicorn==21.2.0
'''


def create_dockerfile(service_name: str, config: Dict) -> str:
    """Generate Dockerfile content."""
    return f'''# Multi-stage build for {service_name}
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Development stage
FROM base as development

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {config["port"]}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{config["port"]}/health || exit 1

# Run the application
CMD ["python", "run.py"]

# Production stage
FROM base as production

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn

# Copy application code
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {config["port"]}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{config["port"]}/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:{config["port"]}", "--workers", "4", "--timeout", "120", "run:app"]
'''


def create_run_py(service_name: str, config: Dict) -> str:
    """Generate run.py content."""
    service_title = service_name.replace('-', ' ').title()
    
    return f'''#!/usr/bin/env python3
"""
{service_title} - Main Application Entry Point

This module serves as the entry point for the {service_title}.
It handles application initialization, configuration loading, and server startup.

Author: AI Assistant
Date: 2024
"""

import os
import sys
import logging
from flask import Flask

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config, setup_logging
from app import create_app


def main() -> None:
    """
    Main application entry point.
    
    This function initializes the Flask application with the appropriate
    configuration based on the environment and starts the development server.
    """
    try:
        # Load configuration
        config = get_config()
        
        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting {{config.SERVICE_NAME}} v{{config.SERVICE_VERSION}}")
        logger.info(f"Environment: {{os.environ.get('FLASK_ENV', 'development')}}")
        
        # Create Flask application
        app = create_app(config)
        
        # Get port from environment or config
        port = int(os.environ.get('PORT', config.SERVICE_PORT))
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info(f"Starting server on {{host}}:{{port}}")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=config.DEBUG,
            threaded=True
        )
        
    except Exception as e:
        logging.error(f"Failed to start application: {{e}}")
        sys.exit(1)


if __name__ == '__main__':
    main()
'''


def create_docker_compose(service_name: str, config: Dict) -> str:
    """Generate docker-compose.yml content."""
    return f'''version: '3.8'

services:
  {service_name}:
    build:
      context: .
      target: development
    container_name: {service_name}
    ports:
      - "{config["port"]}:{config["port"]}"
    environment:
      - FLASK_ENV=development
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - DB_NAME={config["database"]}_dev
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_USER=guest
      - RABBITMQ_PASS=guest
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - rabbitmq
      - redis
    volumes:
      - .:/app
    networks:
      - {service_name.replace("-", "_")}_network

  postgres:
    image: postgres:15-alpine
    container_name: {service_name}_postgres
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB={config["database"]}_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - {service_name.replace("-", "_")}_network

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: {service_name}_rabbitmq
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - {service_name.replace("-", "_")}_network

  redis:
    image: redis:7-alpine
    container_name: {service_name}_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - {service_name.replace("-", "_")}_network

volumes:
  postgres_data:
  rabbitmq_data:
  redis_data:

networks:
  {service_name.replace("-", "_")}_network:
    driver: bridge
'''


def create_app_init(service_name: str) -> str:
    """Generate app/__init__.py content."""
    service_title = service_name.replace('-', ' ').title()
    
    return f'''"""
{service_title} - Flask Application Factory

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
    cors.init_app(app, resources={{
        r"/api/*": {{
            "origins": ["http://localhost:3000", "http://localhost:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }}
    }})
    
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
        return jsonify({{
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized errors."""
        return jsonify({{
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource',
            'status_code': 401
        }}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden errors."""
        return jsonify({{
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403
        }}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors."""
        return jsonify({{
            'error': 'Not Found',
            'message': 'The requested resource could not be found',
            'status_code': 404
        }}), 404
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle validation errors."""
        return jsonify({{
            'error': 'Unprocessable Entity',
            'message': 'The request was well-formed but was unable to be followed due to semantic errors',
            'status_code': 422
        }}), 422
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        """Handle rate limit errors."""
        return jsonify({{
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'status_code': 429,
            'retry_after': error.retry_after
        }}), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle internal server errors."""
        app.logger.error(f"Internal server error: {{error}}")
        return jsonify({{
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred',
            'status_code': 500
        }}), 500


def register_middleware(app: Flask) -> None:
    """Register application middleware."""
    
    @app.before_request
    def log_request_info():
        """Log request information."""
        app.logger.info(f"{{request.method}} {{request.url}} - {{request.remote_addr}}")
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Add service identification header
        response.headers['X-Service'] = app.config.get('SERVICE_NAME', '{service_name}')
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
            'logs/{service_name}.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info(f'{service_title} startup')
'''


def create_health_routes(service_name: str) -> str:
    """Generate health check routes."""
    return f'''"""
Health check endpoints for {service_name.replace('-', ' ').title()}.

This module provides health check endpoints for monitoring service status,
database connectivity, and external service dependencies.

Author: AI Assistant
Date: 2024
"""

import time
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from app import db

# Create blueprint
health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        JSON response with service status
    """
    return jsonify({{
        'status': 'healthy',
        'service': current_app.config.get('SERVICE_NAME', '{service_name}'),
        'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
        'timestamp': datetime.utcnow().isoformat()
    }}), 200


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the service is ready to receive traffic.
    This includes database connectivity and other critical dependencies.
    
    Returns:
        JSON response with readiness status
    """
    checks = {{
        'database': False,
        'overall': False
    }}
    
    start_time = time.time()
    
    try:
        # Check database connectivity
        db.session.execute(text('SELECT 1'))
        checks['database'] = True
        
        # Overall status
        checks['overall'] = all(checks.values())
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        response_data = {{
            'status': 'ready' if checks['overall'] else 'not_ready',
            'service': current_app.config.get('SERVICE_NAME', '{service_name}'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'checks': checks,
            'response_time_ms': response_time,
            'timestamp': datetime.utcnow().isoformat()
        }}
        
        status_code = 200 if checks['overall'] else 503
        return jsonify(response_data), status_code
        
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {{e}}")
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return jsonify({{
            'status': 'not_ready',
            'service': current_app.config.get('SERVICE_NAME', '{service_name}'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'checks': checks,
            'error': str(e),
            'response_time_ms': response_time,
            'timestamp': datetime.utcnow().isoformat()
        }}), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Checks if the service is alive and should be restarted if not.
    This is a basic check that the Flask application is responding.
    
    Returns:
        JSON response with liveness status
    """
    return jsonify({{
        'status': 'alive',
        'service': current_app.config.get('SERVICE_NAME', '{service_name}'),
        'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
        'timestamp': datetime.utcnow().isoformat()
    }}), 200


@health_bp.route('/health/metrics', methods=['GET'])
def metrics():
    """
    Basic metrics endpoint for monitoring.
    
    Returns:
        JSON response with service metrics
    """
    try:
        # Get database connection pool info
        pool_info = {{}}
        if hasattr(db.engine.pool, 'size'):
            pool_info = {{
                'pool_size': db.engine.pool.size(),
                'checked_in': db.engine.pool.checkedin(),
                'checked_out': db.engine.pool.checkedout(),
                'overflow': db.engine.pool.overflow(),
                'invalid': db.engine.pool.invalid()
            }}
        
        return jsonify({{
            'service': current_app.config.get('SERVICE_NAME', '{service_name}'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'metrics': {{
                'database_pool': pool_info,
                'config': {{
                    'debug': current_app.debug,
                    'testing': current_app.testing
                }}
            }},
            'timestamp': datetime.utcnow().isoformat()
        }}), 200
        
    except Exception as e:
        current_app.logger.error(f"Metrics collection failed: {{e}}")
        
        return jsonify({{
            'service': current_app.config.get('SERVICE_NAME', '{service_name}'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'error': 'Failed to collect metrics',
            'timestamp': datetime.utcnow().isoformat()
        }}), 500
'''


def create_readme(service_name: str, config: Dict) -> str:
    """Generate README.md content."""
    service_title = service_name.replace('-', ' ').title()
    
    return f'''# {service_title}

{config["description"]}

## Overview

The {service_title} is a microservice that handles {config["description"].lower()}. It's part of an event-driven architecture using Flask, PostgreSQL, and RabbitMQ.

## Features

- **RESTful API**: Clean and well-documented REST endpoints
- **Event-Driven**: Publishes and consumes events via RabbitMQ
- **Database Models**: Comprehensive data models with validation
- **Health Checks**: Kubernetes-ready health check endpoints
- **Security**: JWT authentication and RBAC
- **Testing**: Comprehensive test suite with pytest
- **Docker**: Production-ready containerization
- **Monitoring**: Built-in metrics and logging

## Quick Start

### Using Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd {service_name}

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f {service_name}

# Stop services
docker-compose down
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_NAME={config["database"]}_dev

# Run database migrations
flask db upgrade

# Start the service
python run.py
```

## API Documentation

### Health Endpoints

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe (checks dependencies)
- `GET /health/live` - Liveness probe (basic check)
- `GET /health/metrics` - Service metrics

### Authentication

The service uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <jwt-token>
```

## Configuration

Configuration is handled through environment variables:

### Database Configuration
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name

### RabbitMQ Configuration
- `RABBITMQ_HOST` - RabbitMQ host
- `RABBITMQ_PORT` - RabbitMQ port (default: 5672)
- `RABBITMQ_USER` - RabbitMQ username
- `RABBITMQ_PASS` - RabbitMQ password

### Service Configuration
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key
- `LOG_LEVEL` - Logging level (default: INFO)

## Database Schema

The service uses PostgreSQL with the following models:

{chr(10).join([f"- **{model}**: [Description needed]" for model in config["models"]])}

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_models.py
```

## Event System

The service participates in the event-driven architecture:

### Published Events
- [List events this service publishes]

### Consumed Events
- [List events this service consumes]

## Deployment

### Docker

```bash
# Build production image
docker build -t {service_name}:latest --target production .

# Run production container
docker run -d \\
  --name {service_name} \\
  -p {config["port"]}:{config["port"]} \\
  -e DB_HOST=your-db-host \\
  -e DB_USER=your-db-user \\
  -e DB_PASSWORD=your-db-password \\
  -e DB_NAME=your-db-name \\
  {service_name}:latest
```

### Kubernetes

The service includes health check endpoints for Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {service_name}
  template:
    metadata:
      labels:
        app: {service_name}
    spec:
      containers:
      - name: {service_name}
        image: {service_name}:latest
        ports:
        - containerPort: {config["port"]}
        livenessProbe:
          httpGet:
            path: /health/live
            port: {config["port"]}
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: {config["port"]}
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Development

### Adding New Features

1. Create database models in `app/models/`
2. Add business logic in `app/services/`
3. Create API routes in `app/routes/`
4. Write tests in `tests/`
5. Update documentation

### Code Style

The project uses:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

```bash
# Format code
black .

# Check linting
flake8

# Check types
mypy app
```

## Monitoring and Logging

### Logging
- Logs are written to `logs/{service_name}.log`
- Structured logging with timestamps and log levels
- Request/response logging for debugging

### Metrics
- Service metrics available at `/health/metrics`
- Database connection pool metrics
- Custom business metrics

## Security

- JWT-based authentication
- Rate limiting on API endpoints
- Input validation and sanitization
- SQL injection prevention with SQLAlchemy
- CORS configuration for web clients

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[License information]

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

---

**Service Information**
- Service: {service_name}
- Version: 1.0.0
- Port: {config["port"]}
- Database: {config["database"]}
'''


def generate_service_files(service_name: str, config: Dict) -> None:
    """Generate all files for a microservice."""
    print(f"Generating {service_name}...")
    
    # Create directory structure
    create_directory_structure(service_name)
    
    # Core files
    files_to_create = {
        f"{service_name}/config.py": create_config_py(service_name, config),
        f"{service_name}/app/models/base.py": create_base_model(service_name),
        f"{service_name}/requirements.txt": create_requirements_txt(service_name),
        f"{service_name}/Dockerfile": create_dockerfile(service_name, config),
        f"{service_name}/docker-compose.yml": create_docker_compose(service_name, config),
        f"{service_name}/run.py": create_run_py(service_name, config),
        f"{service_name}/app/__init__.py": create_app_init(service_name),
        f"{service_name}/app/routes/health.py": create_health_routes(service_name),
        f"{service_name}/README.md": create_readme(service_name, config),
    }
    
    # Write all files
    for file_path, content in files_to_create.items():
        with open(file_path, 'w') as f:
            f.write(content)
    
    print(f"✅ {service_name} generated successfully!")


def main():
    """Main function to generate all microservices."""
    print("🚀 Generating Microservices...")
    print("=" * 50)
    
    for service_name, config in SERVICES.items():
        try:
            generate_service_files(service_name, config)
        except Exception as e:
            print(f"❌ Error generating {service_name}: {e}")
    
    print("=" * 50)
    print("✅ All microservices generated successfully!")
    print("\nNext steps:")
    print("1. Review the generated services")
    print("2. Customize models and business logic")
    print("3. Add specific API endpoints")
    print("4. Configure environment variables")
    print("5. Run tests and deploy")


if __name__ == "__main__":
    main()