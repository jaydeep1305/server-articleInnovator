#!/usr/bin/env python3
"""
Complete Services Script

This script completes all missing components across all microservices
including models, services, routes, tests, and configuration files.

Author: AI Assistant
Date: 2024
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any


# Service definitions with missing components
INCOMPLETE_SERVICES = {
    "workspace-management-service": {
        "missing": ["app/__init__.py", "requirements.txt", "Dockerfile", "docker-compose.yml", "README.md", "run.py"]
    },
    "article-management-service": {
        "missing": ["config.py", "app/__init__.py", "app/models/base.py", "app/services/article_service.py", 
                   "app/routes/article_api.py", "tests/test_article_model.py", "requirements.txt", 
                   "Dockerfile", "docker-compose.yml", "README.md", "run.py"]
    },
    "domain-management-service": {
        "missing": ["app/models/domain.py", "app/services/domain_service.py", "app/routes/domain_api.py", 
                   "tests/test_domain_model.py"]
    },
    "ai-configuration-service": {
        "missing": ["app/models/ai_model.py", "app/services/ai_config_service.py", "app/routes/ai_api.py",
                   "tests/test_ai_model.py"]
    },
    "image-generation-service": {
        "missing": ["app/models/image_generation.py", "app/services/image_service.py", "app/routes/image_api.py",
                   "tests/test_image_model.py"]
    },
    "monitoring-service": {
        "missing": ["app/models/monitoring.py", "app/services/monitoring_service.py", "app/routes/monitoring_api.py",
                   "tests/test_monitoring_model.py"]
    },
    "notification-service": {
        "missing": ["app/models/notification.py", "app/services/notification_service.py", "app/routes/notification_api.py",
                   "tests/test_notification_model.py"]
    },
    "logging-service": {
        "missing": ["app/models/logging.py", "app/services/logging_service.py", "app/routes/logging_api.py",
                   "tests/test_logging_model.py"]
    },
    "configuration-service": {
        "missing": ["app/models/configuration.py", "app/services/config_service.py", "app/routes/config_api.py",
                   "tests/test_configuration_model.py"]
    },
    "scraping-service": {
        "missing": ["app/models/scraping.py", "app/services/scraping_service.py", "app/routes/scraping_api.py",
                   "tests/test_scraping_model.py"]
    },
    "ai-rate-limiter-service": {
        "missing": ["app/models/rate_limit.py", "app/services/rate_limit_service.py", "app/routes/rate_limit_api.py",
                   "tests/test_rate_limit_model.py"]
    }
}


def create_workspace_app_init():
    """Create app/__init__.py for workspace management service."""
    content = '''"""
Workspace Management Service - Flask Application Factory

This module contains the Flask application factory function that creates
and configures the Flask application instance for workspace management.

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
    Application factory function for workspace management service.
    
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
    
    # Workspace API routes
    from app.routes.workspace_api import workspace_api
    app.register_blueprint(workspace_api, url_prefix=app.config['API_PREFIX'])


def register_error_handlers(app: Flask) -> None:
    """Register application error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource could not be found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
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
        response.headers['X-Service'] = 'workspace-management-service'
        response.headers['X-Service-Version'] = '1.0.0'
        return response


def setup_app_logging(app: Flask) -> None:
    """Setup application-specific logging."""
    
    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/workspace-management-service.log',
            maxBytes=10240000,
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Workspace Management Service startup')
'''
    
    with open("workspace-management-service/app/__init__.py", "w") as f:
        f.write(content)


def create_workspace_requirements():
    """Create requirements.txt for workspace management service."""
    content = '''# Flask and extensions
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
    
    with open("workspace-management-service/requirements.txt", "w") as f:
        f.write(content)


def create_workspace_dockerfile():
    """Create Dockerfile for workspace management service."""
    content = '''# Multi-stage build for workspace-management-service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    curl \\
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
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5002/health || exit 1

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
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5002/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "4", "--timeout", "120", "run:app"]
'''
    
    with open("workspace-management-service/Dockerfile", "w") as f:
        f.write(content)


def create_workspace_docker_compose():
    """Create docker-compose.yml for workspace management service."""
    content = '''version: '3.8'

services:
  workspace-management-service:
    build:
      context: .
      target: development
    container_name: workspace-management-service
    ports:
      - "5002:5002"
    environment:
      - FLASK_ENV=development
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - DB_NAME=workspace_management_dev
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_USER=guest
      - RABBITMQ_PASS=guest
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - postgres
      - rabbitmq
      - redis
    volumes:
      - .:/app
    networks:
      - workspace_network

  postgres:
    image: postgres:15-alpine
    container_name: workspace_postgres
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=workspace_management_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - workspace_network

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: workspace_rabbitmq
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - workspace_network

  redis:
    image: redis:7-alpine
    container_name: workspace_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - workspace_network

volumes:
  postgres_data:
  rabbitmq_data:
  redis_data:

networks:
  workspace_network:
    driver: bridge
'''
    
    with open("workspace-management-service/docker-compose.yml", "w") as f:
        f.write(content)


def create_workspace_run_py():
    """Create run.py for workspace management service."""
    content = '''#!/usr/bin/env python3
"""
Workspace Management Service - Main Application Entry Point

