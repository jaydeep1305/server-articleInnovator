"""
Health check endpoints for Monitoring Service.

This module provides health check endpoints for monitoring service status,
database connectivity, and external service dependencies.

Author: AI Assistant
Date: 2024
"""

import time
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from app import db

# Create blueprint
health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        JSON response with service status
    """
    return jsonify({
        'status': 'healthy',
        'service': current_app.config.get('SERVICE_NAME', 'monitoring-service'),
        'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the service is ready to receive traffic.
    This includes database connectivity and other critical dependencies.
    
    Returns:
        JSON response with readiness status
    """
    checks = {
        'database': False,
        'overall': False
    }
    
    start_time = time.time()
    
    try:
        # Check database connectivity
        db.session.execute(text('SELECT 1'))
        checks['database'] = True
        
        # Overall status
        checks['overall'] = all(checks.values())
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        response_data = {
            'status': 'ready' if checks['overall'] else 'not_ready',
            'service': current_app.config.get('SERVICE_NAME', 'monitoring-service'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'checks': checks,
            'response_time_ms': response_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        status_code = 200 if checks['overall'] else 503
        return jsonify(response_data), status_code
        
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {e}")
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return jsonify({
            'status': 'not_ready',
            'service': current_app.config.get('SERVICE_NAME', 'monitoring-service'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'checks': checks,
            'error': str(e),
            'response_time_ms': response_time,
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Checks if the service is alive and should be restarted if not.
    This is a basic check that the Flask application is responding.
    
    Returns:
        JSON response with liveness status
    """
    return jsonify({
        'status': 'alive',
        'service': current_app.config.get('SERVICE_NAME', 'monitoring-service'),
        'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@health_bp.route('/health/metrics', methods=['GET'])
def metrics():
    """
    Basic metrics endpoint for monitoring.
    
    Returns:
        JSON response with service metrics
    """
    try:
        # Get database connection pool info
        pool_info = {}
        if hasattr(db.engine.pool, 'size'):
            pool_info = {
                'pool_size': db.engine.pool.size(),
                'checked_in': db.engine.pool.checkedin(),
                'checked_out': db.engine.pool.checkedout(),
                'overflow': db.engine.pool.overflow(),
                'invalid': db.engine.pool.invalid()
            }
        
        return jsonify({
            'service': current_app.config.get('SERVICE_NAME', 'monitoring-service'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'metrics': {
                'database_pool': pool_info,
                'config': {
                    'debug': current_app.debug,
                    'testing': current_app.testing
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Metrics collection failed: {e}")
        
        return jsonify({
            'service': current_app.config.get('SERVICE_NAME', 'monitoring-service'),
            'version': current_app.config.get('SERVICE_VERSION', '1.0.0'),
            'error': 'Failed to collect metrics',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
