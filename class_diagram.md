# Article Innovator - Class Diagram

This document presents a comprehensive class diagram for the Article Innovator Django project.

## Project Overview

The Article Innovator is a Django-based content management system with the following main applications:
- **apiApp**: Core API and data models
- **competitorApp**: Competitor analysis functionality  
- **AIMessageService**: AI message processing
- **frontendApp**: Frontend application (minimal models)
- **articleInnovator**: Main Django project configuration

## Key Model Classes by Application

### apiApp (Core Application)

#### User Management & Authorization
- **User** (Django built-in): Standard Django user model
- **user_detail**: Extended user profiles with role assignments, limitations, and workspace memberships
- **role**: User role definitions (admin, writer, manager, etc.)
- **permission**: System permission definitions
- **role_has_permissions**: Many-to-many mapping between roles and permissions
- **invitation_code_detail**: Invitation system for user registration
- **user_api_key**: API key management for users

#### Workspace & Configuration
- **workspace**: Multi-tenant workspace management
- **ai_configuration**: AI service configuration (OpenAI, etc.)
- **image_kit_configuration**: Image processing service configuration

#### Domain & WordPress Management
- **domain**: WordPress site/domain management with authentication
- **wp_tag**: WordPress tag management (AI or WordPress derived)
- **wp_category**: WordPress category management with default selection
- **wp_author**: WordPress author management with profiles

#### Article System
- **article**: Core article model with WordPress integration
- **article_type**: Article type definitions (keyword, URL, manual)
- **article_type_field**: Dynamic field definitions for article types
- **article_info**: Article analytics and statistics
- **prompt**: AI prompt configurations for content generation
- **supportive_prompt**: Supporting prompt templates
- **supportive_prompt_type**: Categories of supportive prompts
- **variables**: Dynamic variables for prompt templates
- **internal_links**: Internal link management
- **external_links**: External link management

#### System Management
- **notification**: User notification system
- **activity_log**: Comprehensive system activity logging
- **motivation**: Motivational quotes system
- **language**: Language configuration
- **country**: Country/region management
- **color_detail**: UI color theme management
- **rabbitmq_queue**: Message queue management
- **keyword**: Keyword research and management

#### Analytics & Metrics
- **console_metrics**: Google Search Console metrics
- **analytics_metrics**: Google Analytics data
- **domain_install_log**: Domain installation tracking
- **domain_install_log_percentage**: Installation progress tracking

#### Integration Management
- **integration_type**: Third-party integration types
- **integration**: Integration configurations and credentials

#### Image Management
- **image_tag**: Image categorization tags
- **image_template_category**: Template categorization
- **image_template**: Image template storage
- **image_tag_template_category_template_mapping**: Complex mapping relationships

### competitorApp (Competitor Analysis)

#### Core Competitor Models
- **competitor**: Competitor domain definitions
- **competitor_domain_mapping**: Domain monitoring configuration with intervals and settings

#### URL Monitoring
- **competitor_selected_url**: URLs being actively monitored
- **competitor_article_url**: Articles discovered from competitors

#### Content Extraction
- **category_url_selector**: CSS selectors for category page extraction
- **article_url_selector**: Comprehensive content extraction configuration
- **competitor_selector_prompt**: AI prompts for competitor content processing

#### Analytics
- **competitor_url_daily_stats**: Daily performance metrics with success rates and timing

### AIMessageService (AI Processing)

#### Message Management
- **ai_message**: AI communication messages with request/response tracking
- **input_json**: AI input data storage for processing

### frontendApp
- No significant models (minimal Django app for frontend)

## Key Relationships

### Primary Relationships
1. **User-Workspace**: Many-to-many through user_detail for multi-tenant access
2. **Workspace-Domain**: One-to-many for multi-site management
3. **Domain-WordPress Entities**: One-to-many for tags, categories, authors
4. **Article-Content**: Complex many-to-many relationships with categories, tags
5. **Article-Links**: One-to-many for internal and external links
6. **Competitor-Monitoring**: Hierarchical monitoring structure
7. **AI-Processing**: Message-based processing system

### Secondary Relationships
- **Role-Permission**: Many-to-many through role_has_permissions
- **Article-Analytics**: One-to-one with article_info
- **Prompt-Article**: One-to-many for content generation
- **Workspace-Configuration**: One-to-many for AI and image configurations

## Design Patterns

### 1. UUID-based Identification
All models implement `slug_id` fields using UUID4 for secure, non-sequential identification.

### 2. Audit Trail Pattern
Comprehensive tracking with:
- `created_date` and `updated_date` timestamps
- `created_by` foreign keys to User model
- `status` fields for soft deletion

### 3. Multi-tenancy Pattern
Workspace-based isolation ensuring data separation between tenants.

### 4. Flexible Configuration
Extensive use of JSONField for:
- AI content flags and configurations
- Competitor extraction settings
- Dynamic prompt data
- Integration credentials

### 5. Derived Content Management
`derived_by` fields tracking whether content comes from 'ai' or 'wordpress' sources.

### 6. Default Selection Pattern
`default_section` boolean fields for managing default categories, authors, and configurations.

### 7. Status-based State Management
Multiple status fields for tracking:
- Article status (initiate, success, failed, review)
- WordPress status (publish, draft, future, trash)
- Competitor scraping status (pending, in_progress, completed, failed)

## System Architecture Highlights

### Content Generation Pipeline
1. **Input**: Keywords or URLs through article_type system
2. **Processing**: AI prompt system with supportive prompts
3. **Enhancement**: Link generation and SEO optimization
4. **Publishing**: WordPress integration with scheduling

### Competitor Analysis Pipeline
1. **Discovery**: URL monitoring with configurable intervals
2. **Extraction**: CSS selector-based content extraction
3. **Processing**: AI-powered content analysis
4. **Metrics**: Performance tracking and success rate monitoring

### Multi-tenant Architecture
- Workspace-level isolation
- Role-based access control
- Configurable limitations per user/workspace
- Shared system resources (languages, countries, article types)

This architecture supports a scalable, multi-tenant content management system with advanced AI capabilities and comprehensive competitor analysis features.