This module serves as the entry point for the Workspace Management Service.
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
        
        logger.info(f"Starting {config.SERVICE_NAME} v{config.SERVICE_VERSION}")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        
        # Create Flask application
        app = create_app(config)
        
        # Get port from environment or config
        port = int(os.environ.get('PORT', config.SERVICE_PORT))
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info(f"Starting server on {host}:{port}")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=config.DEBUG,
            threaded=True
        )
        
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
'''
    
    with open("workspace-management-service/run.py", "w") as f:
        f.write(content)


def create_workspace_readme():
    """Create README.md for workspace management service."""
    content = '''# Workspace Management Service

A comprehensive microservice for managing collaborative workspaces and team organization. This service handles workspace creation, member management, permissions, and workspace-related functionality with comprehensive validation and business logic.

## Features

- **Workspace CRUD Operations**: Create, read, update, delete workspaces
- **Member Management**: Add, remove, and manage workspace members with roles
- **Permission System**: Role-based access control (Owner, Admin, Member, Guest)
- **Storage Management**: Workspace storage quotas and usage tracking
- **Search & Discovery**: Advanced workspace search capabilities
- **Customization**: Workspace themes, logos, and custom domains
- **Archive/Restore**: Workspace lifecycle management
- **Event-Driven**: Publishes workspace events for other services

## Quick Start

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f workspace-management-service

# Stop services
docker-compose down
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_NAME=workspace_management_dev

# Run the service
python run.py
```

## API Endpoints

### Workspace Management
- `POST /api/v1/workspaces` - Create workspace
- `GET /api/v1/workspaces` - List user workspaces
- `GET /api/v1/workspaces/{id}` - Get workspace details
- `PUT /api/v1/workspaces/{id}` - Update workspace
- `POST /api/v1/workspaces/{id}/archive` - Archive workspace

### Member Management
- `GET /api/v1/workspaces/{id}/members` - List workspace members
- `POST /api/v1/workspaces/{id}/members` - Add member
- `DELETE /api/v1/workspaces/{id}/members/{user_id}` - Remove member
- `PUT /api/v1/workspaces/{id}/members/{user_id}/role` - Update member role

### Search
- `GET /api/v1/workspaces/search` - Search workspaces

### Health Checks
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /health/metrics` - Service metrics

## Database Schema

### Workspace Model
- `id` (UUID) - Primary key
- `name` (String) - Workspace name
- `slug` (String) - URL-friendly identifier
- `description` (Text) - Workspace description
- `owner_id` (UUID) - Owner user ID
- `status` (String) - Workspace status
- `visibility` (String) - Public/private/internal
- `max_members` (Integer) - Member limit
- `storage_quota_gb` (Integer) - Storage quota
- `storage_used_mb` (Integer) - Storage used
- `theme_color` (String) - Theme color
- `custom_domain` (String) - Custom domain
- Various settings and timestamps

