"""
Decorators for User Management Microservice.

This module provides decorators for authentication, authorization,
rate limiting, and other cross-cutting concerns.
"""

from typing import List, Optional, Callable
from functools import wraps
from flask import request, jsonify, current_app, g
import time
from collections import defaultdict, deque


# Simple in-memory rate limiting storage (use Redis in production)
rate_limit_storage = defaultdict(lambda: deque())


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for a route.
    
    This is a simplified example. In production, you would integrate
    with JWT, OAuth, or your chosen authentication system.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
        
    Example:
        @require_auth
        def protected_route():
            return jsonify({'message': 'Access granted'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': True,
                'message': 'Authorization header is required',
                'status_code': 401
            }), 401
        
        # Extract token from "Bearer <token>" format
        try:
            scheme, token = auth_header.split(' ', 1)
            if scheme.lower() != 'bearer':
                raise ValueError("Invalid authorization scheme")
        except ValueError:
            return jsonify({
                'error': True,
                'message': 'Authorization header must be in format: Bearer <token>',
                'status_code': 401
            }), 401
        
        # In production, validate the JWT token here
        # For this example, we'll use a simple token validation
        if not token or len(token) < 10:
            return jsonify({
                'error': True,
                'message': 'Invalid authentication token',
                'status_code': 401
            }), 401
        
        # Store user information in Flask's g object for use in the route
        # In production, this would come from JWT payload or database lookup
        g.current_user_id = 1  # Placeholder - extract from validated token
        g.current_user_username = 'authenticated_user'  # Placeholder
        
        return f(*args, **kwargs)
    return decorated_function


