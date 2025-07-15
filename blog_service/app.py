"""
Main application entry point for the Blog Microservice.

This module creates the Flask application and provides the
entry point for running the service.

Usage:
    python app.py              # Run with default configuration
    FLASK_ENV=production python app.py  # Run in production mode
"""

import os
from app import create_app

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host=host, port=port, debug=debug)