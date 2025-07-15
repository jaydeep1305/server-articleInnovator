"""
Article routes for the Blog Microservice.

This module provides RESTful API endpoints for article management
including creation, publishing, and content management.

Routes:
    GET /articles: List articles (paginated)
    POST /articles: Create new article
    GET /articles/<id>: Get article by ID
    PUT /articles/<id>: Update article
    DELETE /articles/<id>: Delete article
    GET /articles/slug/<slug>: Get article by slug
    POST /articles/<id>/publish: Publish article
    POST /articles/<id>/unpublish: Unpublish article
    GET /articles/search: Search articles
"""

from flask import Blueprint, request, jsonify, current_app

from app.models.base import db
from app.services import ArticleService
from app.models import ArticleStatus

article_bp = Blueprint('articles', __name__)

# Initialize service
article_service = ArticleService(db)


@article_bp.route('', methods=['GET'])
def list_articles():
    """List articles with pagination and filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        author_id = request.args.get('author_id', type=int)
        category = request.args.get('category')
        featured_only = request.args.get('featured_only', 'false').lower() == 'true'
        search_query = request.args.get('search')
        
        # Convert status string to enum
        status_enum = None
        if status:
            try:
                status_enum = ArticleStatus(status.lower())
            except ValueError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
        
        result = article_service.paginate_articles(
            page=page,
            per_page=per_page,
            status=status_enum,
            author_id=author_id,
            category=category,
            featured_only=featured_only,
            search_query=search_query
        )
        
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"List articles failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve articles'}), 500


@article_bp.route('', methods=['POST'])
def create_article():
    """Create a new article."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        required_fields = ['title', 'content', 'author_id']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract optional fields
        optional_fields = ['excerpt', 'category', 'tags', 'meta_title', 'meta_description']
        article_data = {k: v for k, v in data.items() if k in optional_fields}
        
        article = article_service.create_article(
            title=data['title'],
            content=data['content'],
            author_id=data['author_id'],
            **article_data
        )
        
        return jsonify({
            'message': 'Article created successfully',
            'article': article.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Create article failed: {str(e)}")
        return jsonify({'error': 'Failed to create article'}), 500


@article_bp.route('/<int:article_id>', methods=['GET'])
def get_article(article_id: int):
    """Get an article by ID."""
    try:
        include_views = request.args.get('track_view', 'false').lower() == 'true'
        
        article = article_service.get_by_id(article_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Increment view count if requested
        if include_views and article.is_published():
            article_service.increment_view_count(article_id)
            # Refresh the article to get updated view count
            article = article_service.get_by_id(article_id)
        
        return jsonify({'article': article.to_dict()}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get article failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve article'}), 500


@article_bp.route('/slug/<string:slug>', methods=['GET'])
def get_article_by_slug(slug: str):
    """Get an article by slug."""
    try:
        include_views = request.args.get('track_view', 'false').lower() == 'true'
        published_only = request.args.get('published_only', 'true').lower() == 'true'
        
        article = article_service.get_by_slug(slug, published_only=published_only)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Increment view count if requested
        if include_views:
            article_service.increment_view_count(article.id)
            # Refresh the article to get updated view count
            article = article_service.get_by_id(article.id)
        
        return jsonify({'article': article.to_dict()}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get article by slug failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve article'}), 500


@article_bp.route('/<int:article_id>/publish', methods=['POST'])
def publish_article(article_id: int):
    """Publish an article."""
    try:
        article = article_service.publish_article(article_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        return jsonify({
            'message': 'Article published successfully',
            'article': article.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Publish article failed: {str(e)}")
        return jsonify({'error': 'Failed to publish article'}), 500


@article_bp.route('/search', methods=['GET'])
def search_articles():
    """Search articles."""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        published_only = request.args.get('published_only', 'true').lower() == 'true'
        search_content = request.args.get('search_content', 'false').lower() == 'true'
        
        articles = article_service.search_articles(
            query=query,
            published_only=published_only,
            search_content=search_content
        )
        
        return jsonify({
            'query': query,
            'count': len(articles),
            'articles': [article.to_dict(include_content=False) for article in articles]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Search articles failed: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500