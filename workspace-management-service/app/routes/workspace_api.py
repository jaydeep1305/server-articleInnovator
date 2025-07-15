"""
Workspace API Routes

This module contains REST API endpoints for workspace management operations.
Provides comprehensive CRUD operations for workspaces, member management,
and workspace-related functionality with proper HTTP status codes.

Author: AI Assistant
Date: 2024
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate

from app.services.workspace_service import WorkspaceService
from app.models.workspace import WorkspaceRole, WorkspaceStatus
from app import limiter


# Create API blueprint
workspace_api = Blueprint('workspace_api', __name__)


# Request/Response Schemas for validation
class CreateWorkspaceSchema(Schema):
    """Schema for workspace creation requests."""
    name = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    description = fields.Str(missing=None, validate=validate.Length(max=500))
    visibility = fields.Str(missing="private", validate=validate.OneOf(["public", "private", "internal"]))
    max_members = fields.Int(missing=10, validate=validate.Range(min=1, max=1000))
    storage_quota_gb = fields.Int(missing=5, validate=validate.Range(min=1, max=100))
    theme_color = fields.Str(missing="#6366F1", validate=validate.Regexp(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'))
    allow_guest_access = fields.Bool(missing=False)
    require_approval = fields.Bool(missing=True)
    enable_notifications = fields.Bool(missing=True)


class UpdateWorkspaceSchema(Schema):
    """Schema for workspace update requests."""
    name = fields.Str(validate=validate.Length(min=3, max=50))
    description = fields.Str(validate=validate.Length(max=500), allow_none=True)
    visibility = fields.Str(validate=validate.OneOf(["public", "private", "internal"]))
    max_members = fields.Int(validate=validate.Range(min=1, max=1000))
    storage_quota_gb = fields.Int(validate=validate.Range(min=1, max=100))
    theme_color = fields.Str(validate=validate.Regexp(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'))
    allow_guest_access = fields.Bool()
    require_approval = fields.Bool()
    enable_notifications = fields.Bool()


class AddMemberSchema(Schema):
    """Schema for adding workspace members."""
    user_id = fields.Str(required=True)
    role = fields.Str(missing="member", validate=validate.OneOf(["member", "admin", "guest"]))


class UpdateMemberRoleSchema(Schema):
    """Schema for updating member roles."""
    role = fields.Str(required=True, validate=validate.OneOf(["member", "admin", "guest"]))


def validate_uuid(uuid_string: str) -> uuid.UUID:
    """
    Validate and convert UUID string.
    
    Args:
        uuid_string: UUID string to validate
        
    Returns:
        UUID object
        
    Raises:
        ValueError: If UUID is invalid
    """
    try:
        return uuid.UUID(uuid_string)
    except (ValueError, TypeError):
        raise ValueError("Invalid UUID format")


def handle_validation_error(error: ValidationError) -> tuple:
    """
    Handle marshmallow validation errors.
    
    Args:
        error: ValidationError instance
        
    Returns:
        tuple: JSON response and status code
    """
    return jsonify({
        'error': 'Validation Error',
        'message': 'Request data validation failed',
        'details': error.messages,
        'status_code': 400
    }), 400


def handle_service_error(success: bool, errors: list, default_message: str = "Operation failed") -> tuple:
    """
    Handle service layer errors.
    
    Args:
        success: Success flag from service
        errors: List of error messages
        default_message: Default error message
        
    Returns:
        tuple: JSON response and status code
    """
    if success:
        return None
    
    message = errors[0] if errors else default_message
    status_code = 404 if "not found" in message.lower() else 400
    
    return jsonify({
        'error': 'Operation Failed',
        'message': message,
        'details': errors,
        'status_code': status_code
    }), status_code


# Health check endpoints
@workspace_api.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'workspace-management-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Workspace CRUD endpoints
@workspace_api.route('/workspaces', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def create_workspace():
    """
    Create a new workspace.
    
    Returns:
        JSON response with workspace data or error
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Validate request data
        schema = CreateWorkspaceSchema()
        data = schema.load(request.get_json() or {})
        
        # Create workspace
        workspace_service = WorkspaceService()
        workspace, success, errors = workspace_service.create_workspace(
            name=data['name'],
            owner_id=user_uuid,
            description=data.get('description'),
            **{k: v for k, v in data.items() if k not in ['name', 'description']}
        )
        
        if not success:
            error_response = handle_service_error(success, errors, "Failed to create workspace")
            if error_response:
                return error_response
        
        return jsonify({
            'message': 'Workspace created successfully',
            'data': workspace.to_dict(),
            'status_code': 201
        }), 201
        
    except ValidationError as e:
        return handle_validation_error(e)
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error creating workspace: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@workspace_api.route('/workspaces', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def list_workspaces():
    """
    Get user's workspaces.
    
    Returns:
        JSON response with list of workspaces
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Get query parameters
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        search_query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Get workspaces
        workspace_service = WorkspaceService()
        
        if search_query:
            workspaces = workspace_service.search_workspaces(
                query=search_query,
                user_id=user_uuid,
                limit=limit
            )
        else:
            workspaces = workspace_service.get_user_workspaces(
                user_id=user_uuid,
                include_archived=include_archived
            )[:limit]
        
        return jsonify({
            'message': 'Workspaces retrieved successfully',
            'data': [ws.to_dict() for ws in workspaces],
            'total': len(workspaces),
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error listing workspaces: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@workspace_api.route('/workspaces/<workspace_id>', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_workspace(workspace_id: str):
    """
    Get workspace details.
    
    Args:
        workspace_id: Workspace UUID
        
    Returns:
        JSON response with workspace data
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        workspace_uuid = validate_uuid(workspace_id)
        
        # Get workspace
        workspace_service = WorkspaceService()
        workspace = workspace_service.get_workspace_by_id(workspace_uuid)
        
        if not workspace:
            return jsonify({
                'error': 'Not Found',
                'message': 'Workspace not found',
                'status_code': 404
            }), 404
        
        # Check if user has access to workspace
        if not workspace_service.check_workspace_permissions(workspace_uuid, user_uuid):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied to this workspace',
                'status_code': 403
            }), 403
        
        # Include additional data for detailed view
        workspace_data = workspace.to_dict()
        workspace_data['members'] = workspace_service.get_workspace_members(workspace_uuid)
        workspace_data['user_role'] = workspace.get_member_role(workspace_service.session, user_uuid).value
        
        return jsonify({
            'message': 'Workspace retrieved successfully',
            'data': workspace_data,
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error getting workspace: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@workspace_api.route('/workspaces/<workspace_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_workspace(workspace_id: str):
    """
    Update workspace details.
    
    Args:
        workspace_id: Workspace UUID
        
    Returns:
        JSON response with updated workspace data
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        workspace_uuid = validate_uuid(workspace_id)
        
        # Validate request data
        schema = UpdateWorkspaceSchema()
        updates = schema.load(request.get_json() or {})
        
        if not updates:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No valid fields provided for update',
                'status_code': 400
            }), 400
        
        # Update workspace
        workspace_service = WorkspaceService()
        workspace, success, errors = workspace_service.update_workspace(
            workspace_id=workspace_uuid,
            updates=updates,
            updated_by=user_uuid
        )
        
        error_response = handle_service_error(success, errors, "Failed to update workspace")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'Workspace updated successfully',
            'data': workspace.to_dict(),
            'status_code': 200
        }), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error updating workspace: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@workspace_api.route('/workspaces/<workspace_id>/archive', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def archive_workspace(workspace_id: str):
    """
    Archive a workspace.
    
    Args:
        workspace_id: Workspace UUID
        
    Returns:
        JSON response confirming archive
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        workspace_uuid = validate_uuid(workspace_id)
        
        # Archive workspace
        workspace_service = WorkspaceService()
        success, errors = workspace_service.archive_workspace(workspace_uuid, user_uuid)
        
        error_response = handle_service_error(success, errors, "Failed to archive workspace")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'Workspace archived successfully',
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error archiving workspace: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


# Member management endpoints
@workspace_api.route('/workspaces/<workspace_id>/members', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_workspace_members(workspace_id: str):
    """
    Get workspace members.
    
    Args:
        workspace_id: Workspace UUID
        
    Returns:
        JSON response with member list
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        workspace_uuid = validate_uuid(workspace_id)
        
        # Check access
        workspace_service = WorkspaceService()
        if not workspace_service.check_workspace_permissions(workspace_uuid, user_uuid):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied to this workspace',
                'status_code': 403
            }), 403
        
        # Get members
        members = workspace_service.get_workspace_members(workspace_uuid)
        
        return jsonify({
            'message': 'Members retrieved successfully',
            'data': members,
            'total': len(members),
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error getting workspace members: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@workspace_api.route('/workspaces/<workspace_id>/members', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def add_workspace_member(workspace_id: str):
    """
    Add member to workspace.
    
    Args:
        workspace_id: Workspace UUID
        
    Returns:
        JSON response confirming member addition
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        workspace_uuid = validate_uuid(workspace_id)
        
        # Validate request data
        schema = AddMemberSchema()
        data = schema.load(request.get_json() or {})
        
        member_uuid = validate_uuid(data['user_id'])
        role = WorkspaceRole(data['role'])
        
        # Add member
        workspace_service = WorkspaceService()
        success, errors = workspace_service.add_workspace_member(
            workspace_id=workspace_uuid,
            user_id=member_uuid,
            role=role,
            invited_by=user_uuid
        )
        
        error_response = handle_service_error(success, errors, "Failed to add member")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'Member added successfully',
            'status_code': 201
        }), 201
        
    except ValidationError as e:
        return handle_validation_error(e)
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error adding workspace member: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@workspace_api.route('/workspaces/<workspace_id>/members/<user_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("20 per hour")
def remove_workspace_member(workspace_id: str, user_id: str):
    """
    Remove member from workspace.
    
    Args:
        workspace_id: Workspace UUID
        user_id: User UUID to remove
        
    Returns:
        JSON response confirming member removal
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        remover_uuid = validate_uuid(current_user_id)
        workspace_uuid = validate_uuid(workspace_id)
        member_uuid = validate_uuid(user_id)
        
        # Remove member
        workspace_service = WorkspaceService()
        success, errors = workspace_service.remove_workspace_member(
            workspace_id=workspace_uuid,
            user_id=member_uuid,
            removed_by=remover_uuid
        )
        
        error_response = handle_service_error(success, errors, "Failed to remove member")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'Member removed successfully',
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error removing workspace member: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@workspace_api.route('/workspaces/<workspace_id>/members/<user_id>/role', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_member_role(workspace_id: str, user_id: str):
    """
    Update member role in workspace.
    
    Args:
        workspace_id: Workspace UUID
        user_id: User UUID whose role to update
        
    Returns:
        JSON response confirming role update
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        updater_uuid = validate_uuid(current_user_id)
        workspace_uuid = validate_uuid(workspace_id)
        member_uuid = validate_uuid(user_id)
        
        # Validate request data
        schema = UpdateMemberRoleSchema()
        data = schema.load(request.get_json() or {})
        
        new_role = WorkspaceRole(data['role'])
        
        # Update role
        workspace_service = WorkspaceService()
        success, errors = workspace_service.update_member_role(
            workspace_id=workspace_uuid,
            user_id=member_uuid,
            new_role=new_role,
            updated_by=updater_uuid
        )
        
        error_response = handle_service_error(success, errors, "Failed to update member role")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'Member role updated successfully',
            'status_code': 200
        }), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error updating member role: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


# Search endpoints
@workspace_api.route('/workspaces/search', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def search_workspaces():
    """
    Search workspaces.
    
    Returns:
        JSON response with search results
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Get query parameters
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not query:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Search query is required',
                'status_code': 400
            }), 400
        
        # Search workspaces
        workspace_service = WorkspaceService()
        workspaces = workspace_service.search_workspaces(
            query=query,
            user_id=user_uuid,
            limit=limit
        )
        
        return jsonify({
            'message': 'Search completed successfully',
            'data': [ws.to_dict() for ws in workspaces],
            'total': len(workspaces),
            'query': query,
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error searching workspaces: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500