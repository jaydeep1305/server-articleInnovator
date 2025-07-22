# Article Innovator - Class-Based Components Diagram

This document presents a class diagram focused on the actual **class-based components** in the Article Innovator Django project, showing their methods and relationships.

## Project Architecture Note

**Important**: This Django project primarily uses **function-based views** with `@api_view` decorators rather than class-based views. The classes documented here represent the core utility, service, and middleware components that support the application.

## Class-Based Components

### 1. Middleware Classes

#### AccessControlMiddleware
**Purpose**: Handles authentication, authorization, and access control for all API requests.

**Methods**:
- `__init__(get_response)` - Initialize middleware with response handler
- `__call__(request): HttpResponse` - Main middleware execution logic
- `authenticate_user(request): tuple` - JWT token authentication

**Key Features**:
- JWT token validation
- API key authentication
- Role-based permission checking
- Workspace access control
- Exempt path handling

#### RateLimitMiddleware  
**Purpose**: Implements rate limiting and IP banning to prevent abuse.

**Attributes**:
- `RATE_LIMIT: int = 1000` - Maximum requests allowed
- `TIME_WINDOW: int = 60` - Time window in seconds
- `BAN_DURATION: int = 86400` - Ban duration (24 hours)

**Methods**:
- `__init__(get_response)` - Initialize middleware
- `__call__(request): HttpResponse` - Rate limiting logic

**Key Features**:
- IP-based rate limiting
- User+IP combination tracking
- Automatic 24-hour banning
- Cache-based request counting

#### ActivityLogMiddleware
**Purpose**: Logs all user activities and system events.

**Methods**:
- `__init__(get_response)` - Initialize middleware
- `__call__(request): HttpResponse` - Activity logging
- `process_request(request): void` - Pre-request processing
- `process_response(request, response): HttpResponse` - Post-request processing

**Key Features**:
- Comprehensive activity tracking
- Database logging
- User action monitoring

### 2. Service Classes

#### ImageGenerator
**Purpose**: Handles image template processing and generation with ImageKit integration.

**Methods**:
- `get_all_templates_by_tags(json_data): dict` - Retrieve templates by tags
- `create_circular_templates_info(templates_info, number): list` - Create circular template array
- `create_circular_keywords(keyword_with_original_image_url, template_image_count): list` - Generate keyword circles
- `upload_image_to_imagekit(original_image_url, keyword, workspace_id): string` - Upload to ImageKit
- `get_imagekit_urls(keyword, original_image_url, workspace_id): string` - Get ImageKit URLs
- `generate_image(template_file_name): string` - Generate image using Node.js
- `process_template(template, keyword_with_original_image_url, used_orignal_image_url, workspace_id): string` - Process template
- `process_template_done(generated_images): callable` - Callback for completed processing

**Key Features**:
- Template-based image generation
- ImageKit cloud storage integration
- Node.js script execution
- Multiprocessing support
- Circular array processing for scalability

#### AIProvider
**Purpose**: Integrates with AI services (Novita/Deepseek) for content analysis.

**Attributes**:
- `api_key: string` - AI service API key
- `api_url: string` - AI service endpoint
- `model: string` - AI model identifier
- `client: OpenAI` - OpenAI client instance

**Methods**:
- `__init__()` - Initialize AI provider with configuration
- `extract_selectors(html_content, domain): dict` - Extract CSS selectors from HTML
- `_get_fallback_selectors(): dict` - Provide fallback selectors when AI fails

**Key Features**:
- HTML content analysis
- CSS selector extraction
- Competitor content parsing
- Fallback mechanism for reliability
- JSON-structured responses

### 3. Utility Classes

#### Handler
**Purpose**: Custom logging handler for database-backed activity logging.

**Methods**:
- `__init__()` - Initialize Loguru logger with custom handler
- `log_to_database(message): void` - Write log entries to database

**Key Features**:
- Loguru integration
- Database activity logging
- Notification creation
- User role determination
- Workspace and domain tracking

### 4. Configuration Classes

#### ApiappConfig
**Purpose**: Django app configuration for the main API application.

**Attributes**:
- `default_auto_field: string` - Default auto field type
- `name: string` - App name

**Methods**:
- `ready(): void` - App initialization hook

#### FrontendappConfig
**Purpose**: Django app configuration for the frontend application.

**Attributes**:
- `default_auto_field: string` - Default auto field type  
- `name: string` - App name

**Methods**:
- `ready(): void` - App initialization hook

## Key Function-Based Views

While this project primarily uses function-based views, here are the main view functions:

### API Views (using @api_view decorator):
- `admin_login()` - User authentication
- `list_article()` - Article listing with pagination
- `add_competitor()` - Competitor domain addition
- `list_ai_message()` - AI message management
- `generate_single_image()` - Image generation endpoint

### Frontend Views:
- `login_page()` - Login page rendering
- `registration_enter_otp_page()` - OTP verification page

## Relationships and Dependencies

1. **Middleware Chain**: AccessControlMiddleware → RateLimitMiddleware → ActivityLogMiddleware
2. **Logging Pipeline**: ActivityLogMiddleware → Handler → Database
3. **AI Processing**: ImageGenerator → AIProvider for intelligent processing
4. **Authentication Flow**: AccessControlMiddleware → JWT/API Key validation
5. **Image Processing**: ImageGenerator → ImageKit → Node.js scripts

## Design Patterns

### 1. Middleware Pattern
All middleware classes follow Django's middleware pattern with `__call__` methods for request/response processing.

### 2. Service Layer Pattern  
ImageGenerator and AIProvider act as service layers abstracting complex business logic.

### 3. Static Factory Pattern
ImageGenerator uses static methods for template and keyword processing.

### 4. Strategy Pattern
AIProvider implements fallback strategies when AI services fail.

### 5. Observer Pattern
Handler class observes log events and creates database records.

## Integration Points

### External Services:
- **ImageKit**: Cloud image storage and transformation
- **OpenAI/Novita**: AI content analysis  
- **Node.js**: Image generation scripts
- **Redis Cache**: Rate limiting storage
- **JWT**: Token-based authentication

### Django Integration:
- **Middleware**: Custom middleware for cross-cutting concerns
- **Apps**: Modular app configuration
- **Logging**: Custom database logging with Loguru
- **DRF**: Function-based API views with decorators

This architecture demonstrates a hybrid approach where Django's class-based components handle infrastructure concerns (middleware, configuration, services) while business logic is implemented through function-based views for simplicity and clarity.
