# Blog Microservice

A comprehensive, production-ready blog microservice built with Flask, SQLAlchemy, and PostgreSQL. This microservice demonstrates best practices in Python OOP, microservice architecture, API design, and deployment strategies.

## 🏗 Architecture Overview

### Microservice Structure

```
blog_service/
├── app/                    # Main application code
│   ├── models/            # Database models (SQLAlchemy)
│   │   ├── base.py        # Base model with common functionality
│   │   ├── user.py        # User model with authentication
│   │   ├── article.py     # Article model with publishing logic
│   │   └── comment.py     # Comment model with moderation
│   ├── services/          # Business logic layer
│   │   ├── base_service.py    # Base service with CRUD operations
│   │   ├── user_service.py    # User management service
│   │   ├── article_service.py # Article management service
│   │   └── comment_service.py # Comment management service
│   ├── routes/            # Flask route definitions
│   │   ├── user_routes.py     # User API endpoints
│   │   ├── article_routes.py  # Article API endpoints
│   │   ├── comment_routes.py  # Comment API endpoints
│   │   └── health_routes.py   # Health check endpoints
│   └── __init__.py        # Application factory
├── config/                # Configuration management
│   └── config.py          # Environment-specific configs
├── tests/                 # Unit tests
│   └── test_user_service.py  # Comprehensive test examples
├── Dockerfile             # Production container definition
├── docker-compose.yml     # Development environment setup
├── requirements.txt       # Python dependencies
└── app.py                # Application entry point
```

### Key Features

- **🏛 Clean Architecture**: Separation of concerns with models, services, and routes
- **🔒 Security**: Password hashing, input validation, SQL injection protection
- **📊 Type Safety**: Comprehensive type hints throughout the codebase
- **🧪 Testing**: Unit tests with pytest and comprehensive coverage
- **📖 Documentation**: Extensive docstrings and inline comments
- **🚀 Production Ready**: Docker containers, health checks, monitoring
- **🔍 Observability**: Health checks, metrics, and logging
- **📈 Scalability**: Pagination, caching support, and database optimization

## 🛠 Technology Stack

- **Framework**: Flask 2.3+
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Authentication**: Werkzeug password hashing
- **Testing**: pytest with comprehensive fixtures
- **Containerization**: Docker and Docker Compose
- **Database Migrations**: Flask-Migrate
- **API Documentation**: RESTful design with JSON responses
- **Monitoring**: Health checks and metrics endpoints

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (if running locally)

### Development Setup

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd blog_service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   export FLASK_ENV=development
   export SECRET_KEY=your-secret-key
   export DATABASE_URL=postgresql://blog_user:blog_password@localhost:5432/blog_dev
   ```

3. **Database Setup**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

4. **Run Application**
   ```bash
   python app.py
   ```

### Docker Development

1. **Start All Services**
   ```bash
   docker-compose up -d
   ```

2. **View Logs**
   ```bash
   docker-compose logs -f blog_app
   ```

3. **Access Services**
   - Blog API: http://localhost:5000
   - Health Check: http://localhost:5000/health/status
   - pgAdmin: http://localhost:8080 (admin@blog.local / admin)

4. **Optional Monitoring**
   ```bash
   # Start with monitoring tools
   docker-compose --profile monitoring up -d
   
   # Access monitoring
   # Prometheus: http://localhost:9090
   # Grafana: http://localhost:3000 (admin / admin)
   ```

## 📡 API Endpoints

### User Management

```http
POST /api/v1/users/register
POST /api/v1/users/login
GET  /api/v1/users
GET  /api/v1/users/{id}
PUT  /api/v1/users/{id}
DELETE /api/v1/users/{id}
GET  /api/v1/users/{id}/profile
POST /api/v1/users/{id}/activate
PUT  /api/v1/users/{id}/password
```

### Article Management

```http
GET  /api/v1/articles
POST /api/v1/articles
GET  /api/v1/articles/{id}
PUT  /api/v1/articles/{id}
DELETE /api/v1/articles/{id}
GET  /api/v1/articles/slug/{slug}
POST /api/v1/articles/{id}/publish
GET  /api/v1/articles/search
```

### Comment Management

```http
GET  /api/v1/comments
POST /api/v1/comments
GET  /api/v1/comments/{id}
PUT  /api/v1/comments/{id}
DELETE /api/v1/comments/{id}
GET  /api/v1/comments/article/{article_id}
POST /api/v1/comments/{id}/approve
GET  /api/v1/comments/moderation
```

### Health & Monitoring

```http
GET /health/live      # Liveness probe
GET /health/ready     # Readiness probe
GET /health/status    # Detailed health info
GET /health/metrics   # Prometheus metrics
```

## 🗃 Database Models

### User Model
- Authentication with password hashing
- Profile management with validation
- Activity tracking and statistics
- Account activation/deactivation

### Article Model
- Content management with WYSIWYG support
- Publishing workflow (draft → published → archived)
- SEO optimization fields
- View tracking and analytics
- Tag and category organization

### Comment Model
- Threaded commenting system
- Moderation workflow
- Spam detection and filtering
- Guest and registered user support

## 🎯 Design Patterns & Best Practices

### Service Layer Pattern
```python
# Clean separation of business logic
class UserService(BaseService[User]):
    def register(self, username: str, email: str, password: str) -> User:
        # Validation, business rules, and persistence
        pass
