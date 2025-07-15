# Logging Service

Centralized logging and audit trails

## Overview

The Logging Service is a microservice that handles centralized logging and audit trails. It's part of an event-driven architecture using Flask, PostgreSQL, and RabbitMQ.

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
cd logging-service

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f logging-service

# Stop services
docker-compose down
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_NAME=logging_dev

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

- **LogEntry**: [Description needed]
- **AuditLog**: [Description needed]
- **SystemEvent**: [Description needed]

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
docker build -t logging-service:latest --target production .

# Run production container
docker run -d \
  --name logging-service \
  -p 5008:5008 \
  -e DB_HOST=your-db-host \
  -e DB_USER=your-db-user \
  -e DB_PASSWORD=your-db-password \
  -e DB_NAME=your-db-name \
  logging-service:latest
```

### Kubernetes

The service includes health check endpoints for Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logging-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: logging-service
  template:
    metadata:
      labels:
        app: logging-service
    spec:
      containers:
      - name: logging-service
        image: logging-service:latest
        ports:
        - containerPort: 5008
        livenessProbe:
          httpGet:
            path: /health/live
            port: 5008
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 5008
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
- Logs are written to `logs/logging-service.log`
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
- Service: logging-service
- Version: 1.0.0
- Port: 5008
- Database: logging
