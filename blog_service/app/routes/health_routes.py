"""
Health check routes for the Blog Microservice.

This module provides health check endpoints for monitoring
application status and readiness.

Routes:
    GET /health/live: Liveness probe
    GET /health/ready: Readiness probe
    GET /health/status: Detailed health status
"""

from datetime import datetime
from flask import Blueprint, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError

from app.models.base import db


health_bp = Blueprint('health', __name__)


@health_bp.route('/live', methods=['GET'])
def liveness_probe():
    """
    Liveness probe endpoint.
    
    This endpoint indicates whether the application is running.
    It should return 200 if the application is alive.
    
    Returns:
        JSON response with liveness status
        
    Example:
        GET /health/live
        Response: {"status": "alive", "timestamp": "2023-12-01T10:30:00Z"}
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@health_bp.route('/ready', methods=['GET'])
def readiness_probe():
    """
    Readiness probe endpoint.
    
    This endpoint indicates whether the application is ready to serve traffic.
    It checks database connectivity and other critical dependencies.
    
    Returns:
        JSON response with readiness status
        
    Example:
        GET /health/ready
        Response: {"status": "ready", "checks": {...}, "timestamp": "..."}
    """
    checks = {}
    overall_status = 'ready'
    status_code = 200
    
    # Database connectivity check
    try:
        # Simple query to test database connection
        db.session.execute(db.text('SELECT 1'))
        checks['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except SQLAlchemyError as e:
        checks['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        overall_status = 'not_ready'
        status_code = 503
    except Exception as e:
        checks['database'] = {
            'status': 'unhealthy',
            'message': f'Unexpected database error: {str(e)}'
        }
        overall_status = 'not_ready'
        status_code = 503
    
    # Configuration check
    try:
        required_configs = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI']
        missing_configs = []
        
        for config in required_configs:
            if not current_app.config.get(config):
                missing_configs.append(config)
        
        if missing_configs:
            checks['configuration'] = {
                'status': 'unhealthy',
                'message': f'Missing required configurations: {", ".join(missing_configs)}'
            }
            overall_status = 'not_ready'
            status_code = 503
        else:
            checks['configuration'] = {
                'status': 'healthy',
                'message': 'All required configurations present'
            }
    except Exception as e:
        checks['configuration'] = {
            'status': 'unhealthy',
            'message': f'Configuration check failed: {str(e)}'
        }
        overall_status = 'not_ready'
        status_code = 503
    
    return jsonify({
        'status': overall_status,
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), status_code


@health_bp.route('/status', methods=['GET'])
def health_status():
    """
    Detailed health status endpoint.
    
    This endpoint provides comprehensive health information including
    application version, uptime, and system metrics.
    
    Returns:
        JSON response with detailed health status
        
    Example:
        GET /health/status
        Response: {
            "status": "healthy",
            "version": "1.0.0",
            "environment": "development",
            ...
        }
    """
    import psutil
    import sys
    from datetime import timedelta
    
    try:
        # Basic application info
        app_info = {
            'name': 'Blog Microservice',
            'version': '1.0.0',
            'environment': current_app.config.get('ENV', 'unknown'),
            'debug_mode': current_app.config.get('DEBUG', False),
            'api_version': current_app.config.get('API_VERSION', 'v1')
        }
        
        # System metrics
        system_info = {
            'python_version': sys.version,
            'cpu_usage_percent': psutil.cpu_percent(interval=1),
            'memory_usage': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk_usage': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            }
        }
        
        # Database info
        db_info = {}
        try:
            # Get database connection info
            result = db.session.execute(db.text('SELECT version()'))
            db_version = result.scalar()
            
            # Count records in main tables
            from app.models import User, Article, Comment
            
            user_count = db.session.query(User).count()
            article_count = db.session.query(Article).count()
            comment_count = db.session.query(Comment).count()
            
            db_info = {
                'status': 'connected',
                'version': db_version,
                'connection_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', '').split('@')[-1] if '@' in current_app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'hidden',
                'record_counts': {
                    'users': user_count,
                    'articles': article_count,
                    'comments': comment_count
                }
            }
        except Exception as e:
            db_info = {
                'status': 'error',
                'message': str(e)
            }
        
        # Application uptime (approximation)
        uptime_info = {
            'started_at': datetime.utcnow().isoformat() + 'Z',
            'uptime_seconds': 0  # Would need to track actual start time
        }
        
        overall_status = 'healthy' if db_info.get('status') == 'connected' else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'application': app_info,
            'system': system_info,
            'database': db_info,
            'uptime': uptime_info
        }), 200
        
    except ImportError:
        # If psutil is not available, provide basic info
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'application': {
                'name': 'Blog Microservice',
                'version': '1.0.0',
                'environment': current_app.config.get('ENV', 'unknown')
            },
            'message': 'Limited health information available (psutil not installed)'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Health status check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'message': 'Health status check failed',
            'error': str(e) if current_app.config.get('DEBUG') else 'Internal error'
        }), 500


@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """
    Application metrics endpoint (basic implementation).
    
    This endpoint provides basic application metrics that can be
    consumed by monitoring systems like Prometheus.
    
    Returns:
        Plain text response with metrics in Prometheus format
    """
    try:
        from app.models import User, Article, Comment
        
        # Get basic counts
        user_count = db.session.query(User).count()
        article_count = db.session.query(Article).count()
        comment_count = db.session.query(Comment).count()
        
        # Active users count
        active_users = db.session.query(User).filter(User.is_active == True).count()
        
        # Published articles count
        from app.models.article import ArticleStatus
        published_articles = db.session.query(Article).filter(
            Article.status == ArticleStatus.PUBLISHED
        ).count()
        
        # Approved comments count
        from app.models.comment import CommentStatus
        approved_comments = db.session.query(Comment).filter(
            Comment.status == CommentStatus.APPROVED
        ).count()
        
        metrics_text = f"""# HELP blog_users_total Total number of users
# TYPE blog_users_total counter
blog_users_total {user_count}

# HELP blog_users_active_total Number of active users
# TYPE blog_users_active_total gauge
blog_users_active_total {active_users}

# HELP blog_articles_total Total number of articles
# TYPE blog_articles_total counter
blog_articles_total {article_count}

# HELP blog_articles_published_total Number of published articles
# TYPE blog_articles_published_total gauge
blog_articles_published_total {published_articles}

# HELP blog_comments_total Total number of comments
# TYPE blog_comments_total counter
blog_comments_total {comment_count}

# HELP blog_comments_approved_total Number of approved comments
# TYPE blog_comments_approved_total gauge
blog_comments_approved_total {approved_comments}

# HELP blog_health_status Application health status (1=healthy, 0=unhealthy)
# TYPE blog_health_status gauge
blog_health_status 1
"""
        
        return metrics_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        current_app.logger.error(f"Metrics collection failed: {str(e)}")
        return f"# Error collecting metrics: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}