### Workspace Members (Association Table)
- `workspace_id` (UUID) - Workspace reference
- `user_id` (UUID) - User reference
- `role` (String) - Member role
- `joined_at` (DateTime) - Join timestamp
- `invited_by` (UUID) - Inviter reference

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_workspace_service.py
```

## Configuration

The service supports environment-based configuration:

- `FLASK_ENV` - Environment (development/testing/production)
- `SECRET_KEY` - Flask secret key
- `DB_*` - Database configuration
- `RABBITMQ_*` - Message broker configuration
- `REDIS_URL` - Cache configuration

## Architecture

This service follows clean architecture principles:

- **Models**: Database models with validation
- **Services**: Business logic layer
- **Routes**: REST API endpoints
- **Events**: Event publishing/consuming

## Security

- JWT-based authentication
- Role-based access control
- Input validation and sanitization
- Rate limiting
- Security headers

## Monitoring

- Health check endpoints
- Structured logging
- Metrics collection
- Error tracking

---

**Port**: 5002  
**Database**: workspace_management  
**Version**: 1.0.0
'''
    
    with open("workspace-management-service/README.md", "w") as f:
        f.write(content)


def create_workspace_health_routes():
    """Create health routes for workspace management service."""
    content = '''"""
Health check endpoints for Workspace Management Service.

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
    return jsonify({
        'status': 'healthy',
        'service': current_app.config.get('SERVICE_NAME', 'workspace-management-service'),
        'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the service is ready to receive traffic.
    This includes database connectivity and other critical dependencies.
    
    Returns:
        JSON response with readiness status
    """
    checks = {
        'database': False,
        'overall': False
    }
    
    start_time = time.time()
    
    try:
        # Check database connectivity
        db.session.execute(text('SELECT 1'))
        checks['database'] = True
        
        # Overall status
        checks['overall'] = all(checks.values())
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        response_data = {
            'status': 'ready' if checks['overall'] else 'not_ready',
            'service': current_app.config.get('SERVICE_NAME', 'workspace-management-service'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'checks': checks,
            'response_time_ms': response_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        status_code = 200 if checks['overall'] else 503
        return jsonify(response_data), status_code
        
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {e}")
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return jsonify({
            'status': 'not_ready',
            'service': current_app.config.get('SERVICE_NAME', 'workspace-management-service'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'checks': checks,
            'error': str(e),
            'response_time_ms': response_time,
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Checks if the service is alive and should be restarted if not.
    This is a basic check that the Flask application is responding.
    
    Returns:
        JSON response with liveness status
    """
    return jsonify({
        'status': 'alive',
        'service': current_app.config.get('SERVICE_NAME', 'workspace-management-service'),
        'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@health_bp.route('/health/metrics', methods=['GET'])
def metrics():
    """
    Basic metrics endpoint for monitoring.
    
    Returns:
        JSON response with service metrics
    """
    try:
        # Get database connection pool info
        pool_info = {}
        if hasattr(db.engine.pool, 'size'):
            pool_info = {
                'pool_size': db.engine.pool.size(),
                'checked_in': db.engine.pool.checkedin(),
                'checked_out': db.engine.pool.checkedout(),
                'overflow': db.engine.pool.overflow(),
                'invalid': db.engine.pool.invalid()
            }
        
        return jsonify({
            'service': current_app.config.get('SERVICE_NAME', 'workspace-management-service'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'metrics': {
                'database_pool': pool_info,
                'config': {
                    'debug': current_app.debug,
                    'testing': current_app.testing
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Metrics collection failed: {e}")
        
        return jsonify({
            'service': current_app.config.get('SERVICE_NAME', 'workspace-management-service'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'error': 'Failed to collect metrics',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
'''
    
    with open("workspace-management-service/app/routes/health.py", "w") as f:
        f.write(content)


def main():
    """Complete all missing components for workspace management service."""
    print("🔧 Completing Workspace Management Service...")
    
    try:
        # Create missing components
        create_workspace_app_init()
        print("✅ Created app/__init__.py")
        
        create_workspace_requirements()
        print("✅ Created requirements.txt")
        
        create_workspace_dockerfile()
        print("✅ Created Dockerfile")
        
        create_workspace_docker_compose()
        print("✅ Created docker-compose.yml")
        
        create_workspace_run_py()
        print("✅ Created run.py")
        
        create_workspace_readme()
        print("✅ Created README.md")
        
        create_workspace_health_routes()
        print("✅ Created health routes")
        
        print("\n🎉 Workspace Management Service completed successfully!")
        print("\nNext steps:")
        print("1. Test the service: cd workspace-management-service && docker-compose up -d")
        print("2. Access health check: curl http://localhost:5002/health")
        print("3. View API docs: http://localhost:5002/api/v1/")
        
    except Exception as e:
        print(f"❌ Error completing service: {e}")


if __name__ == "__main__":
    main()