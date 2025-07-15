"""
User routes for the Blog Microservice.

This module provides RESTful API endpoints for user management
including registration, authentication, and profile operations.

Routes:
    POST /users/register: Register a new user
    POST /users/login: Authenticate user
    GET /users: List users (paginated)
    GET /users/<id>: Get user by ID
    PUT /users/<id>: Update user
    DELETE /users/<id>: Delete user
    GET /users/<id>/profile: Get user profile
    PUT /users/<id>/profile: Update user profile
    POST /users/<id>/activate: Activate user account
    POST /users/<id>/deactivate: Deactivate user account
    GET /users/<id>/statistics: Get user statistics
"""

from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

from app.models.base import db
from app.services import UserService
from app.models import User

user_bp = Blueprint('users', __name__)

# Initialize service
user_service = UserService(db)


def validate_request_json(required_fields: list) -> Dict[str, Any]:
    """
    Validate request JSON and check for required fields.
    
    Args:
        required_fields: List of required field names
        
    Returns:
        Validated JSON data
        
    Raises:
        BadRequest: If JSON is invalid or fields are missing
    """
    if not request.is_json:
        raise BadRequest("Request must be JSON")
    
    data = request.get_json()
    if not data:
        raise BadRequest("Request body cannot be empty")
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")
    
    return data