```

### Repository Pattern
```python
# Database abstraction through base service
class BaseService(Generic[ModelType]):
    def paginate(self, page: int, per_page: int) -> PaginationResult:
        # Common pagination logic
        pass
```

### Cognitive Functions
```python
def validate_email(email: str) -> bool:
    """
    Cognitive function for email validation.
    
    This function demonstrates complex validation logic
    with multiple checks and comprehensive error messages.
    """
    # Pattern matching for email format
    # Length validation
    # Domain validation
    pass
```

### Error Handling
```python
@app.errorhandler(ValueError)
def handle_value_error(error):
    """Handle validation errors with proper HTTP status codes."""
    return jsonify({'error': str(error)}), 400
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_user_service.py

# Run with verbose output
pytest -v
```

### Test Structure
```python
class TestUserService:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test environment with Flask app and database."""
        
    def test_register_user_success(self):
        """Test successful user registration with validation."""
        
    def test_authentication_scenarios(self):
        """Test various authentication scenarios and edge cases."""
```

## 🚢 Deployment

### Production Deployment

1. **Build Production Image**
   ```bash
   docker build -t blog-microservice:latest .
   ```

2. **Environment Variables**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-production-secret
   export DATABASE_URL=postgresql://user:pass@host:5432/blog_prod
   ```

3. **Run Container**
   ```bash
   docker run -d \
     --name blog-microservice \
     -p 5000:5000 \
     -e FLASK_ENV=production \
     -e SECRET_KEY=$SECRET_KEY \
     -e DATABASE_URL=$DATABASE_URL \
     blog-microservice:latest
   ```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog-microservice
spec:
  replicas: 3
  selector:
    matchLabels:
      app: blog-microservice
  template:
    metadata:
      labels:
        app: blog-microservice
    spec:
      containers:
      - name: blog-microservice
        image: blog-microservice:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: blog-secrets
              key: database-url
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

## 📊 Monitoring & Observability

### Health Checks
- **Liveness**: `/health/live` - Application is running
- **Readiness**: `/health/ready` - Application is ready to serve traffic
- **Status**: `/health/status` - Detailed health information

### Metrics
- **Prometheus**: `/health/metrics` - Application metrics
- **Custom Metrics**: User count, article count, comment moderation queue

### Logging
```python
# Structured logging throughout the application
current_app.logger.info(f"User registered: {user.username}")
current_app.logger.error(f"Authentication failed: {str(e)}")
```

## 🔧 Configuration Management

### Environment-Specific Configs
```python
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
```

### API Versioning
- Base URL: `/api/v1/`
- Version header support
- Backward compatibility strategy

### Error Handling
- Comprehensive error responses
- Proper HTTP status codes
- Validation error details
- Production error hiding

## 🤝 Contributing

1. **Code Style**: Follow PEP 8 and use type hints
2. **Testing**: Write tests for new features
3. **Documentation**: Update docstrings and README
4. **Commits**: Use conventional commit messages

### Development Workflow
```bash
# Create feature branch
git checkout -b feature/user-authentication

# Run tests
pytest

# Run linting
flake8 app/

# Commit changes
git commit -m "feat: add user authentication with JWT"
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Microservices Patterns](https://microservices.io/patterns/)

---

**Built with ❤️ using Python, Flask, and best practices in microservice architecture.**