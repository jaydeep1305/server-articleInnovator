"""
Main application entry point for User Management Service.

This module serves as the entry point for running the Flask microservice
with proper configuration, logging setup, and graceful error handling.
It provides both development and production-ready startup patterns.

Author: AI Assistant
Date: 2024
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, register_cli_commands
from config import get_config, setup_logging

logger = logging.getLogger(__name__)


def create_application(config_name: Optional[str] = None):
    """
    Create and configure Flask application instance.
    
    This function implements the application factory pattern with
    proper configuration loading, logging setup, and error handling.
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Flask application instance
    """
    try:
        # Get configuration
        config = get_config(config_name)
        
        # Setup logging
        setup_logging(config)
        
        # Create Flask application
        app = create_app(config_name)
        
        # Register CLI commands
        register_cli_commands(app)
        
        # Set start time for uptime calculations
        app.start_time = datetime.utcnow()
        
        logger.info(f"Application created successfully with config: {config_name or 'auto-detected'}")
        return app
        
    except Exception as e:
        print(f"Failed to create application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    """
    Main entry point for running the application.
    
    This section handles command-line execution with environment-based
    configuration and proper error handling for production deployment.
    """
    
    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    try:
        # Create application
        app = create_application(config_name)
        
        # Get runtime configuration
        host = os.environ.get('HOST', '127.0.0.1')
        port = int(os.environ.get('PORT', '5000'))
        debug = config_name == 'development'
        
        # Log startup information
        logger.info(f"Starting {app.config['SERVICE_NAME']} v{app.config['SERVICE_VERSION']}")
        logger.info(f"Environment: {config_name}")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Debug: {debug}")
        
        # Start the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)