"""
Comment routes for the Blog Microservice.

This module provides RESTful API endpoints for comment management
including creation, moderation, and threading.

Routes:
    GET /comments: List comments (paginated)
    POST /comments: Create new comment
    GET /comments/<id>: Get comment by ID
    PUT /comments/<id>: Update comment
    DELETE /comments/<id>: Delete comment
    POST /comments/<id>/approve: Approve comment
    POST /comments/<id>/reject: Reject comment
    GET /comments/article/<id>: Get comments for article
    GET /comments/moderation: Get moderation queue
"""

from flask import Blueprint, request, jsonify, current_app

from app.models.base import db
from app.services import CommentService
from app.models import CommentStatus

comment_bp = Blueprint('comments', __name__)

# Initialize service
comment_service = CommentService(db)


@comment_bp.route('', methods=['GET'])
def list_comments():
    """List comments with pagination and filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        article_id = request.args.get('article_id', type=int)
        author_id = request.args.get('author_id', type=int)
        status = request.args.get('status')
        search_query = request.args.get('search')
        
        # Convert status string to enum
        status_enum = None
        if status:
            try:
                status_enum = CommentStatus(status.lower())
            except ValueError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
        
        result = comment_service.paginate_comments(
            page=page,
            per_page=per_page,
            article_id=article_id,
            author_id=author_id,
            status=status_enum,
            search_query=search_query
        )
        
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"List comments failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve comments'}), 500


@comment_bp.route('', methods=['POST'])
def create_comment():
    """Create a new comment."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        
        # Required fields
        if 'content' not in data or 'article_id' not in data:
            return jsonify({'error': 'Missing required fields: content, article_id'}), 400
        
        # Extract fields
        content = data['content']
        article_id = data['article_id']
        author_id = data.get('author_id')
        author_name = data.get('author_name')
        author_email = data.get('author_email')
        parent_id = data.get('parent_id')
        ip_address = request.environ.get('REMOTE_ADDR')
        
        # Create comment or reply
        if parent_id:
            comment = comment_service.create_reply(
                content=content,
                parent_id=parent_id,
                author_id=author_id,
                author_name=author_name,
                author_email=author_email,
                ip_address=ip_address
            )
        else:
            comment = comment_service.create_comment(
                content=content,
                article_id=article_id,
                author_id=author_id,
                author_name=author_name,
                author_email=author_email,
                ip_address=ip_address
            )
        
        return jsonify({
            'message': 'Comment created successfully',
            'comment': comment.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Create comment failed: {str(e)}")
        return jsonify({'error': 'Failed to create comment'}), 500


@comment_bp.route('/<int:comment_id>', methods=['GET'])
def get_comment(comment_id: int):
    """Get a comment by ID."""
    try:
        comment = comment_service.get_by_id(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        return jsonify({'comment': comment.to_dict()}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get comment failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve comment'}), 500


@comment_bp.route('/article/<int:article_id>', methods=['GET'])
def get_article_comments(article_id: int):
    """Get comments for a specific article."""
    try:
        approved_only = request.args.get('approved_only', 'true').lower() == 'true'
        include_replies = request.args.get('include_replies', 'true').lower() == 'true'
        
        comments = comment_service.get_comments_by_article(
            article_id=article_id,
            approved_only=approved_only,
            include_replies=include_replies
        )
        
        return jsonify({
            'article_id': article_id,
            'count': len(comments),
            'comments': [comment.to_dict() for comment in comments]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get article comments failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve comments'}), 500


@comment_bp.route('/<int:comment_id>/approve', methods=['POST'])
def approve_comment(comment_id: int):
    """Approve a comment for public display."""
    try:
        comment = comment_service.approve_comment(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        return jsonify({
            'message': 'Comment approved successfully',
            'comment': comment.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Approve comment failed: {str(e)}")
        return jsonify({'error': 'Failed to approve comment'}), 500


@comment_bp.route('/<int:comment_id>/reject', methods=['POST'])
def reject_comment(comment_id: int):
    """Reject a comment."""
    try:
        comment = comment_service.reject_comment(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        return jsonify({
            'message': 'Comment rejected successfully',
            'comment': comment.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Reject comment failed: {str(e)}")
        return jsonify({'error': 'Failed to reject comment'}), 500


@comment_bp.route('/moderation', methods=['GET'])
def get_moderation_queue():
    """Get comments pending moderation."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        result = comment_service.get_moderation_queue(page=page, per_page=per_page)
        
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get moderation queue failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve moderation queue'}), 500