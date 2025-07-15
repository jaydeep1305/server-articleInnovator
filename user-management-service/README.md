# User Management Service

A comprehensive Flask microservice for user authentication, authorization, and management with PostgreSQL, RabbitMQ, and Docker support. Built following OOP standards, strict typing, and cognitive patterns for production use.

## 🏗️ Architecture Overview

This microservice implements a clean architecture with the following layers:

- **Presentation Layer**: RESTful API endpoints with Flask blueprints
- **Business Logic Layer**: Service classes with domain-specific operations
- **Data Access Layer**: SQLAlchemy models with comprehensive validation
- **Infrastructure Layer**: Database, message queue, and external service integrations

### Key Features

- ✅ **User Authentication & Authorization**: JWT-based auth with role-based access control (RBAC)
- ✅ **Comprehensive User Management**: CRUD operations with business validation
- ✅ **Security Features**: Password hashing, account lockout, email verification
- ✅ **Event-Driven Architecture**: RabbitMQ integration for microservice communication
- ✅ **Database Management**: PostgreSQL with SQLAlchemy ORM and migrations
- ✅ **API Versioning**: Structured API versioning with proper HTTP status codes
- ✅ **Health Checks**: Kubernetes-ready health endpoints
- ✅ **Monitoring**: Metrics endpoints and comprehensive logging
- ✅ **Testing**: Comprehensive unit and integration tests with pytest
- ✅ **Docker Support**: Multi-stage builds with production-ready containers
- ✅ **Development Tools**: Hot-reload, debugging, and development utilities

## 📋 Requirements

### System Requirements
- Python 3.11+
- PostgreSQL 13+
- RabbitMQ 3.12+
- Redis 7+ (for rate limiting)
- Docker & Docker Compose (for containerized development)

