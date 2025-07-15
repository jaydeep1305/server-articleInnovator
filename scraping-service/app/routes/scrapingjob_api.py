"""
ScrapingJob API Routes

REST API endpoints for scrapingjob management with comprehensive
CRUD operations, validation, error handling, and rate limiting.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate

from app.services.scrapingjob_service import ScrapingJobService
from app import limiter

# Create API blueprint
scrapingjob_api = Blueprint('scrapingjob_api', __name__)


# Request/Response Schemas
class CreateScrapingJobSchema(Schema):
    """Schema for scrapingjob creation requests."""
    name = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(missing=None, validate=validate.Length(max=1000))
    status = fields.Str(missing="active", validate=validate.OneOf(["active", "inactive"]))


class UpdateScrapingJobSchema(Schema):
    """Schema for scrapingjob update requests."""
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
@scrapingjob_api.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'scraping-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# CRUD endpoints
@scrapingjob_api.route('/scrapingjobs', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_scrapingjob():
    """Create a new scrapingjob."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Validate request data
        schema = CreateScrapingJobSchema()
        data = schema.load(request.get_json() or {})
        
        # Create scrapingjob
        service = ScrapingJobService()
        item, success, errors = service.create_scrapingjob(
            name=data['name'],
            owner_id=user_uuid,
            description=data.get('description'),
            status=data.get('status', 'active')
        )
        
        error_response = handle_service_error(success, errors, "Failed to create scrapingjob")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'ScrapingJob created successfully',
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
        current_app.logger.error(f"Error creating scrapingjob: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@scrapingjob_api.route('/scrapingjobs', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def list_scrapingjobs():
    """Get user's scrapingjobs."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Get scrapingjobs
        service = ScrapingJobService()
        items = service.get_scrapingjobs_by_owner(user_uuid, limit)
        
        return jsonify({
            'message': 'ScrapingJobs retrieved successfully',
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
        current_app.logger.error(f"Error listing scrapingjobs: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@scrapingjob_api.route('/scrapingjobs/<item_id>', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_scrapingjob(item_id: str):
    """Get scrapingjob details."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Get scrapingjob
        service = ScrapingJobService()
        item = service.get_scrapingjob_by_id(item_uuid)
        
        if not item:
            return jsonify({
                'error': 'Not Found',
                'message': 'ScrapingJob not found',
                'status_code': 404
            }), 404
        
        # Check permissions
        if item.owner_id != user_uuid:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied to this scrapingjob',
                'status_code': 403
            }), 403
        
        return jsonify({
            'message': 'ScrapingJob retrieved successfully',
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
        current_app.logger.error(f"Error getting scrapingjob: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@scrapingjob_api.route('/scrapingjobs/<item_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_scrapingjob(item_id: str):
    """Update scrapingjob details."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Validate request data
        schema = UpdateScrapingJobSchema()
        updates = schema.load(request.get_json() or {})
        
        if not updates:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No valid fields provided for update',
                'status_code': 400
            }), 400
        
        # Update scrapingjob
        service = ScrapingJobService()
        item, success, errors = service.update_scrapingjob(
            item_id=item_uuid,
            updates=updates,
            updated_by=user_uuid
        )
        
        error_response = handle_service_error(success, errors, "Failed to update scrapingjob")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'ScrapingJob updated successfully',
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
        current_app.logger.error(f"Error updating scrapingjob: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


@scrapingjob_api.route('/scrapingjobs/<item_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per hour")
def delete_scrapingjob(item_id: str):
    """Delete scrapingjob."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Delete scrapingjob
        service = ScrapingJobService()
        success, errors = service.delete_scrapingjob(item_uuid, user_uuid)
        
        error_response = handle_service_error(success, errors, "Failed to delete scrapingjob")
        if error_response:
            return error_response
        
        return jsonify({
            'message': 'ScrapingJob deleted successfully',
            'status_code': 200
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error deleting scrapingjob: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