@user_bp.route('/register', methods=['POST'])
def register_user():
    """
    Register a new user.
    
    Request JSON:
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "first_name": "John",      // optional
            "last_name": "Doe",        // optional
            "bio": "Software developer" // optional
        }
    
    Returns:
        JSON response with created user data or error
        
    Status Codes:
        201: User created successfully
        400: Validation error or user already exists
        422: Data validation failed
        500: Internal server error
    """
    try:
        data = validate_request_json(['username', 'email', 'password'])
        
        # Extract required fields
        username = data['username'].strip()
        email = data['email'].strip()
        password = data['password']
        
        # Extract optional fields
        first_name = data.get('first_name', '').strip() or None
        last_name = data.get('last_name', '').strip() or None
        bio = data.get('bio', '').strip() or None
        
        # Register user
        user = user_service.register(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            bio=bio
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"User registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@user_bp.route('/login', methods=['POST'])
def login_user():
    """
    Authenticate a user.
    
    Request JSON:
        {
            "username": "john_doe",    // or email
            "password": "SecurePass123"
        }
    
    Returns:
        JSON response with user data or error
        
    Status Codes:
        200: Authentication successful
        401: Invalid credentials
        400: Request validation error
        500: Internal server error
    """
    try:
        data = validate_request_json(['username', 'password'])
        
        username = data['username'].strip()
        password = data['password']
        
        # Authenticate user
        user = user_service.authenticate(username, password)
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        return jsonify({
            'message': 'Authentication successful',
            'user': user.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"User authentication failed: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 500


@user_bp.route('', methods=['GET'])
def list_users():
    """
    List users with pagination and filtering.
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
        active_only: Only active users (default: true)
        verified_only: Only verified users (default: false)
        search: Search query for username/email/name
    
    Returns:
        JSON response with paginated users
        
    Status Codes:
        200: Success
        400: Invalid query parameters
        500: Internal server error
    """
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        search_query = request.args.get('search', '').strip() or None
        
        if page < 1:
            return jsonify({'error': 'Page must be >= 1'}), 400
        if per_page < 1:
            return jsonify({'error': 'Per page must be >= 1'}), 400
        
        # Get paginated users
        result = user_service.paginate_users(
            page=page,
            per_page=per_page,
            active_only=active_only,
            verified_only=verified_only,
            search_query=search_query
        )
        
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"List users failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    """
    Get a user by ID.
    
    Path Parameters:
        user_id: User ID
    
    Returns:
        JSON response with user data
        
    Status Codes:
        200: Success
        404: User not found
        500: Internal server error
    """
    try:
        user = user_service.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user'}), 500


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id: int):
    """
    Update a user.
    
    Path Parameters:
        user_id: User ID
    
    Request JSON:
        {
            "first_name": "John",      // optional
            "last_name": "Doe",        // optional
            "bio": "Updated bio",      // optional
            "email": "new@email.com"   // optional
        }
    
    Returns:
        JSON response with updated user data
        
    Status Codes:
        200: Success
        404: User not found
        400: Validation error
        500: Internal server error
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body cannot be empty'}), 400
        
        # Get allowed update fields
        allowed_fields = ['first_name', 'last_name', 'bio', 'email']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update user
        user = user_service.update(user_id, **update_data)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Update user failed: {str(e)}")
        return jsonify({'error': 'Failed to update user'}), 500


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    """
    Delete a user.
    
    Path Parameters:
        user_id: User ID
    
    Returns:
        JSON response with deletion status
        
    Status Codes:
        200: Success
        404: User not found
        500: Internal server error
    """
    try:
        success = user_service.delete(user_id)
        
        if not success:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete user failed: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 500


@user_bp.route('/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id: int):
    """
    Get detailed user profile with statistics.
    
    Path Parameters:
        user_id: User ID
    
    Returns:
        JSON response with user profile and statistics
        
    Status Codes:
        200: Success
        404: User not found
        500: Internal server error
    """
    try:
        user = user_service.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user statistics
        statistics = user_service.get_user_statistics(user_id)
        
        # Get activity summary
        activity = user_service.get_user_activity_summary(user_id, days=30)
        
        profile_data = {
            'user': user.to_dict(),
            'statistics': statistics,
            'activity': activity
        }
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user profile failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user profile'}), 500


@user_bp.route('/<int:user_id>/activate', methods=['POST'])
def activate_user(user_id: int):
    """
    Activate a user account.
    
    Path Parameters:
        user_id: User ID
    
    Returns:
        JSON response with activation status
        
    Status Codes:
        200: Success
        404: User not found
        500: Internal server error
    """
    try:
        user = user_service.activate_user(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'User activated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Activate user failed: {str(e)}")
        return jsonify({'error': 'Failed to activate user'}), 500


@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
def deactivate_user(user_id: int):
    """
    Deactivate a user account.
    
    Path Parameters:
        user_id: User ID
    
    Returns:
        JSON response with deactivation status
        
    Status Codes:
        200: Success
        404: User not found
        500: Internal server error
    """
    try:
        user = user_service.deactivate_user(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'User deactivated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Deactivate user failed: {str(e)}")
        return jsonify({'error': 'Failed to deactivate user'}), 500


@user_bp.route('/<int:user_id>/verify', methods=['POST'])
def verify_user_email(user_id: int):
    """
    Verify a user's email address.
    
    Path Parameters:
        user_id: User ID
    
    Returns:
        JSON response with verification status
        
    Status Codes:
        200: Success
        404: User not found
        500: Internal server error
    """
    try:
        user = user_service.verify_email(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'Email verified successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Verify user email failed: {str(e)}")
        return jsonify({'error': 'Failed to verify email'}), 500


@user_bp.route('/<int:user_id>/password', methods=['PUT'])
def update_password(user_id: int):
    """
    Update user password.
    
    Path Parameters:
        user_id: User ID
    
    Request JSON:
        {
            "current_password": "old_password",
            "new_password": "new_password"
        }
    
    Returns:
        JSON response with update status
        
    Status Codes:
        200: Success
        400: Validation error or incorrect current password
        404: User not found
        500: Internal server error
    """
    try:
        data = validate_request_json(['current_password', 'new_password'])
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Update password
        success = user_service.update_password(user_id, current_password, new_password)
        
        if success:
            return jsonify({'message': 'Password updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update password'}), 400
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Update password failed: {str(e)}")
        return jsonify({'error': 'Failed to update password'}), 500


@user_bp.route('/search', methods=['GET'])
def search_users():
    """
    Search users by username, email, or name.
    
    Query Parameters:
        q: Search query string (required)
        include_inactive: Include inactive users (default: false)
    
    Returns:
        JSON response with matching users
        
    Status Codes:
        200: Success
        400: Missing search query
        500: Internal server error
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        users = user_service.search_users(query, include_inactive=include_inactive)
        
        return jsonify({
            'query': query,
            'count': len(users),
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Search users failed: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500