def require_permission(permission: str) -> Callable:
    """
    Decorator to require a specific permission for a route.
    
    Args:
        permission: Required permission (e.g., 'user:read', 'admin:delete')
        
    Returns:
        Decorator function
        
    Example:
        @require_permission('user:create')
        def create_user():
            return jsonify({'message': 'User created'})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'current_user_id'):
                return jsonify({
                    'error': True,
                    'message': 'Authentication required',
                    'status_code': 401
                }), 401
            
            # In production, check user permissions from database or cache
            # For this example, we'll use a simple permission check
            user_permissions = _get_user_permissions(g.current_user_id)
            
            if permission not in user_permissions:
                return jsonify({
                    'error': True,
                    'message': f'Permission denied. Required permission: {permission}',
                    'status_code': 403,
                    'details': {
                        'required_permission': permission,
                        'user_permissions': user_permissions
                    }
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_roles(roles: List[str], require_all: bool = False) -> Callable:
    """
    Decorator to require specific roles for a route.
    
    Args:
        roles: List of required role names
        require_all: If True, user must have ALL roles. If False, ANY role is sufficient.
        
    Returns:
        Decorator function
        
    Example:
        @require_roles(['admin', 'moderator'])
        def admin_only_route():
            return jsonify({'message': 'Admin access granted'})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'current_user_id'):
                return jsonify({
                    'error': True,
                    'message': 'Authentication required',
                    'status_code': 401
                }), 401
            
            # Get user roles
            user_roles = _get_user_roles(g.current_user_id)
            
            # Check role requirements
            if require_all:
                # User must have ALL required roles
                if not all(role in user_roles for role in roles):
                    missing_roles = [role for role in roles if role not in user_roles]
                    return jsonify({
                        'error': True,
                        'message': f'Missing required roles: {", ".join(missing_roles)}',
                        'status_code': 403,
                        'details': {
                            'required_roles': roles,
                            'missing_roles': missing_roles,
                            'user_roles': user_roles
                        }
                    }), 403
            else:
                # User must have ANY of the required roles
                if not any(role in user_roles for role in roles):
                    return jsonify({
                        'error': True,
                        'message': f'Access denied. Required roles: {", ".join(roles)}',
                        'status_code': 403,
                        'details': {
                            'required_roles': roles,
                            'user_roles': user_roles
                        }
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit(requests_per_minute: int = 60, 
               per_user: bool = True) -> Callable:
    """
    Decorator to implement rate limiting.
    
    Args:
        requests_per_minute: Maximum requests allowed per minute
        per_user: If True, limit per user. If False, limit per IP.
        
    Returns:
        Decorator function
        
    Example:
        @rate_limit(requests_per_minute=30)
        def api_endpoint():
            return jsonify({'data': 'response'})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine rate limit key
            if per_user and hasattr(g, 'current_user_id'):
                limit_key = f"user:{g.current_user_id}"
            else:
                limit_key = f"ip:{request.remote_addr}"
            
            current_time = time.time()
            window_start = current_time - 60  # 60 seconds window
            
            # Get request history for this key
            request_history = rate_limit_storage[limit_key]
            
            # Remove old requests outside the time window
            while request_history and request_history[0] < window_start:
                request_history.popleft()
            
            # Check if rate limit is exceeded
            if len(request_history) >= requests_per_minute:
                return jsonify({
                    'error': True,
                    'message': 'Rate limit exceeded',
                    'status_code': 429,
                    'details': {
                        'limit': requests_per_minute,
                        'window': '1 minute',
                        'retry_after': 60 - (current_time - request_history[0])
                    }
                }), 429
            
            # Add current request to history
            request_history.append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_activity(activity_type: str, include_request_data: bool = False) -> Callable:
    """
    Decorator to log user activity.
    
    Args:
        activity_type: Type of activity being logged
        include_request_data: Whether to include request data in log
        
    Returns:
        Decorator function
        
    Example:
        @log_activity('user_login', include_request_data=True)
        def login():
            return jsonify({'status': 'success'})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Execute the function
            try:
                result = f(*args, **kwargs)
                success = True
                error_message = None
            except Exception as e:
                result = jsonify({
                    'error': True,
                    'message': 'An error occurred',
                    'status_code': 500
                }), 500
                success = False
                error_message = str(e)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Prepare log data
            log_data = {
                'activity_type': activity_type,
                'user_id': getattr(g, 'current_user_id', None),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'method': request.method,
                'endpoint': request.endpoint,
                'path': request.path,
                'duration_seconds': round(duration, 3),
                'success': success,
                'timestamp': time.time()
            }
            
            if error_message:
                log_data['error_message'] = error_message
            
            if include_request_data:
                log_data['request_data'] = {
                    'args': dict(request.args),
                    'json': request.get_json(silent=True),
                    'form': dict(request.form)
                }
            
            # Log the activity
            current_app.logger.info(f"Activity logged: {activity_type}", extra=log_data)
            
            return result
        return decorated_function
    return decorator


def cache_response(timeout_seconds: int = 300) -> Callable:
    """
    Decorator to cache response data.
    
    Note: This is a simplified example. In production, use Redis or Memcached.
    
    Args:
        timeout_seconds: Cache timeout in seconds
        
    Returns:
        Decorator function
        
    Example:
        @cache_response(timeout_seconds=600)
        def get_user_stats():
            return jsonify({'stats': 'data'})
    """
    cache_storage = {}
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{hash(str(args) + str(kwargs))}"
            current_time = time.time()
            
            # Check if cached response exists and is still valid
            if cache_key in cache_storage:
                cached_data, timestamp = cache_storage[cache_key]
                if current_time - timestamp < timeout_seconds:
                    current_app.logger.debug(f"Cache hit for {cache_key}")
                    return cached_data
                else:
                    # Remove expired cache entry
                    del cache_storage[cache_key]
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache_storage[cache_key] = (result, current_time)
            current_app.logger.debug(f"Cache miss for {cache_key} - result cached")
            
            return result
        return decorated_function
    return decorator


def _get_user_permissions(user_id: int) -> List[str]:
    """
    Get user permissions from database or cache.
    
    This is a placeholder implementation. In production, this would
    query the database or cache to get the user's actual permissions.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of permission names
    """
    # Placeholder - in production, query from UserService
    return ['user:read', 'user:update', 'profile:read', 'profile:update']


def _get_user_roles(user_id: int) -> List[str]:
    """
    Get user roles from database or cache.
    
    This is a placeholder implementation. In production, this would
    query the database or cache to get the user's actual roles.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of role names
    """
    # Placeholder - in production, query from UserService
    return ['user']