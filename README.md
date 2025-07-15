# Event-Driven Microservices Platform

A comprehensive, production-ready microservices architecture built with Flask, PostgreSQL, and RabbitMQ. This platform provides a scalable foundation for modern web applications with event-driven communication and cognitive UX patterns.

## 🏗️ Architecture Overview

This platform consists of **12 specialized microservices** organized into three main categories:

### Core Services
- **User Management Service** (Port 5001) - Authentication, authorization, and user profiles
- **Workspace Management Service** (Port 5002) - Collaborative workspaces and team management
- **Article Management Service** (Port 5003) - Content creation, editing, and publishing

### Domain-Specific Services
- **Domain Management Service** (Port 5004) - Domain registration and WordPress integration
- **AI Configuration Service** (Port 5005) - AI model configuration and provider management
- **Image Generation Service** (Port 5006) - AI-powered image generation and processing

### Infrastructure Services
- **Monitoring Service** (Port 5007) - System health monitoring and alerting
- **Notification Service** (Port 5008) - Multi-channel notification delivery
- **Logging Service** (Port 5009) - Centralized logging and audit trails
- **Configuration Service** (Port 5010) - Global configuration and secrets management
- **Scraping Service** (Port 5011) - External data collection and processing
- **AI Rate Limiter Service** (Port 5012) - AI API usage quotas and rate limiting

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- At least 8GB RAM for running all services

### Option 1: Run All Services (Recommended for Development)

```bash
# Clone the repository
git clone <repository-url>
cd microservices-platform

# Start all services with shared infrastructure
docker-compose -f docker-compose.master.yml up -d

# View logs for all services
docker-compose -f docker-compose.master.yml logs -f

# Stop all services
docker-compose -f docker-compose.master.yml down
```

### Option 2: Run Individual Services

```bash
# Start a specific service (e.g., user management)
cd user-management-service
docker-compose up -d

# Or run locally
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Option 3: Development Mode

```bash
# Start only infrastructure services
docker-compose -f docker-compose.master.yml up -d postgres rabbitmq redis

# Run services locally in development mode
cd user-management-service
export FLASK_ENV=development
export DB_HOST=localhost
export RABBITMQ_HOST=localhost
python run.py
```

## 🔧 Configuration

### Environment Variables

Each service supports the following environment variables:

```bash
# Flask Configuration
FLASK_ENV=development|testing|production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=service_database_name

# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=platform
RABBITMQ_PASS=platform123

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Service-Specific Configuration
LOG_LEVEL=INFO
```

### Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| User Management | 5001 | Authentication & user profiles |
| Workspace Management | 5002 | Collaborative workspaces |
| Article Management | 5003 | Content management |
| Domain Management | 5004 | Domain & WordPress integration |
| AI Configuration | 5005 | AI model configuration |
| Image Generation | 5006 | AI image generation |
| Monitoring | 5007 | System monitoring |
| Notification | 5008 | Multi-channel notifications |
| Logging | 5009 | Centralized logging |
| Configuration | 5010 | Global configuration |
| Scraping | 5011 | Data scraping |
| AI Rate Limiter | 5012 | AI usage quotas |

### Infrastructure Ports

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database |
| RabbitMQ | 5672, 15672 | Message broker & management |
| Redis | 6379 | Caching |
| Nginx (API Gateway) | 80, 443 | Load balancing |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Monitoring dashboards |
| pgAdmin | 8080 | Database administration |

## 📊 Health Checks

Each service provides comprehensive health check endpoints:

```bash
# Basic health check
curl http://localhost:5001/health

# Readiness probe (Kubernetes)
curl http://localhost:5001/health/ready

# Liveness probe (Kubernetes)
curl http://localhost:5001/health/live

# Service metrics
curl http://localhost:5001/health/metrics
```

## 🔐 Security

### Authentication Flow
1. Users authenticate with the User Management Service
2. JWT tokens are issued for authenticated sessions
3. API Gateway validates tokens for all requests
4. Services trust the gateway's authentication

### Authorization Levels
- **Public**: Health checks, documentation
- **Authenticated**: Basic user operations
- **Role-Based**: Admin functions, sensitive operations
- **Workspace-Based**: Workspace-specific permissions

## 📡 Event Architecture

Services communicate through events via RabbitMQ:

### Key Event Types
- **User Events**: `user.created`, `user.activated`, `user.role_changed`
- **Workspace Events**: `workspace.created`, `workspace.member_added`
- **Content Events**: `article.created`, `article.published`
- **System Events**: `service.health_check`, `system.configuration_changed`

### Event Flow Example
```python
# Service A publishes an event
event_service.publish('user.created', {
    'user_id': str(user.id),
    'email': user.email,
    'workspace_id': str(workspace.id)
})

# Service B consumes the event
@event_service.subscribe('user.created')
def handle_user_created(data):
    # Initialize user's workspace resources
    workspace_service.setup_user_workspace(data['user_id'])