### Python Dependencies
See `requirements.txt` for complete list. Key dependencies include:
- Flask 3.0.0
- SQLAlchemy 2.0.23
- Flask-JWT-Extended 4.6.0
- psycopg2-binary 2.9.9
- pika 1.3.2 (RabbitMQ client)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd user-management-service
   ```

2. **Start all services**:
   ```bash
   # Start core services (PostgreSQL, RabbitMQ, Redis, App)
   docker-compose up -d
   
   # Or start with additional tools (pgAdmin)
   docker-compose --profile tools up -d
   
   # Or start with monitoring (Prometheus, Grafana)
   docker-compose --profile monitoring up -d
   ```

3. **Initialize database**:
   ```bash
   docker-compose exec user-service python -c "
   from app import create_app, db
   from app.models import User, Role, Permission
   app = create_app()
   with app.app_context():
       db.create_all()
       print('Database initialized')
   "
   ```

4. **Access services**:
   - **API**: http://localhost:5000
   - **Health Check**: http://localhost:5000/health
   - **pgAdmin**: http://localhost:8080 (admin@example.com / admin)
   - **RabbitMQ Management**: http://localhost:15672 (guest / guest)
   - **Prometheus**: http://localhost:9090 (with monitoring profile)
   - **Grafana**: http://localhost:3000 (admin / admin, with monitoring profile)

### Option 2: Local Development

1. **Setup Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup environment variables**:
   ```bash
   export FLASK_ENV=development
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_USER=postgres
   export DB_PASSWORD=postgres
   export DB_NAME=user_management_dev
   export RABBITMQ_HOST=localhost
   export RABBITMQ_USER=guest
   export RABBITMQ_PASS=guest
   ```

3. **Start external services** (PostgreSQL, RabbitMQ):
   ```bash
   docker-compose up -d postgres rabbitmq redis
   ```

4. **Initialize database**:
   ```bash
   python -c "
   from app import create_app, db
   app = create_app()
   with app.app_context():
       db.create_all()
   "
   ```

5. **Run the application**:
   ```bash
   python run.py
   ```

## 📊 Database Schema

### Core Models

#### User Model
```python
- id: UUID (Primary Key)
- email: String(255) UNIQUE
- username: String(50) UNIQUE  
- password_hash: String(255)
- first_name: String(100)
- last_name: String(100)
- phone_number: String(20)
- birth_date: Date
- bio: Text
- profile_picture_url: String(500)
- is_verified: Boolean
- is_admin: Boolean
- last_login_at: DateTime
- failed_login_attempts: String(10)
- account_locked_until: DateTime
- password_changed_at: DateTime
- timezone: String(50)
- language: String(10)
- receive_notifications: Boolean
- created_at: DateTime
- updated_at: DateTime
- is_active: Boolean
```

#### Role Model  
```python
- id: UUID (Primary Key)
- name: String(100) UNIQUE
- display_name: String(200)
- description: Text
- is_system_role: String(10)
- hierarchy_level: Integer
- color: String(7)
- created_at: DateTime
- updated_at: DateTime
- is_active: Boolean
```

#### Permission Model
```python
- id: UUID (Primary Key)
- name: String(100) UNIQUE
- display_name: String(200) 
- description: String(500)
- group: String(50)
- resource: String(50)
- action: String(50)
- scope: String(20)
- is_system_permission: String(10)
- created_at: DateTime
- updated_at: DateTime
- is_active: Boolean
```

### Relationships
- **Users ↔ Roles**: Many-to-Many through `user_roles` table
- **Roles ↔ Permissions**: Many-to-Many through `role_permissions` table

## 🔌 API Endpoints

### Health & Monitoring
```http
GET /health                    # Basic health check
GET /health/ready             # Readiness probe (Kubernetes)
GET /health/live              # Liveness probe (Kubernetes)  
GET /health/metrics           # Service metrics
```

### Authentication
```http
POST /api/v1/auth/register    # User registration
POST /api/v1/auth/login       # User login
POST /api/v1/auth/logout      # User logout
POST /api/v1/auth/refresh     # Refresh JWT token
POST /api/v1/auth/verify      # Verify email
```

### User Management
```http
GET    /api/v1/users          # List users (paginated)
POST   /api/v1/users          # Create user
GET    /api/v1/users/{id}     # Get user by ID
PUT    /api/v1/users/{id}     # Update user
DELETE /api/v1/users/{id}     # Delete user (soft delete)
PATCH  /api/v1/users/{id}/password  # Change password
PATCH  /api/v1/users/{id}/verify    # Verify user email
```

### Role Management
```http
GET    /api/v1/roles          # List roles
POST   /api/v1/roles          # Create role
GET    /api/v1/roles/{id}     # Get role by ID
PUT    /api/v1/roles/{id}     # Update role
DELETE /api/v1/roles/{id}     # Delete role
POST   /api/v1/roles/{id}/permissions  # Add permission to role
DELETE /api/v1/roles/{id}/permissions/{permission_id}  # Remove permission
```

### Permission Management
```http
GET    /api/v1/permissions    # List permissions
POST   /api/v1/permissions    # Create permission
GET    /api/v1/permissions/{id}  # Get permission by ID
PUT    /api/v1/permissions/{id}  # Update permission
DELETE /api/v1/permissions/{id}  # Delete permission
```

## 🏷️ API Versioning

The API supports versioning through URL prefixes:
- **Current**: `/api/v1/`
- **Headers**: `API-Version: v1` (returned in responses)
- **Future**: `/api/v2/` (when breaking changes are introduced)

### Versioning Strategy
- **URL-based versioning** for major version changes
- **Header-based content negotiation** for minor changes
- **Backward compatibility** maintained for at least 2 major versions
- **Deprecation notices** provided 6 months before removal

## 🔒 Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access Control (RBAC)**: Fine-grained permission system
- **Account Lockout**: Progressive lockout after failed login attempts
- **Password Security**: bcrypt hashing with configurable rounds
- **Email Verification**: Required for account activation

### Data Protection
- **Input Validation**: Comprehensive validation with cognitive patterns
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Prevention**: Input sanitization and output encoding
- **CSRF Protection**: CSRF tokens for state-changing operations
- **Rate Limiting**: Configurable rate limits per endpoint

### Monitoring & Auditing
- **Audit Trails**: Comprehensive logging of user actions
- **Security Events**: Failed logins, password changes, role modifications
- **Health Monitoring**: Real-time service health and metrics
- **Error Tracking**: Structured logging with correlation IDs

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m "unit"           # Unit tests only
pytest -m "integration"    # Integration tests only
pytest -m "not slow"       # Skip slow tests

# Run specific test file
pytest tests/test_user_model.py

# Run with verbose output
pytest -v
```

