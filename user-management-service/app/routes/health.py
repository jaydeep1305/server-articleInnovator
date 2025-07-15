"""
Health check routes for service monitoring and deployment.

This module provides health check endpoints for monitoring service status,
database connectivity, and overall system health. Essential for microservice
deployments with load balancers and orchestration systems.

Author: AI Assistant
Date: 2024
"""

import logging
from datetime import datetime
from typing import Dict, Any
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text

from app import db

logger = logging.getLogger(__name__)

# Create health blueprint
health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for load balancers and monitoring.
    
    This endpoint provides a quick health status check without heavy
    database operations. Used by load balancers for traffic routing.
    
    Returns:
        JSON response with basic health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "user-management-service",
            "version": "1.0.0",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    """
    try:
        return jsonify({
            "status": "healthy",
            "service": current_app.config.get('SERVICE_NAME', 'user-management-service'),
            "version": current_app.config.get('SERVICE_VERSION', '1.0.0'),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 200
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": "Internal service error",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 503


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes and container orchestration.
    
    This endpoint performs deeper health checks including database connectivity
    to determine if the service is ready to accept traffic. Used by Kubernetes
    for readiness probes.
    
    Returns:
        JSON response with detailed readiness status
        
    Example Response:
        {
            "status": "ready",
            "checks": {
                "database": "healthy",
                "configuration": "healthy"
            },
            "service": "user-management-service",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    """
    checks = {}
    overall_status = "ready"
    status_code = 200
    
    try:
        # Database connectivity check
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            checks["database"] = "healthy"
            logger.debug("Database health check passed")
        except Exception as db_error:
            checks["database"] = f"unhealthy: {str(db_error)}"
            overall_status = "not_ready"
            status_code = 503
            logger.error(f"Database health check failed: {db_error}")
        
        # Configuration check
        try:
            required_configs = ['SECRET_KEY', 'SERVICE_NAME']
            missing_configs = [config for config in required_configs 
                             if not current_app.config.get(config)]
            
            if missing_configs:
                checks["configuration"] = f"missing: {', '.join(missing_configs)}"
                overall_status = "not_ready"
                status_code = 503
            else:
                checks["configuration"] = "healthy"
                logger.debug("Configuration health check passed")
                
        except Exception as config_error:
            checks["configuration"] = f"error: {str(config_error)}"
            overall_status = "not_ready"
            status_code = 503
            logger.error(f"Configuration health check failed: {config_error}")
        
        # Memory and resource checks could be added here
        # checks["memory"] = "healthy"
        # checks["disk_space"] = "healthy"
        
        return jsonify({
            "status": overall_status,
            "checks": checks,
            "service": current_app.config.get('SERVICE_NAME', 'user-management-service'),
            "version": current_app.config.get('SERVICE_VERSION', '1.0.0'),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), status_code
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            "status": "not_ready",
            "error": "Service readiness check failed",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint for Kubernetes and container orchestration.
    
    This endpoint provides a simple liveness check to determine if the
    service process is still running and responsive. Used by Kubernetes
    for liveness probes to restart containers if needed.
    
    Returns:
        JSON response with liveness status
        
    Example Response:
        {
            "status": "alive",
            "service": "user-management-service",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    """
    try:
        return jsonify({
            "status": "alive",
            "service": current_app.config.get('SERVICE_NAME', 'user-management-service'),
            "uptime_seconds": _get_uptime_seconds(),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify({
            "status": "dead",
            "error": "Service liveness check failed",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 503


@health_bp.route('/health/metrics', methods=['GET'])
def metrics_endpoint() -> Dict[str, Any]:
    """
    Service metrics endpoint for monitoring and observability.
    
    This endpoint provides basic service metrics that can be consumed
    by monitoring systems like Prometheus, Grafana, or custom dashboards.
    
    Returns:
        JSON response with service metrics
        
    Example Response:
        {
            "metrics": {
                "uptime_seconds": 3600,
                "memory_usage_mb": 128,
                "active_connections": 5,
                "total_requests": 1000,
                "database_connections": 10
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
    """
    try:
        metrics = {}
        
        # Basic service metrics
        metrics["uptime_seconds"] = _get_uptime_seconds()
        metrics["service_version"] = current_app.config.get('SERVICE_VERSION', '1.0.0')
        
        # Database connection pool metrics
        try:
            pool = db.engine.pool
            metrics["database_pool_size"] = pool.size()
            metrics["database_pool_checked_in"] = pool.checkedin()
            metrics["database_pool_checked_out"] = pool.checkedout()
            metrics["database_pool_overflow"] = pool.overflow()
        except Exception as pool_error:
            logger.warning(f"Could not retrieve database pool metrics: {pool_error}")
            metrics["database_pool_error"] = str(pool_error)
        
        # Memory metrics (basic approximation)
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            metrics["memory_rss_mb"] = round(memory_info.rss / 1024 / 1024, 2)
            metrics["memory_vms_mb"] = round(memory_info.vms / 1024 / 1024, 2)
            metrics["cpu_percent"] = process.cpu_percent()
        except ImportError:
            # psutil not available, skip memory metrics
            logger.debug("psutil not available, skipping memory metrics")
        except Exception as memory_error:
            logger.warning(f"Could not retrieve memory metrics: {memory_error}")
        
        # Flask application metrics
        if hasattr(current_app, 'request_count'):
            metrics["total_requests"] = getattr(current_app, 'request_count', 0)
        
        return jsonify({
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return jsonify({
            "error": "Failed to retrieve metrics",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }), 500


def _get_uptime_seconds() -> float:
    """
    Calculate service uptime in seconds.
    
    This is a simple approximation based on when the Flask app was created.
    For production, consider using a more sophisticated approach with
    persistent storage or process start time tracking.
    
    Returns:
        float: Uptime in seconds
    """
    try:
        if hasattr(current_app, 'start_time'):
            return (datetime.utcnow() - current_app.start_time).total_seconds()
        else:
            # Fallback: assume service just started
            return 0.0
    except Exception:
        return 0.0


# Error handlers for health blueprint
@health_bp.errorhandler(404)
def health_not_found(error):
    """Handle 404 errors in health blueprint."""
    return jsonify({
        "error": "Health endpoint not found",
        "available_endpoints": [
            "/health",
            "/health/ready", 
            "/health/live",
            "/health/metrics"
        ],
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }), 404


@health_bp.errorhandler(405)
def health_method_not_allowed(error):
    """Handle 405 errors in health blueprint."""
    return jsonify({
        "error": "Method not allowed",
        "allowed_methods": ["GET"],
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }), 405


@health_bp.errorhandler(500)
def health_internal_error(error):
    """Handle 500 errors in health blueprint."""
    logger.error(f"Internal error in health endpoint: {error}")
    return jsonify({
        "error": "Internal server error in health check",
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }), 500