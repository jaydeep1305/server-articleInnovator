# Microservices Architecture Analysis & Migration Plan

## Current Monolithic Architecture

### Technology Stack
- **Backend**: Django with DRF
- **Database**: PostgreSQL (multi-database)
- **Queue**: Celery with Redis
- **Auth**: JWT tokens

### Current Apps Analysis
1. **apiApp** - Main business logic (1399 lines in models.py)
2. **competitorApp** - Competitor monitoring (289 lines in models.py) 
3. **AIMessageService** - AI processing (41 lines in models.py)
4. **frontendApp** - Web UI

### Key Models Identified
- User management (users, roles, permissions)
- Workspace management
- Domain management (WordPress integration)
- Article management and publishing
- AI configuration (prompts, models)
- Competitor monitoring and scraping
- Image generation and templates
- Notifications and activity logging

## Proposed Microservices Architecture

### Core Infrastructure
- **API Gateway**: APISIX
- **Message Broker**: RabbitMQ
- **Identity Provider**: Keycloak
- **Databases**: PostgreSQL per service
- **External Services**: AWS Lambda

### Services Breakdown

#### 1. User Management Service (Port 5001)
**Responsibilities**: Authentication, users, roles, permissions
**Database**: user_management_db
**Key Endpoints**:
- POST /auth/login, /auth/register
- GET/POST /users, /roles, /permissions
- POST /users/{id}/workspaces (assign to workspace)

#### 2. Workspace Management Service (Port 5002)
**Responsibilities**: Workspaces and user relationships
**Database**: workspace_db
**Key Endpoints**:
- GET/POST /workspaces
- GET/POST /workspaces/{id}/users
- GET /workspaces/{id}/stats

#### 3. Domain Management Service (Port 5003)
**Responsibilities**: WordPress domains and integration
**Database**: domain_db
**Key Endpoints**:
- GET/POST /domains
- POST /domains/{id}/test-connection
- GET/POST /domains/{id}/wp-categories
- GET/POST /domains/{id}/wp-tags
- GET/POST /domains/{id}/wp-authors

#### 4. Article Management Service (Port 5004)
**Responsibilities**: Content creation and publishing
**Database**: article_db
**Key Endpoints**:
- GET/POST /articles
- POST /articles/{id}/publish
- GET/POST /article-types
- GET /articles/{id}/content

#### 5. AI Configuration Service (Port 5005)
**Responsibilities**: AI models, prompts, configurations
**Database**: ai_config_db
**Key Endpoints**:
- GET/POST /ai-configs
- GET/POST /prompts, /supportive-prompts
- POST /ai/generate

#### 6. Image Generation Service (Port 5006)
**Responsibilities**: Image templates and generation
**Database**: image_db
**Key Endpoints**:
- GET/POST /image-templates, /image-tags
- POST /generate

#### 7. Monitoring Service (Port 5007)
**Responsibilities**: Competitor analysis and metrics
**Database**: monitoring_db
**Key Endpoints**:
- GET/POST /competitors
- GET /analytics, /console-metrics
- POST /monitoring/start

#### 8. Notification Service (Port 5008)
**Responsibilities**: User notifications
**Database**: notification_db
**Key Endpoints**:
- GET/POST /notifications
- POST /notifications/send

#### 9. Logging Service (Port 5009)
**Responsibilities**: Centralized logging
**Database**: logging_db
**Key Endpoints**:
- GET/POST /logs
- GET /logs/activity

#### 10. Configuration Service (Port 5010)
**Responsibilities**: System settings
**Database**: config_db
**Key Endpoints**:
- GET/POST /configs, /motivations
- GET /languages, /countries

### External Services (Lambda)
1. **Scraping Service** - URL/SERP/sitemap scraping
2. **AI Rate Limiter Service** - AI API rate limiting

## Event-Driven Communication

### Key Events
- user.created, user.workspace.assigned
- workspace.created, workspace.updated
- domain.created, domain.wordpress.connected
- article.creation.requested, article.published
- ai.response.received, image.generated
- monitoring.alert.triggered, notification.sent

### Communication Pattern
Services communicate via RabbitMQ events instead of direct database calls.

## Migration Strategy

### Phase 1: Infrastructure Setup
- Set up RabbitMQ, APISIX, Keycloak
- Prepare separate databases

### Phase 2: Service Extraction
- Extract User Management Service first
- Extract Workspace and Configuration services
- Extract remaining services in parallel

### Phase 3: Event Integration
- Implement event publishing/subscribing
- Replace direct database calls with events

### Phase 4: Gateway & External Services
- Configure APISIX routing
- Migrate scraping to Lambda
- Implement AI rate limiting

This architecture provides better scalability, maintainability, and fault tolerance.
