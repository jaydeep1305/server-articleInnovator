'''Article model for content management'''

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ArticleStatus:
    DRAFT = "draft"
    UNDER_REVIEW = "under_review" 
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Article(BaseModel):
    '''Article model for content management and publishing.'''
    
    __tablename__ = 'articles'
    
    # Basic fields
    title = Column(String(200), nullable=False)
    slug = Column(String(250), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    status = Column(String(50), default=ArticleStatus.DRAFT, index=True)
    
    # Author and workspace
    author_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # SEO fields
    meta_title = Column(String(200))
    meta_description = Column(String(300))
    meta_keywords = Column(String(500))
    featured_image_url = Column(String(500))
    
    # Publishing fields
    published_at = Column(DateTime)
    scheduled_at = Column(DateTime)
    word_count = Column(Integer, default=0)
    reading_time_minutes = Column(Integer, default=0)
    
    # Engagement metrics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # Content settings
    allow_comments = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    content_type = Column(String(50), default="article")
    
    # Relationships (defined as strings to avoid circular imports)
    # versions = relationship("ArticleVersion", back_populates="article")
    # comments = relationship("Comment", back_populates="article")
    
    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @classmethod
    def generate_slug(cls, title: str) -> str:
        '''Generate URL-friendly slug from title.'''
        import re
        slug = title.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug[:250]
    
    def publish(self) -> None:
        '''Publish the article.'''
        self.status = ArticleStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.calculate_reading_time()
    
    def calculate_reading_time(self) -> None:
        '''Calculate estimated reading time based on word count.'''
        if self.content:
            words = len(self.content.split())
            self.word_count = words
            # Average reading speed: 200 words per minute
            self.reading_time_minutes = max(1, round(words / 200))
    
    def to_dict(self) -> Dict[str, Any]:
        '''Convert article to dictionary.'''
        data = super().to_dict()
        data.update({
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'excerpt': self.excerpt,
            'status': self.status,
            'author_id': str(self.author_id),
            'workspace_id': str(self.workspace_id),
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'featured_image_url': self.featured_image_url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'word_count': self.word_count,
            'reading_time_minutes': self.reading_time_minutes,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'allow_comments': self.allow_comments,
            'is_featured': self.is_featured,
            'content_type': self.content_type
        })
        return data