### Test Structure
```
tests/
├── unit/                  # Unit tests for individual components
│   ├── test_user_model.py # User model tests
│   ├── test_role_model.py # Role model tests
│   └── test_services.py   # Service layer tests
├── integration/           # Integration tests
│   ├── test_api_endpoints.py  # API endpoint tests
│   └── test_database.py       # Database integration tests
└── conftest.py           # Test configuration and fixtures
```

### Test Coverage
The test suite covers:
- **Models**: Validation, relationships, business logic
- **Services**: CRUD operations, business rules, error handling  
- **API Endpoints**: Request/response validation, authentication
- **Security**: Authentication, authorization, input validation
- **Edge Cases**: Boundary conditions, error scenarios

## 🐳 Docker Deployment

### Development
```bash
# Start development environment
docker-compose up -d

# Watch for changes (hot reload)
docker-compose watch

# View logs
docker-compose logs -f user-service
```

### Production
```bash
# Build production image
docker build --target production-gunicorn -t user-management-service:latest .

# Run with production settings
docker run -d \
  --name user-management-service \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e DB_HOST=your-db-host \
  -e DB_USER=your-db-user \
  -e DB_PASSWORD=your-db-password \
  user-management-service:latest
```

### Kubernetes Deployment
```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-management-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-management-service
  template:
    metadata:
      labels:
        app: user-management-service
    spec:
      containers:
      - name: user-management-service
        image: user-management-service:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: host
        livenessProbe:
          httpGet:
            path: /health/live
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 📈 Monitoring & Observability

### Health Checks
- **Basic Health**: `/health` - Simple service status
- **Readiness**: `/health/ready` - Database connectivity check
- **Liveness**: `/health/live` - Process responsiveness check
- **Metrics**: `/health/metrics` - Detailed service metrics

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Automatic log rotation and archival
- **Centralized Logging**: Compatible with ELK, Fluentd, etc.

### Metrics
- **Application Metrics**: Request count, response time, error rate
- **Business Metrics**: User registrations, login attempts, active users
- **Infrastructure Metrics**: Memory usage, CPU utilization, database connections
- **Custom Metrics**: Domain-specific measurements

## 🔧 Configuration

### Environment Variables

#### Database Configuration
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=user_management_dev
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

#### RabbitMQ Configuration
```bash
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=events
```

#### Application Configuration
```bash
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600
LOG_LEVEL=INFO
API_VERSION=v1
```

### Configuration Classes
- **DevelopmentConfig**: Debug mode, verbose logging
- **TestingConfig**: In-memory database, disabled external services
- **ProductionConfig**: Security hardening, optimized performance

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with proper tests
4. Ensure code quality: `black app/ && flake8 app/ && mypy app/`
5. Run tests: `pytest`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Code Standards
- **Python Style**: Follow PEP 8 with Black formatting
- **Type Hints**: Strict typing for all functions and methods
- **Documentation**: Comprehensive docstrings and inline comments
- **Testing**: Minimum 90% test coverage for new code
- **Security**: Security review required for authentication/authorization changes

### Cognitive Patterns
This codebase follows "cognitive patterns" - development practices that enhance code readability, maintainability, and developer productivity:

- **Explicit Intent**: Code should clearly express business intent
- **Fail-Fast Validation**: Validate inputs early and provide clear error messages
- **Defensive Programming**: Handle edge cases and unexpected inputs gracefully
- **Audit Trails**: Log significant business events for troubleshooting
- **Performance Awareness**: Consider performance implications of design decisions

## 📚 Additional Resources

### Documentation
- **API Documentation**: Auto-generated Swagger/OpenAPI docs
- **Database Schema**: ERD and migration guides
- **Deployment Guide**: Step-by-step deployment instructions
- **Troubleshooting**: Common issues and solutions

### External Dependencies
- **Flask Documentation**: https://flask.palletsprojects.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **RabbitMQ Documentation**: https://www.rabbitmq.com/documentation.html

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Support

For support and questions:
- **Issues**: Create a GitHub issue for bugs and feature requests
- **Documentation**: Check the docs/ directory for detailed guides
- **Community**: Join our development community discussions

---

**Built with ❤️ using Flask, SQLAlchemy, and PostgreSQL**