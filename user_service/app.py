"""
Main Application Entry Point for User Management Microservice.

This module creates and configures the Flask application instance
and serves as the entry point for the microservice.
"""

from app import create_app
import os

# Create the Flask application
app = create_app(environment=os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run the application
    app.run(host=host, port=port, debug=debug)