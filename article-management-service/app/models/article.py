"""
Article model for content management and publishing.

This module defines the Article model that handles content creation, editing,
publishing workflow, SEO optimization, and content versioning. Implements
cognitive patterns for content management systems.

Author: AI Assistant
Date: 2024
"""

import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID, JSON

from .base import BaseModel
from app import db


class ArticleStatus(Enum):
    """Enumeration for article publication status."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ContentType(Enum):
    """Enumeration for content types."""
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    NEWS = "news"
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"
    ANNOUNCEMENT = "announcement"


class Article(BaseModel):
    """
    Article model for content management and publishing.
    
    This model handles content creation, editing, publishing workflow,
    SEO optimization, and content versioning. It supports rich content
    management with cognitive UX patterns for content creators.
    
    Attributes:
        title (str): Article title (required, 3-200 characters)
        slug (str): URL-friendly identifier (auto-generated from title)
        content (text): Main article content (rich text/markdown)
        excerpt (str): Short summary/description (optional, max 500 chars)
        content_type (str): Type of content (article, blog_post, etc.)
        status (str): Publication status (draft, published, etc.)
        author_id (UUID): ID of the content author
        workspace_id (UUID): ID of the workspace this article belongs to
        published_at (datetime): When article was published
        
    SEO Fields:
        meta_title (str): SEO meta title
        meta_description (str): SEO meta description
        meta_keywords (str): SEO keywords (comma-separated)
        
    Content Features:
        featured_image_url (str): URL to featured image
        reading_time_minutes (int): Estimated reading time
        word_count (int): Article word count
        tags (JSON): Article tags for categorization
        
    Engagement:
        view_count (int): Number of views
        like_count (int): Number of likes
        comment_count (int): Number of comments
        
    Relationships:
        author: Many-to-one relationship with User
        workspace: Many-to-one relationship with Workspace
        versions: One-to-many relationship with ArticleVersion
    """
    
    __tablename__ = 'articles'
    
    # Core article content
    title = Column(
        String(200),
        nullable=False,
        index=True,
        comment="Article title (3-200 characters)"
    )
    
    slug = Column(
        String(250),
        nullable=False,
        index=True,
        comment="URL-friendly identifier"
    )
    
    content = Column(
        Text,
        nullable=False,
        comment="Main article content (rich text/markdown)"
    )
    
    excerpt = Column(
        String(500),
        nullable=True,
        comment="Short summary/description"
    )
    
    # Content classification
    content_type = Column(
        String(20),
        default=ContentType.ARTICLE.value,
        nullable=False,
        index=True,
        comment="Type of content"
    )
    
    status = Column(
        String(20),
        default=ArticleStatus.DRAFT.value,
        nullable=False,
        index=True,
        comment="Publication status"
    )
    
    # Ownership and workspace
    author_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID of the content author"
    )
    
    workspace_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID of the workspace this article belongs to"
    )
    
    # Publishing information
    published_at = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="When article was published"
    )
    
    scheduled_for = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="Scheduled publication time"
    )
    
    # SEO fields
    meta_title = Column(
        String(60),
        nullable=True,
        comment="SEO meta title (max 60 chars for Google)"
    )
    
    meta_description = Column(
        String(160),
        nullable=True,
        comment="SEO meta description (max 160 chars for Google)"
    )
    
    meta_keywords = Column(
        String(500),
        nullable=True,
        comment="SEO keywords (comma-separated)"
    )
    
    # Content metadata
    featured_image_url = Column(
        String(500),
        nullable=True,
        comment="URL to featured image"
    )
    
    reading_time_minutes = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Estimated reading time in minutes"
    )
    
    word_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Article word count"
    )
    
    tags = Column(
        JSON,
        nullable=True,
        comment="Article tags for categorization"
    )
    
    # Engagement metrics
    view_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of views"
    )
    
    like_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of likes"
    )
    
    comment_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of comments"
    )
    
    # Content settings
    allow_comments = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether comments are allowed"
    )
    
    is_featured = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether article is featured"
    )
    
    is_pinned = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether article is pinned"
    )
    
    # Content format
    content_format = Column(
        String(20),
        default="markdown",
        nullable=False,
        comment="Content format (markdown, html, rich_text)"
    )
    
    # Version tracking
    version_number = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Current version number"
    )
    
    last_edited_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of user who last edited the article"
    )
    
    last_edited_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When article was last edited"
    )
    
    def __init__(self, title: str, content: str, author_id: uuid.UUID, 
                 workspace_id: uuid.UUID, **kwargs) -> None:
        """
        Initialize a new article with cognitive validation.
        
        Args:
            title: Article title
            content: Article content
            author_id: UUID of the author
            workspace_id: UUID of the workspace
            **kwargs: Additional article attributes
            
        Raises:
            ValueError: If article data is invalid
        """
        # Generate slug from title if not provided
        slug = kwargs.get('slug', self._generate_slug(title))
        
        # Calculate content metrics
        word_count = self._calculate_word_count(content)
        reading_time = self._calculate_reading_time(word_count)
        
        # Auto-generate excerpt if not provided
        excerpt = kwargs.get('excerpt', self._generate_excerpt(content))
        
        # Set required and calculated fields
        kwargs.update({
            'title': title.strip(),
            'slug': slug,
            'content': content,
            'excerpt': excerpt,
            'author_id': author_id,
            'workspace_id': workspace_id,
            'word_count': word_count,
            'reading_time_minutes': reading_time,
            'last_edited_by': author_id,
            'last_edited_at': datetime.utcnow()
        })
        
        super().__init__(**kwargs)
        
        # Validate the article
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Article validation failed: {', '.join(errors)}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate article data according to business rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        is_valid, errors = super().validate()
        
        # Title validation
        if not self._validate_title(self.title):
            errors.append("Title must be 3-200 characters long")
        
        # Slug validation
        if not self._validate_slug(self.slug):
            errors.append("Slug must be URL-friendly and 3-250 characters long")
        
        # Content validation
        if not self.content or len(self.content.strip()) < 10:
            errors.append("Content must be at least 10 characters long")
        
        # Excerpt validation
        if self.excerpt and len(self.excerpt) > 500:
            errors.append("Excerpt cannot exceed 500 characters")
        
        # Content type validation
        valid_types = {content_type.value for content_type in ContentType}
        if self.content_type not in valid_types:
            errors.append(f"Content type must be one of: {', '.join(valid_types)}")
        
        # Status validation
        valid_statuses = {status.value for status in ArticleStatus}
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # SEO validation
        if self.meta_title and len(self.meta_title) > 60:
            errors.append("Meta title should not exceed 60 characters for SEO")
        
        if self.meta_description and len(self.meta_description) > 160:
            errors.append("Meta description should not exceed 160 characters for SEO")
        
        # Content format validation
        valid_formats = {'markdown', 'html', 'rich_text'}
        if self.content_format not in valid_formats:
            errors.append(f"Content format must be one of: {', '.join(valid_formats)}")
        
        # Scheduled publication validation
        if self.scheduled_for and self.scheduled_for <= datetime.utcnow():
            errors.append("Scheduled publication time must be in the future")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _generate_slug(title: str) -> str:
        """
        Generate URL-friendly slug from article title.
        
        Args:
            title: Article title
            
        Returns:
            str: URL-friendly slug
        """
        if not title:
            return f"article-{uuid.uuid4().hex[:8]}"
        
        # Convert to lowercase and clean up
        slug = title.lower().strip()
        
        # Remove special characters and replace with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure minimum length
        if len(slug) < 3:
            slug = f"article-{uuid.uuid4().hex[:8]}"
        
        return slug[:250]  # Limit length
    
    @staticmethod
    def _calculate_word_count(content: str) -> int:
        """
        Calculate word count of content.
        
        Args:
            content: Article content
            
        Returns:
            int: Word count
        """
        if not content:
            return 0
        
        # Remove HTML/Markdown tags for accurate count
        clean_content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
        clean_content = re.sub(r'\[.*?\]\(.*?\)', '', clean_content)  # Remove markdown links
        clean_content = re.sub(r'[*_`#]', '', clean_content)  # Remove markdown formatting
        
        # Count words
        words = clean_content.split()
        return len(words)
    
    @staticmethod
    def _calculate_reading_time(word_count: int) -> int:
        """
        Calculate estimated reading time based on word count.
        
        Args:
            word_count: Number of words in article
            
        Returns:
            int: Estimated reading time in minutes
        """
        # Average reading speed: 200-250 words per minute
        # Using 220 as a reasonable average
        if word_count == 0:
            return 0
        
        reading_time = max(1, round(word_count / 220))
        return reading_time
    
    @staticmethod
    def _generate_excerpt(content: str, max_length: int = 200) -> str:
        """
        Generate excerpt from article content.
        
        Args:
            content: Article content
            max_length: Maximum excerpt length
            
        Returns:
            str: Generated excerpt
        """
        if not content:
            return ""
        
        # Clean content for excerpt generation
        clean_content = re.sub(r'<[^>]+>', '', content)  # Remove HTML
        clean_content = re.sub(r'\[.*?\]\(.*?\)', '', clean_content)  # Remove markdown links
        clean_content = re.sub(r'[*_`#]', '', clean_content)  # Remove formatting
        clean_content = clean_content.strip()
        
        # Take first paragraph or first N characters
        paragraphs = clean_content.split('\n\n')
        first_paragraph = paragraphs[0] if paragraphs else clean_content
        
        if len(first_paragraph) <= max_length:
            return first_paragraph
        
        # Truncate at word boundary
        truncated = first_paragraph[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # Only truncate if we don't lose too much
            truncated = truncated[:last_space]
        
        return truncated + "..." if len(first_paragraph) > len(truncated) else truncated
    
    @staticmethod
    def _validate_title(title: str) -> bool:
        """
        Validate article title.
        
        Args:
            title: Title to validate
            
        Returns:
            bool: True if title is valid
        """
        if not title:
            return False
        
        title = title.strip()
        return 3 <= len(title) <= 200
    
    @staticmethod
    def _validate_slug(slug: str) -> bool:
        """
        Validate article slug.
        
        Args:
            slug: Slug to validate
            
        Returns:
            bool: True if slug is valid
        """
        if not slug or len(slug) < 3 or len(slug) > 250:
            return False
        
        # Slug pattern: lowercase letters, numbers, hyphens
        slug_pattern = r'^[a-z0-9-]+$'
        return re.match(slug_pattern, slug) is not None
    
    def publish(self, published_by: uuid.UUID) -> None:
        """
        Publish the article.
        
        Args:
            published_by: ID of user publishing the article
        """
        self.status = ArticleStatus.PUBLISHED.value
        self.published_at = datetime.utcnow()
        self.last_edited_by = published_by
        self.last_edited_at = datetime.utcnow()
    
    def unpublish(self, unpublished_by: uuid.UUID) -> None:
        """
        Unpublish the article (move to draft).
        
        Args:
            unpublished_by: ID of user unpublishing the article
        """
        self.status = ArticleStatus.DRAFT.value
        self.published_at = None
        self.last_edited_by = unpublished_by
        self.last_edited_at = datetime.utcnow()
    
    def archive(self, archived_by: uuid.UUID) -> None:
        """
        Archive the article.
        
        Args:
            archived_by: ID of user archiving the article
        """
        self.status = ArticleStatus.ARCHIVED.value
        self.last_edited_by = archived_by
        self.last_edited_at = datetime.utcnow()
    
    def update_content(self, new_content: str, updated_by: uuid.UUID) -> None:
        """
        Update article content and recalculate metrics.
        
        Args:
            new_content: New article content
            updated_by: ID of user updating the content
        """
        self.content = new_content
        self.word_count = self._calculate_word_count(new_content)
        self.reading_time_minutes = self._calculate_reading_time(self.word_count)
        
        # Auto-update excerpt if it was auto-generated
        if not self.excerpt or len(self.excerpt) < 50:
            self.excerpt = self._generate_excerpt(new_content)
        
        self.last_edited_by = updated_by
        self.last_edited_at = datetime.utcnow()
        self.version_number += 1
    
    def increment_view_count(self) -> None:
        """Increment the article view count."""
        self.view_count += 1
    
    def increment_like_count(self) -> None:
        """Increment the article like count."""
        self.like_count += 1
    
    def decrement_like_count(self) -> None:
        """Decrement the article like count."""
        self.like_count = max(0, self.like_count - 1)
    
    def update_comment_count(self, count: int) -> None:
        """
        Update the comment count.
        
        Args:
            count: New comment count
        """
        self.comment_count = max(0, count)
    
    def set_featured(self, is_featured: bool) -> None:
        """Set featured status."""
        self.is_featured = is_featured
        self.updated_at = datetime.utcnow()
    
    def set_pinned(self, is_pinned: bool) -> None:
        """Set pinned status."""
        self.is_pinned = is_pinned
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the article.
        
        Args:
            tag: Tag to add
        """
        if not self.tags:
            self.tags = []
        
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the article.
        
        Args:
            tag: Tag to remove
        """
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def update_seo_meta(self, meta_title: str = None, 
                       meta_description: str = None,
                       meta_keywords: str = None) -> None:
        """
        Update SEO metadata.
        
        Args:
            meta_title: SEO meta title
            meta_description: SEO meta description
            meta_keywords: SEO keywords
        """
        if meta_title is not None:
            self.meta_title = meta_title[:60]  # Truncate for SEO
        
        if meta_description is not None:
            self.meta_description = meta_description[:160]  # Truncate for SEO
        
        if meta_keywords is not None:
            self.meta_keywords = meta_keywords
        
        self.updated_at = datetime.utcnow()
    
    @property
    def is_published(self) -> bool:
        """Check if article is published."""
        return self.status == ArticleStatus.PUBLISHED.value
    
    @property
    def is_draft(self) -> bool:
        """Check if article is in draft status."""
        return self.status == ArticleStatus.DRAFT.value
    
    @property
    def is_scheduled(self) -> bool:
        """Check if article is scheduled for future publication."""
        return (self.scheduled_for is not None and 
                self.scheduled_for > datetime.utcnow())
    
    @property
    def reading_time_text(self) -> str:
        """Get human-readable reading time."""
        if self.reading_time_minutes <= 1:
            return "1 min read"
        return f"{self.reading_time_minutes} min read"
    
    @classmethod
    def find_by_slug(cls, session: Session, slug: str) -> Optional['Article']:
        """
        Find article by slug.
        
        Args:
            session: SQLAlchemy session
            slug: Article slug
            
        Returns:
            Article instance or None
        """
        return cls.get_active_query(session).filter(cls.slug == slug).first()
    
    @classmethod
    def find_published(cls, session: Session) -> List['Article']:
        """
        Find all published articles.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List of published articles
        """
        return (cls.get_active_query(session)
                .filter(cls.status == ArticleStatus.PUBLISHED.value)
                .order_by(cls.published_at.desc())
                .all())
    
    @classmethod
    def find_by_author(cls, session: Session, author_id: uuid.UUID) -> List['Article']:
        """
        Find articles by author.
        
        Args:
            session: SQLAlchemy session
            author_id: Author user ID
            
        Returns:
            List of articles by the author
        """
        return (cls.get_active_query(session)
                .filter(cls.author_id == author_id)
                .order_by(cls.created_at.desc())
                .all())
    
    @classmethod
    def find_by_workspace(cls, session: Session, workspace_id: uuid.UUID) -> List['Article']:
        """
        Find articles in a workspace.
        
        Args:
            session: SQLAlchemy session
            workspace_id: Workspace ID
            
        Returns:
            List of articles in the workspace
        """
        return (cls.get_active_query(session)
                .filter(cls.workspace_id == workspace_id)
                .order_by(cls.created_at.desc())
                .all())
    
    @classmethod
    def find_featured(cls, session: Session, limit: int = 10) -> List['Article']:
        """
        Find featured articles.
        
        Args:
            session: SQLAlchemy session
            limit: Maximum number of articles to return
            
        Returns:
            List of featured articles
        """
        return (cls.get_active_query(session)
                .filter(cls.is_featured == True,
                       cls.status == ArticleStatus.PUBLISHED.value)
                .order_by(cls.published_at.desc())
                .limit(limit)
                .all())
    
    def to_dict(self, include_content: bool = True, 
                include_stats: bool = False) -> Dict[str, Any]:
        """
        Convert article to dictionary.
        
        Args:
            include_content: Whether to include full content
            include_stats: Whether to include engagement statistics
            
        Returns:
            Dict[str, Any]: Article data
        """
        result = super().to_dict()
        
        # Add computed fields
        result.update({
            'is_published': self.is_published,
            'is_draft': self.is_draft,
            'is_scheduled': self.is_scheduled,
            'reading_time_text': self.reading_time_text
        })
        
        # Exclude content if not requested (for lists)
        if not include_content:
            result.pop('content', None)
        
        # Include stats if requested
        if include_stats:
            result.update({
                'engagement_score': self.view_count + (self.like_count * 5) + (self.comment_count * 10)
            })
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the article."""
        return f"<Article(title='{self.title}', slug='{self.slug}', status='{self.status}')>"