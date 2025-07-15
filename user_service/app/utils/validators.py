"""
Validation Utilities for User Management Microservice.

This module provides validation functions for request data,
pagination parameters, and common data formats.
"""

from typing import Dict, Any, Optional, List, Tuple
from functools import wraps
from flask import request, jsonify
import re


def validate_json(required_fields: Optional[List[str]] = None,
                 optional_fields: Optional[List[str]] = None) -> callable:
    """
    Decorator to validate JSON request data.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        
    Returns:
        Decorator function
        
    Example:
        @validate_json(required_fields=['username', 'email'])
        def create_user():
            data = request.get_json()
            # data is guaranteed to have username and email
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': True,
                    'message': 'Request must be JSON',
                    'status_code': 400
                }), 400
            
            data = request.get_json()
            if data is None:
                return jsonify({
                    'error': True,
                    'message': 'Invalid JSON data',
                    'status_code': 400
                }), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': True,
                        'message': f'Missing required fields: {", ".join(missing_fields)}',
                        'status_code': 400,
                        'details': {
                            'missing_fields': missing_fields,
                            'required_fields': required_fields
                        }
                    }), 400
            
            # Validate field types and values
            validation_errors = []
            
            # Check for empty required fields
            if required_fields:
                for field in required_fields:
                    value = data.get(field)
                    if value is None or (isinstance(value, str) and not value.strip()):
                        validation_errors.append(f'{field} cannot be empty')
            
            if validation_errors:
                return jsonify({
                    'error': True,
                    'message': 'Validation failed',
                    'status_code': 422,
                    'details': {
                        'validation_errors': validation_errors
                    }
                }), 422
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_pagination(max_per_page: int = 100) -> callable:
    """
    Decorator to validate pagination parameters.
    
    Args:
        max_per_page: Maximum allowed items per page
        
    Returns:
        Decorator function
        
    Example:
        @validate_pagination(max_per_page=50)
        def get_users():
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            if page < 1:
                return jsonify({
                    'error': True,
                    'message': 'Page number must be 1 or greater',
                    'status_code': 400
                }), 400
            
            if per_page < 1:
                return jsonify({
                    'error': True,
                    'message': 'Items per page must be 1 or greater',
                    'status_code': 400
                }), 400
            
            if per_page > max_per_page:
                return jsonify({
                    'error': True,
                    'message': f'Items per page cannot exceed {max_per_page}',
                    'status_code': 400
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not password or not isinstance(password, str):
        errors.append("Password is required")
        return False, errors
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def validate_username(username: str) -> Tuple[bool, List[str]]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not username or not isinstance(username, str):
        errors.append("Username is required")
        return False, errors
    
    username = username.strip()
    
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    
    if len(username) > 50:
        errors.append("Username cannot exceed 50 characters")
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("Username can only contain letters, numbers, and underscores")
    
    return len(errors) == 0, errors


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone number is valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Basic international phone number validation
    phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,18}$'
    return re.match(phone_pattern, phone.strip()) is not None


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url_pattern = r'^https?:\/\/[^\s/$.?#].[^\s]*$'
    return re.match(url_pattern, url, re.IGNORECASE) is not None


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input by stripping whitespace and limiting length.
    
    Args:
        value: String value to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value) if value is not None else ''
    
    sanitized = value.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
    
    return sanitized


def validate_date_range(start_date: str, end_date: str) -> Tuple[bool, List[str]]:
    """
    Validate date range parameters.
    
    Args:
        start_date: Start date string (YYYY-MM-DD format)
        end_date: End date string (YYYY-MM-DD format)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    from datetime import datetime
    
    errors = []
    
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    if start_date and not re.match(date_pattern, start_date):
        errors.append("Start date must be in YYYY-MM-DD format")
    
    if end_date and not re.match(date_pattern, end_date):
        errors.append("End date must be in YYYY-MM-DD format")
    
    if not errors and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start > end:
                errors.append("Start date must be before or equal to end date")
        except ValueError:
            errors.append("Invalid date format")
    
    return len(errors) == 0, errors


def validate_sort_parameters(sort_by: str, valid_fields: List[str], 
                           sort_order: str = 'asc') -> Tuple[bool, List[str]]:
    """
    Validate sorting parameters.
    
    Args:
        sort_by: Field name to sort by
        valid_fields: List of valid field names for sorting
        sort_order: Sort order ('asc' or 'desc')
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if sort_by and sort_by not in valid_fields:
        errors.append(f"Invalid sort field. Valid options: {', '.join(valid_fields)}")
    
    if sort_order.lower() not in ['asc', 'desc']:
        errors.append("Sort order must be 'asc' or 'desc'")
    
    return len(errors) == 0, errors


def validate_search_query(query: str, min_length: int = 2, 
                         max_length: int = 100) -> Tuple[bool, List[str]]:
    """
    Validate search query parameters.
    
    Args:
        query: Search query string
        min_length: Minimum query length
        max_length: Maximum query length
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not query or not isinstance(query, str):
        errors.append("Search query is required")
        return False, errors
    
    query = query.strip()
    
    if len(query) < min_length:
        errors.append(f"Search query must be at least {min_length} characters long")
    
    if len(query) > max_length:
        errors.append(f"Search query cannot exceed {max_length} characters")
    
    return len(errors) == 0, errors