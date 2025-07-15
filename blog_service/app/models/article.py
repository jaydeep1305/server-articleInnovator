"""
Article model module for the Blog Microservice.

This module defines the Article model with content management,
categorization, and relationship handling.

Classes:
    ArticleStatus: Enumeration for article status
    Article: Article entity with content and metadata
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SQLEnum, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class ArticleStatus(Enum):
    """
    Enumeration defining possible article statuses.
    
    Values:
        DRAFT: Article is in draft state
        PUBLISHED: Article is published and visible
        ARCHIVED: Article is archived and hidden
        DELETED: Article is marked for deletion
    """
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Article(BaseModel):
    """
    Article model representing blog posts in the system.
    
    This model handles article content, metadata, publishing status,
    and relationships with users and comments.
    
    Attributes:
        title: Article title
        content: Article content/body
        excerpt: Short description or summary
        slug: URL-friendly version of the title
        status: Current publication status
        is_featured: Whether the article is featured
        view_count: Number of times the article has been viewed
        author_id: Foreign key to the User who authored the article
        author: Relationship to the User model
        comments: List of comments on this article
        tags: Comma-separated list of tags
        category: Article category
        published_at: Timestamp when the article was published
        meta_title: SEO meta title
        meta_description: SEO meta description
    
    Methods:
        publish: Publish the article
        unpublish: Unpublish the article
        archive: Archive the article
        validate_content: Validate article content
        generate_slug: Generate URL-friendly slug
        get_tags_list: Get tags as a list
        set_tags_list: Set tags from a list
        increment_view_count: Increment the view counter
    """
    
    __tablename__ = 'articles'
    
    # Article content
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Article title"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Article content/body"
    )
    
    excerpt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Short description or summary of the article"
    )
    
    slug: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        nullable=False,
        index=True,
        doc="URL-friendly version of the title"
    )
    
    # Article metadata
    status: Mapped[ArticleStatus] = mapped_column(
        SQLEnum(ArticleStatus),
        default=ArticleStatus.DRAFT,
        nullable=False,
        index=True,
        doc="Current publication status"
    )
    
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the article is featured"
    )
    
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of times the article has been viewed"
    )
    
    # Categorization
    tags: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Comma-separated list of tags"
    )
    
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Article category"
    )
    
    # Publishing information
    published_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        doc="Timestamp when the article was published"
    )
    
    # SEO fields
    meta_title: Mapped[Optional[str]] = mapped_column(
        String(60),
        nullable=True,
        doc="SEO meta title"
    )
    
    meta_description: Mapped[Optional[str]] = mapped_column(
        String(160),
        nullable=True,
        doc="SEO meta description"
    )
    
    # Foreign Keys
    author_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to the User who authored the article"
    )
    
    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="articles",
        doc="Relationship to the User model"
    )
    
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="List of comments on this article"
    )
    
    # Database constraints
    __table_args__ = (
        CheckConstraint(
            "length(title) >= 1",
            name="title_not_empty"
        ),
        CheckConstraint(
            "length(content) >= 10",
            name="content_min_length"
        ),
        CheckConstraint(
            "view_count >= 0",
            name="view_count_non_negative"
        ),
    )
    
    def __init__(self, title: str, content: str, author_id: int, **kwargs):
        """
        Initialize a new Article instance.
        
        Args:
            title: Article title
            content: Article content
            author_id: ID of the author
            **kwargs: Additional article attributes
        
        Raises:
            ValueError: If validation fails for title or content
        """
        # Validate required fields
        self.validate_title(title)
        self.validate_content(content)
        
        # Set basic attributes
        self.title = title.strip()
        self.content = content.strip()
        self.author_id = author_id
        
        # Generate slug if not provided
        if 'slug' not in kwargs:
            self.slug = self.generate_slug(title)
        
        # Set additional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def publish(self) -> 'Article':
        """
        Publish the article.
        
        Sets the status to PUBLISHED and records the publication timestamp.
        
        Returns:
            The updated article instance
            
        Example:
            article.publish()
        """
        self.status = ArticleStatus.PUBLISHED
        if not self.published_at:
            self.published_at = datetime.utcnow()
        return self
    
    def unpublish(self) -> 'Article':
        """
        Unpublish the article by setting status to DRAFT.
        
        Returns:
            The updated article instance
            
        Example:
            article.unpublish()
        """
        self.status = ArticleStatus.DRAFT
        return self
    
    def archive(self) -> 'Article':
        """
        Archive the article by setting status to ARCHIVED.
        
        Returns:
            The updated article instance
            
        Example:
            article.archive()
        """
        self.status = ArticleStatus.ARCHIVED
        return self
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """
        Validate article title.
        
        Args:
            title: Title to validate
            
        Returns:
            True if title is valid
            
        Raises:
            ValueError: If title doesn't meet requirements
        """
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        
        if len(title.strip()) > 200:
            raise ValueError("Title must be less than 200 characters")
        
        return True
    
    @staticmethod
    def validate_content(content: str) -> bool:
        """
        Validate article content.
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is valid
            
        Raises:
            ValueError: If content doesn't meet requirements
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
        
        if len(content.strip()) < 10:
            raise ValueError("Content must be at least 10 characters long")
        
        return True
    
    @staticmethod
    def generate_slug(title: str) -> str:
        """
        Generate a URL-friendly slug from the title.
        
        Args:
            title: Article title
            
        Returns:
            URL-friendly slug
            
        Example:
            Article.generate_slug("Hello World!") # Returns "hello-world"
        """
        import re
        import uuid
        
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure slug is not empty and not too long
        if not slug:
            slug = f"article-{uuid.uuid4().hex[:8]}"
        elif len(slug) > 200:
            slug = slug[:200].rstrip('-')
        
        return slug
    
    def get_tags_list(self) -> List[str]:
        """
        Get tags as a list of strings.
        
        Returns:
            List of tag strings
            
        Example:
            article.get_tags_list()  # Returns ["python", "flask", "api"]
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def set_tags_list(self, tags: List[str]) -> None:
        """
        Set tags from a list of strings.
        
        Args:
            tags: List of tag strings
            
        Example:
            article.set_tags_list(["python", "flask", "api"])
        """
        if tags:
            # Clean and filter tags
            clean_tags = [tag.strip().lower() for tag in tags if tag.strip()]
            self.tags = ','.join(clean_tags) if clean_tags else None
        else:
            self.tags = None
    
    def increment_view_count(self) -> 'Article':
        """
        Increment the article view count.
        
        Returns:
            The updated article instance
            
        Example:
            article.increment_view_count()
        """
        self.view_count += 1
        return self
    
    def is_published(self) -> bool:
        """
        Check if the article is published.
        
        Returns:
            True if the article is published
        """
        return self.status == ArticleStatus.PUBLISHED
    
    def get_reading_time(self) -> int:
        """
        Estimate reading time in minutes based on content length.
        
        Returns:
            Estimated reading time in minutes
            
        Note:
            Assumes average reading speed of 200 words per minute
        """
        if not self.content:
            return 0
        
        word_count = len(self.content.split())
        reading_time = max(1, round(word_count / 200))
        return reading_time
    
    def validate_data(self) -> bool:
        """
        Comprehensive validation of article data.
        
        Returns:
            True if all data is valid
            
        Raises:
            ValueError: If any validation fails
        """
        self.validate_title(self.title)
        self.validate_content(self.content)
        
        # Validate optional fields
        if self.excerpt and len(self.excerpt) > 500:
            raise ValueError("Excerpt must be less than 500 characters")
        
        if self.category and len(self.category) > 100:
            raise ValueError("Category must be less than 100 characters")
        
        if self.meta_title and len(self.meta_title) > 60:
            raise ValueError("Meta title must be less than 60 characters")
        
        if self.meta_description and len(self.meta_description) > 160:
            raise ValueError("Meta description must be less than 160 characters")
        
        return True
    
    def to_dict(self, include_content: bool = True, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert article to dictionary with additional computed fields.
        
        Args:
            include_content: Whether to include the full content
            exclude: Additional fields to exclude
            
        Returns:
            Dictionary representation of the article
        """
        exclude = exclude or []
        if not include_content:
            exclude.append('content')
        
        result = super().to_dict(exclude=exclude)
        
        # Add computed fields
        result['reading_time'] = self.get_reading_time()
        result['tags_list'] = self.get_tags_list()
        result['comment_count'] = self.comments.count() if self.comments else 0
        result['is_published'] = self.is_published()
        
        # Add author information if available
        if hasattr(self, 'author') and self.author:
            result['author_name'] = self.author.get_full_name()
            result['author_username'] = self.author.username
        
        return result
    
    def __repr__(self) -> str:
        """
        String representation of the Article instance.
        
        Returns:
            String representation including title and status
        """
        return f"<Article(title='{self.title}', status='{self.status.value}')>"