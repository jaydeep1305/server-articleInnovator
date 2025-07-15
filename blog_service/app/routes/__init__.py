"""
Routes package initialization.

This module exports all route blueprints for the Blog Microservice.
"""

from .user_routes import user_bp
from .article_routes import article_bp
from .comment_routes import comment_bp
from .health_routes import health_bp

__all__ = ['user_bp', 'article_bp', 'comment_bp', 'health_bp']