```

## 🗄️ Database Schema

### Common Model Structure
All models inherit from `BaseModel` with:
- `id`: UUID primary key
- `created_at`, `updated_at`: Audit timestamps
- `is_deleted`, `deleted_at`: Soft delete support
- `metadata_json`: Additional metadata storage

### Service Relationships
- **User ↔ Workspace**: Many-to-many (membership)
- **User ↔ Article**: One-to-many (authorship)
- **Workspace ↔ Article**: One-to-many (content)
- **User ↔ Role**: Many-to-many (permissions)

## 🧪 Testing

### Running Tests

```bash
# Test all services
for service in */; do
  if [ -d "$service" ] && [ -f "$service/requirements.txt" ]; then
    echo "Testing $service"
    cd "$service"
    pytest
    cd ..
  fi
done

# Test specific service
cd user-management-service
pytest --cov=app tests/

# Integration tests
pytest tests/integration/
```

### Test Coverage
- **Unit Tests**: Models, services, utilities
- **Integration Tests**: Database operations, API endpoints
- **Contract Tests**: Service-to-service communication
- **End-to-End Tests**: Complete user workflows

## 📈 Monitoring

### Prometheus Metrics
- Service response times and error rates
- Database connection pool metrics
- RabbitMQ queue depths
- Business metrics (registrations, articles, etc.)

### Grafana Dashboards
- System overview dashboard
- Service-specific dashboards
- Business metrics dashboard
- Infrastructure monitoring

### Log Aggregation
- Structured logging across all services
- Centralized log collection via Logging Service
- Log correlation with request IDs
- Alert integration for critical errors

## 🚀 Deployment

### Development
```bash
docker-compose -f docker-compose.master.yml up -d
```

### Production (Kubernetes)
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n microservices

# View service logs
kubectl logs -f deployment/user-management-service -n microservices
```

### Scaling
```bash
# Scale specific service
kubectl scale deployment user-management-service --replicas=3 -n microservices

# Auto-scaling based on CPU
kubectl autoscale deployment user-management-service --cpu-percent=70 --min=2 --max=10 -n microservices
```

## 🔧 Development

### Adding a New Service

1. **Create Service Structure**
```bash
mkdir new-service
cd new-service
# Copy template files from existing service
```

2. **Define Models**
```python
# app/models/new_model.py
from .base import BaseModel

class NewModel(BaseModel):
    __tablename__ = 'new_models'
    # Define your fields
```

3. **Implement Business Logic**
```python
# app/services/new_service.py
class NewService:
    def create_item(self, data):
        # Business logic here
        pass
```

4. **Create API Routes**
```python
# app/routes/api.py
@api_bp.route('/items', methods=['POST'])
def create_item():
    # API endpoint logic
    pass
```

5. **Add Event Handlers**
```python
# app/events/handlers.py
@event_service.subscribe('item.created')
def handle_item_created(data):
    # Event handling logic
    pass
```

### Code Standards
- **Python**: PEP 8 with Black formatting
- **Typing**: Full type annotations required
- **Documentation**: Comprehensive docstrings
- **Testing**: Minimum 80% code coverage
- **Logging**: Structured logging with correlation IDs

## 📚 API Documentation

Each service provides OpenAPI/Swagger documentation:
- User Management: http://localhost:5001/docs
- Workspace Management: http://localhost:5002/docs
- Article Management: http://localhost:5003/docs
- [etc. for all services]

## 🛠️ Troubleshooting

### Common Issues

1. **Service Won't Start**
```bash
# Check logs
docker-compose logs service-name

# Check dependencies
docker-compose ps
```

2. **Database Connection Issues**
```bash
# Verify database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres
```

3. **Event Publishing/Consuming Issues**
```bash
# Check RabbitMQ status
docker-compose ps rabbitmq

# Access RabbitMQ management interface
open http://localhost:15672
```

### Performance Tuning

1. **Database Optimization**
- Review slow query logs
- Add appropriate indexes
- Tune connection pool settings

2. **Service Optimization**
- Enable Redis caching
- Implement async processing
- Optimize database queries

3. **Infrastructure Scaling**
- Scale horizontally with load balancers
- Use read replicas for databases
- Implement CDN for static content

## 🤝 Contributing

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Make Changes**: Follow code standards and add tests
4. **Run Tests**: Ensure all tests pass
5. **Submit Pull Request**: With clear description of changes

### Development Workflow
1. Pick an issue from the project board
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request for review

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- **Issues**: Create an issue in the repository
- **Discussions**: Use GitHub Discussions for general questions
- **Security**: Email security@platform.com for security issues

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core microservices architecture
- ✅ Event-driven communication
- ✅ Comprehensive testing
- ✅ Docker containerization

### Phase 2 (Planned)
- [ ] Kubernetes deployment
- [ ] Service mesh (Istio)
- [ ] GraphQL gateway
- [ ] Advanced monitoring

### Phase 3 (Future)
- [ ] Machine learning integration
- [ ] Real-time collaboration
- [ ] Mobile API optimization
- [ ] Advanced analytics

---

**Built with ❤️ using Flask, PostgreSQL, RabbitMQ, and modern DevOps practices.**