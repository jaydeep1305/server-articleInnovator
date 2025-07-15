"""
Error Handlers for User Management Microservice.

This module provides comprehensive error handling for Flask applications
with consistent JSON responses and proper HTTP status codes.
"""

from typing import Tuple, Dict, Any
from flask import jsonify, request, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import traceback


def create_error_response(message: str, status_code: int, 
                         details: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized error response.
    
    Args:
        message: Error message to display
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    error_response = {
        'error': True,
        'message': message,
        'status_code': status_code,
        'timestamp': current_app.json.datetime_now().isoformat() if hasattr(current_app, 'json') else None,
        'path': request.path if request else None
    }
    
    if details:
        error_response['details'] = details
    
    # Add request ID if available (useful for tracing)
    if hasattr(request, 'id'):
        error_response['request_id'] = request.id
    
    return error_response, status_code


def handle_bad_request(error: HTTPException) -> Tuple[Dict[str, Any], int]:
    """
    Handle 400 Bad Request errors.
    
    Args:
        error: HTTPException instance
        
    Returns:
        JSON error response with 400 status code
    """
    message = "Bad request. Please check your input data."
    
    if hasattr(error, 'description') and error.description:
        message = error.description
    
    details = {
        'error_type': 'BadRequest',
        'suggestion': 'Verify that all required fields are provided and properly formatted.'
    }
    
    current_app.logger.warning(f"Bad request: {message} - Path: {request.path}")
    
    return create_error_response(message, 400, details)


def handle_not_found_error(error: HTTPException) -> Tuple[Dict[str, Any], int]:
    """
    Handle 404 Not Found errors.
    
    Args:
        error: HTTPException instance
        
    Returns:
        JSON error response with 404 status code
    """
    message = "The requested resource was not found."
    
    if hasattr(error, 'description') and error.description:
        message = error.description
    
    details = {
        'error_type': 'NotFound',
        'suggestion': 'Check the URL and ensure the resource exists.'
    }
    
    current_app.logger.info(f"Resource not found: {request.path}")
    
    return create_error_response(message, 404, details)


def handle_validation_error(error: HTTPException) -> Tuple[Dict[str, Any], int]:
    """
    Handle 422 Unprocessable Entity (validation) errors.
    
    Args:
        error: HTTPException instance
        
    Returns:
        JSON error response with 422 status code
    """
    message = "Validation failed. Please check your input data."
    
    if hasattr(error, 'description') and error.description:
        message = error.description
    
    details = {
        'error_type': 'ValidationError',
        'suggestion': 'Review the input data format and ensure all validation rules are met.'
    }
    
    # Extract validation details if available
    if hasattr(error, 'data') and error.data:
        details['validation_errors'] = error.data
    
    current_app.logger.warning(f"Validation error: {message} - Path: {request.path}")
    
    return create_error_response(message, 422, details)


def handle_unauthorized_error(error: HTTPException) -> Tuple[Dict[str, Any], int]:
    """
    Handle 401 Unauthorized errors.
    
    Args:
        error: HTTPException instance
        
    Returns:
        JSON error response with 401 status code
    """
    message = "Authentication required. Please provide valid credentials."
    
    if hasattr(error, 'description') and error.description:
        message = error.description
    
    details = {
        'error_type': 'Unauthorized',
        'suggestion': 'Provide valid authentication credentials in the request.'
    }
    
    current_app.logger.warning(f"Unauthorized access attempt: {request.path}")
    
    return create_error_response(message, 401, details)


def handle_forbidden_error(error: HTTPException) -> Tuple[Dict[str, Any], int]:
    """
    Handle 403 Forbidden errors.
    
    Args:
        error: HTTPException instance
        
    Returns:
        JSON error response with 403 status code
    """
    message = "Access forbidden. You don't have permission to access this resource."
    
    if hasattr(error, 'description') and error.description:
        message = error.description
    
    details = {
        'error_type': 'Forbidden',
        'suggestion': 'Contact your administrator to request appropriate permissions.'
    }
    
    current_app.logger.warning(f"Forbidden access attempt: {request.path}")
    
    return create_error_response(message, 403, details)


def handle_method_not_allowed(error: HTTPException) -> Tuple[Dict[str, Any], int]:
    """
    Handle 405 Method Not Allowed errors.
    
    Args:
        error: HTTPException instance
        
    Returns:
        JSON error response with 405 status code
    """
    message = f"Method {request.method} not allowed for this endpoint."
    
    allowed_methods = []
    if hasattr(error, 'valid_methods'):
        allowed_methods = list(error.valid_methods)
    
    details = {
        'error_type': 'MethodNotAllowed',
        'allowed_methods': allowed_methods,
        'suggestion': f'Use one of the allowed methods: {", ".join(allowed_methods)}'
    }
    
    current_app.logger.warning(f"Method not allowed: {request.method} {request.path}")
    
    return create_error_response(message, 405, details)


def handle_internal_error(error: Exception) -> Tuple[Dict[str, Any], int]:
    """
    Handle 500 Internal Server errors.
    
    Args:
        error: Exception instance
        
    Returns:
        JSON error response with 500 status code
    """
    message = "An internal server error occurred. Please try again later."
    
    details = {
        'error_type': 'InternalServerError',
        'suggestion': 'If the problem persists, please contact support.'
    }
    
    # Log the full error for debugging
    current_app.logger.error(f"Internal server error: {str(error)}")
    current_app.logger.error(f"Traceback: {traceback.format_exc()}")
    
    # In development, include error details
    if current_app.debug:
        details['debug_info'] = {
            'error_message': str(error),
            'error_type': type(error).__name__
        }
    
    return create_error_response(message, 500, details)


def handle_database_error(error: SQLAlchemyError) -> Tuple[Dict[str, Any], int]:
    """
    Handle database-related errors.
    
    Args:
        error: SQLAlchemyError instance
        
    Returns:
        JSON error response with 500 status code
    """
    message = "A database error occurred. Please try again later."
    
    details = {
        'error_type': 'DatabaseError',
        'suggestion': 'If the problem persists, please contact support.'
    }
    
    # Log the database error
    current_app.logger.error(f"Database error: {str(error)}")
    
    # In development, include more details
    if current_app.debug:
        details['debug_info'] = {
            'error_message': str(error),
            'error_type': type(error).__name__
        }
    
    return create_error_response(message, 500, details)


def handle_rate_limit_exceeded(error: Exception) -> Tuple[Dict[str, Any], int]:
    """
    Handle 429 Too Many Requests errors.
    
    Args:
        error: Exception instance
        
    Returns:
        JSON error response with 429 status code
    """
    message = "Rate limit exceeded. Please try again later."
    
    details = {
        'error_type': 'RateLimitExceeded',
        'suggestion': 'Wait before making additional requests.'
    }
    
    # Add rate limit info if available
    if hasattr(error, 'retry_after'):
        details['retry_after'] = error.retry_after
    
    current_app.logger.warning(f"Rate limit exceeded for {request.remote_addr}")
    
    return create_error_response(message, 429, details)


def register_error_handlers(app):
    """
    Register all error handlers with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request_handler(error):
        response, status_code = handle_bad_request(error)
        return jsonify(response), status_code
    
    @app.errorhandler(401)
    def unauthorized_handler(error):
        response, status_code = handle_unauthorized_error(error)
        return jsonify(response), status_code
    
    @app.errorhandler(403)
    def forbidden_handler(error):
        response, status_code = handle_forbidden_error(error)
        return jsonify(response), status_code
    
    @app.errorhandler(404)
    def not_found_handler(error):
        response, status_code = handle_not_found_error(error)
        return jsonify(response), status_code
    
    @app.errorhandler(405)
    def method_not_allowed_handler(error):
        response, status_code = handle_method_not_allowed(error)
        return jsonify(response), status_code
    
    @app.errorhandler(422)
    def validation_error_handler(error):
        response, status_code = handle_validation_error(error)
        return jsonify(response), status_code
    
    @app.errorhandler(429)
    def rate_limit_handler(error):
        response, status_code = handle_rate_limit_exceeded(error)
        return jsonify(response), status_code
    
    @app.errorhandler(500)
    def internal_error_handler(error):
        response, status_code = handle_internal_error(error)
        return jsonify(response), status_code
    
    @app.errorhandler(SQLAlchemyError)
    def database_error_handler(error):
        response, status_code = handle_database_error(error)
        return jsonify(response), status_code