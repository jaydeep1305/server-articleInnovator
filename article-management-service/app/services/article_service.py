"""
Article Service - Business Logic Layer

This module contains comprehensive business logic for article management,
including content creation, publishing workflow, SEO optimization, and analytics.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.article import Article, ArticleStatus
from app import db


class ArticleService:
    """Service class for article management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_article(self, title: str, content: str, author_id: uuid.UUID,
                      workspace_id: uuid.UUID, **kwargs) -> Tuple[Optional[Article], bool, List[str]]:
        """Create a new article with validation."""
        try:
            # Generate slug
            base_slug = Article.generate_slug(title)
            slug = self._ensure_unique_slug(base_slug)
            
            # Create article
            article = Article(
                title=title.strip(),
                slug=slug,
                content=content,
                author_id=author_id,
                workspace_id=workspace_id,
                **kwargs
            )
            
            # Calculate reading time
            article.calculate_reading_time()
            
            # Validate
            is_valid, errors = article.validate()
            if not is_valid:
                return None, False, errors
            
            self.session.add(article)
            self.session.commit()
            
            return article, True, []
            
        except IntegrityError:
            self.session.rollback()
            return None, False, ["Article with this slug already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating article: {str(e)}"]
    
    def publish_article(self, article_id: uuid.UUID, published_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Publish an article."""
        try:
            article = Article.get_by_id(self.session, article_id)
            if not article:
                return False, ["Article not found"]
            
            # Check permissions (simplified)
            if article.author_id != published_by:
                return False, ["Only the author can publish this article"]
            
            article.publish()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error publishing article: {str(e)}"]
    
    def get_articles_by_workspace(self, workspace_id: uuid.UUID, 
                                 status: str = None, limit: int = 20) -> List[Article]:
        """Get articles for a workspace."""
        query = self.session.query(Article).filter(
            Article.workspace_id == workspace_id,
            Article.is_deleted == False
        )
        
        if status:
            query = query.filter(Article.status == status)
        
        return query.order_by(Article.created_at.desc()).limit(limit).all()
    
    def search_articles(self, query: str, workspace_id: uuid.UUID = None) -> List[Article]:
        """Search articles by title and content."""
        from sqlalchemy import or_, func
        
        search_query = self.session.query(Article).filter(Article.is_deleted == False)
        
        if workspace_id:
            search_query = search_query.filter(Article.workspace_id == workspace_id)
        
        if query:
            search_terms = f"%{query}%"
            search_query = search_query.filter(
                or_(
                    func.lower(Article.title).like(func.lower(search_terms)),
                    func.lower(Article.content).like(func.lower(search_terms))
                )
            )
        
        return search_query.order_by(Article.created_at.desc()).limit(50).all()
    
    def _ensure_unique_slug(self, base_slug: str) -> str:
        """Ensure article slug is unique."""
        slug = base_slug
        counter = 1
        
        while True:
            existing = self.session.query(Article).filter(
                Article.slug == slug,
                Article.is_deleted == False
            ).first()
            
            if not existing:
                return slug
            
            slug = f"{base_slug}-{counter}"
            counter += 1
