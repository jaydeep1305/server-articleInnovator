# Workspace Management Service

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
