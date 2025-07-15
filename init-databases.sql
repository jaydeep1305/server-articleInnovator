-- Initialize databases for all microservices
-- This script creates separate databases for each service to ensure data isolation

-- Core Services
CREATE DATABASE user_management_dev;
CREATE DATABASE workspace_management_dev;  
CREATE DATABASE article_management_dev;

-- Domain-Specific Services
CREATE DATABASE domain_management_dev;
CREATE DATABASE ai_configuration_dev;
CREATE DATABASE image_generation_dev;

-- Infrastructure Services
CREATE DATABASE monitoring_dev;
CREATE DATABASE notifications_dev;
CREATE DATABASE logging_dev;
CREATE DATABASE configuration_dev;

-- External Services
CREATE DATABASE scraping_dev;
CREATE DATABASE ai_rate_limiter_dev;

-- Create users and grant permissions for each service (optional, for production)
-- For development, we'll use the postgres superuser

-- Grant permissions to postgres user (development only)
GRANT ALL PRIVILEGES ON DATABASE user_management_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE workspace_management_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE article_management_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE domain_management_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE ai_configuration_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE image_generation_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE monitoring_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE notifications_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE logging_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE configuration_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE scraping_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE ai_rate_limiter_dev TO postgres;