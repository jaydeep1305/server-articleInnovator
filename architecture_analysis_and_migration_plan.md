# Architecture Analysis and Event-Driven Migration Plan

## Current Monolithic Architecture Analysis

### Technology Stack
- **Backend**: Django (Python) with DRF
- **Database**: PostgreSQL (with multi-database setup)
- **Queue**: Celery with Redis
- **Authentication**: JWT
- **Frontend**: Svelte with Tailwind CSS

### Current Modules Identified

#### Core Applications
1. **apiApp** - Main business logic (Users, Workspaces, Domains, Articles, AI Config, Prompts)
2. **competitorApp** - Competitor monitoring and scraping
3. **AIMessageService** - AI message processing
4. **frontendApp** - Web UI

#### Key Domain Models
- User Management (Users, Roles, Permissions)
- Workspace Management
- Domain Management (WordPress integration)
- Article Management
- AI Configuration (Prompts, Models)
- Competitor Monitoring
- Image Generation
- Notifications
- Activity Logging

### Current Issues with Monolithic Architecture
1. **Tight Coupling**: All modules share the same database and codebase
2. **Scalability Issues**: Cannot scale individual components independently
3. **Deployment Complexity**: Any change requires full application deployment
4. **Technology Lock-in**: All components must use Django/Python
5. **Single Point of Failure**: Entire application fails if one module fails

## Event-Driven Microservices Architecture Plan

### Core Infrastructure Components
- **API Gateway**: APISIX
- **Message Broker**: RabbitMQ
- **Identity Provider**: Keycloak
- **Database**: PostgreSQL (per service)
- **Content Management**: WordPress
- **External Services**: AWS Lambda functions

### Service Architecture

#### Internal Services
1. **User Management Service**
2. **Workspace Management Service**
3. **Domain Management Service**
4. **Article Management Service**
5. **AI Configuration Service**
6. **Image Generation Service**
7. **Monitoring Service**
8. **Notification Service**
9. **Logging Service**
10. **Configuration Service**

#### External Services (Lambda)
1. **Scraping Service**
2. **AI Rate Limiter Service**

### Event-Driven Communication Patterns

#### Events Design
```
User Events:
- user.created
- user.updated
- user.deleted
- user.workspace.assigned
- user.workspace.revoked

Workspace Events:
- workspace.created
- workspace.updated
- workspace.deleted
- workspace.user.added
- workspace.user.removed

Domain Events:
- domain.created
- domain.updated
- domain.deleted
- domain.wordpress.connected
- domain.wordpress.disconnected

Article Events:
- article.creation.requested
- article.created
- article.updated
- article.published
- article.failed

AI Events:
- ai.request.submitted
- ai.response.received
- ai.generation.completed
- ai.generation.failed

Monitoring Events:
- competitor.url.discovered
- competitor.content.scraped
- monitoring.alert.triggered

Notification Events:
- notification.send.requested
- notification.sent
- notification.failed
```

### Migration Strategy

#### Phase 1: Database Separation
1. Split databases by domain
2. Implement database-per-service pattern
3. Create data migration scripts

#### Phase 2: Service Extraction
1. Extract User Management Service
2. Extract Workspace Management Service
3. Extract Configuration Services

#### Phase 3: Event Implementation
1. Implement RabbitMQ message broker
2. Add event publishing/subscribing
3. Replace direct database calls with events

#### Phase 4: Gateway Implementation
1. Configure APISIX as API Gateway
2. Implement routing rules
3. Add authentication integration with Keycloak

#### Phase 5: External Services
1. Migrate scraping to Lambda
2. Implement AI rate limiting service
3. Add monitoring and logging

## Service Communication Matrix

| Service | Publishes Events | Subscribes to Events |
|---------|------------------|---------------------|
| User Management | user.*, workspace.user.* | workspace.created |
| Workspace Management | workspace.* | user.created |
| Domain Management | domain.* | workspace.created, user.workspace.assigned |
| Article Management | article.* | domain.created, ai.response.received |
| AI Configuration | ai.* | article.creation.requested |
| Image Generation | image.* | article.creation.requested |
| Monitoring | competitor.*, monitoring.* | domain.created |
| Notification | notification.* | article.published, monitoring.alert.triggered |
| Logging | - | *.* (all events) |

## Technology Decisions

### Service Technologies
- **API Framework**: Flask (as specified)
- **Authentication**: Service-to-service via Keycloak
- **Database**: PostgreSQL per service
- **Message Format**: JSON
- **API Documentation**: OpenAPI/Swagger

### Infrastructure
- **Container**: Docker
- **Orchestration**: Docker Compose (development), Kubernetes (production)
- **Load Balancing**: APISIX
- **Service Discovery**: Built into APISIX
- **Health Checks**: HTTP endpoints per service

## Data Consistency Strategy

### Eventual Consistency
- Services maintain their own data
- Cross-service data synchronized via events
- Implement compensation patterns for failures

### Saga Pattern
- For complex workflows (article creation, user onboarding)
- Orchestration via dedicated workflow services
- Rollback mechanisms for failures

### CQRS Implementation
- Command services for writes
- Query services for reads
- Event sourcing for audit trails

## Security Architecture

### Authentication Flow
1. Frontend → APISIX → Keycloak (token validation)
2. Service-to-service: mTLS + service tokens
3. External services: API keys + Lambda authorizers

### Authorization
- Role-based access control via Keycloak
- Resource-based permissions
- Service-level authorization

## Monitoring and Observability

### Metrics
- Service health metrics
- Event processing metrics
- Business metrics (articles created, users active)

### Logging
- Centralized logging via dedicated service
- Structured JSON logs
- Correlation IDs across services

### Tracing
- Distributed tracing for request flows
- Event correlation tracking
- Performance monitoring

## Deployment Strategy

### Development
- Docker Compose for local development
- Shared databases for easier development

### Staging
- Kubernetes deployment
- Service mesh (Istio/Linkerd)
- Full event-driven communication

### Production
- Multi-region deployment
- Auto-scaling based on metrics
- Circuit breakers and retries

This analysis provides the foundation for the detailed Swagger documentation that follows for each service.