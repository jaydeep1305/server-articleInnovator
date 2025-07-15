"""
ImageRequest API Routes

REST API endpoints for imagerequest management with comprehensive
CRUD operations, validation, error handling, and rate limiting.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate

from app.services.imagerequest_service import ImageRequestService
from app import limiter

# Create API blueprint
imagerequest_api = Blueprint('imagerequest_api', __name__)


# Request/Response Schemas
class CreateImageRequestSchema(Schema):
    """Schema for imagerequest creation requests."""
    name = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(missing=None, validate=validate.Length(max=1000))
    status = fields.Str(missing="active", validate=validate.OneOf(["active", "inactive"]))


class UpdateImageRequestSchema(Schema):
    """Schema for imagerequest update requests."""
    name = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str(validate=validate.Length(max=1000), allow_none=True)
    status = fields.Str(validate=validate.OneOf(["active", "inactive"]))


def validate_uuid(uuid_string: str) -> uuid.UUID:
    """Validate and convert UUID string."""
    try:
        return uuid.UUID(uuid_string)
    except (ValueError, TypeError):
        raise ValueError("Invalid UUID format")


def handle_validation_error(error: ValidationError) -> tuple:
    """Handle marshmallow validation errors."""
    return jsonify({
        'error': 'Validation Error',
        'message': 'Request data validation failed',
        'details': error.messages,
        'status_code': 400
    }), 400


def handle_service_error(success: bool, errors: list, default_message: str = "Operation failed") -> tuple:
    """Handle service layer errors."""
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


# Health check endpoint
@imagerequest_api.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'image-generation-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# CRUD endpoints
@imagerequest_api.route('/imagerequests', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_imagerequest():
    """Create a new imagerequest."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Validate request data
        schema = CreateImageRequestSchema()
        data = schema.load(request.get_json() or {})
        
        # Create imagerequest
        service = ImageRequestService()
        item, success, errors = service.create_imagerequest(
            name=data['name'],
            owner_id=user_uuid,
            description=data.get('description'),
            status=data.get('status', 'active')
        )
        
        error_response = handle_service_error(success, errors, "Failed to create imagerequest")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'ImageRequest created successfully',
            'data': item.to_dict(),
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
        current_app.logger.error(f"Error creating imagerequest: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@imagerequest_api.route('/imagerequests', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def list_imagerequests():
    """Get user's imagerequests."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Get imagerequests
        service = ImageRequestService()
        items = service.get_imagerequests_by_owner(user_uuid, limit)
        
        return jsonify({
            'message': 'ImageRequests retrieved successfully',
            'data': [item.to_dict() for item in items],
            'total': len(items),
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error listing imagerequests: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@imagerequest_api.route('/imagerequests/<item_id>', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_imagerequest(item_id: str):
    """Get imagerequest details."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Get imagerequest
        service = ImageRequestService()
        item = service.get_imagerequest_by_id(item_uuid)
        
        if not item:
            return jsonify({
                'error': 'Not Found',
                'message': 'ImageRequest not found',
                'status_code': 404
            }), 404
        
        # Check permissions
        if item.owner_id != user_uuid:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied to this imagerequest',
                'status_code': 403
            }), 403
        
        return jsonify({
            'message': 'ImageRequest retrieved successfully',
            'data': item.to_dict(),
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error getting imagerequest: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@imagerequest_api.route('/imagerequests/<item_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_imagerequest(item_id: str):
    """Update imagerequest details."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Validate request data
        schema = UpdateImageRequestSchema()
        updates = schema.load(request.get_json() or {})
        
        if not updates:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No valid fields provided for update',
                'status_code': 400
            }), 400
        
        # Update imagerequest
        service = ImageRequestService()
        item, success, errors = service.update_imagerequest(
            item_id=item_uuid,
            updates=updates,
            updated_by=user_uuid
        )
        
        error_response = handle_service_error(success, errors, "Failed to update imagerequest")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'ImageRequest updated successfully',
            'data': item.to_dict(),
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
        current_app.logger.error(f"Error updating imagerequest: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@imagerequest_api.route('/imagerequests/<item_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per hour")
def delete_imagerequest(item_id: str):
    """Delete imagerequest."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Delete imagerequest
        service = ImageRequestService()
        success, errors = service.delete_imagerequest(item_uuid, user_uuid)
        
        error_response = handle_service_error(success, errors, "Failed to delete imagerequest")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'ImageRequest deleted successfully',
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error deleting imagerequest: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
