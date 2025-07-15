#!/usr/bin/env python3
"""
Configuration Service - Main Application Entry Point

This module serves as the entry point for the Configuration Service.
It handles application initialization, configuration loading, and server startup.

Author: AI Assistant
Date: 2024
"""

import os
import sys
import logging
from flask import Flask

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config, setup_logging
from app import create_app


def main() -> None:
    """
    Main application entry point.
    
    This function initializes the Flask application with the appropriate
    configuration based on the environment and starts the development server.
    """
    try:
        # Load configuration
        config = get_config()
        
        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting {config.SERVICE_NAME} v{config.SERVICE_VERSION}")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        
        # Create Flask application
        app = create_app(config)
        
        # Get port from environment or config
        port = int(os.environ.get('PORT', config.SERVICE_PORT))
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info(f"Starting server on {host}:{port}")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=config.DEBUG,
            threaded=True
        )
        
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
