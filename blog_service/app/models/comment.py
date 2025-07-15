"""
Comment model module for the Blog Microservice.

This module defines the Comment model with content moderation,
threading, and relationship management.

Classes:
    CommentStatus: Enumeration for comment status
    Comment: Comment entity with content and moderation
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class CommentStatus(Enum):
    """
    Enumeration defining possible comment statuses.
    
    Values:
        PENDING: Comment is pending moderation
        APPROVED: Comment is approved and visible
        REJECTED: Comment is rejected and hidden
        SPAM: Comment is marked as spam
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SPAM = "spam"


class Comment(BaseModel):
    """
    Comment model representing comments on blog articles.
    
    This model handles comment content, moderation status,
    threading capabilities, and relationships with users and articles.
    
    Attributes:
        content: Comment content/text
        status: Current moderation status
        is_edited: Whether the comment has been edited
        author_id: Foreign key to the User who wrote the comment
        article_id: Foreign key to the Article the comment belongs to
        parent_id: Foreign key to parent comment for threading
        author: Relationship to the User model
        article: Relationship to the Article model
        parent: Relationship to parent Comment
        replies: List of reply comments
        author_name: Name of the comment author (for non-registered users)
        author_email: Email of the comment author (for non-registered users)
        ip_address: IP address of the commenter (for moderation)
    
    Methods:
        approve: Approve the comment
        reject: Reject the comment
        mark_as_spam: Mark the comment as spam
        validate_content: Validate comment content
        is_reply: Check if comment is a reply to another comment
        get_thread_depth: Get the depth of the comment in thread
        mark_as_edited: Mark the comment as edited
    """
    
    __tablename__ = 'comments'
    
    # Comment content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Comment content/text"
    )
    
    # Moderation
    status: Mapped[CommentStatus] = mapped_column(
        SQLEnum(CommentStatus),
        default=CommentStatus.PENDING,
        nullable=False,
        index=True,
        doc="Current moderation status"
    )
    
    is_edited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the comment has been edited"
    )
    
    # Foreign Keys
    author_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="Foreign key to the User who wrote the comment"
    )
    
    article_id: Mapped[int] = mapped_column(
        ForeignKey('articles.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Foreign key to the Article the comment belongs to"
    )
    
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('comments.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
        doc="Foreign key to parent comment for threading"
    )
    
    # Guest user information (for non-registered commenters)
    author_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Name of the comment author (for non-registered users)"
    )
    
    author_email: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True,
        doc="Email of the comment author (for non-registered users)"
    )
    
    # Moderation information
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 compatible
        nullable=True,
        doc="IP address of the commenter (for moderation)"
    )
    
    # Relationships
    author: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="comments",
        doc="Relationship to the User model"
    )
    
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="comments",
        doc="Relationship to the Article model"
    )
    
    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment",
        remote_side="Comment.id",
        back_populates="replies",
        doc="Relationship to parent Comment"
    )
    
    replies: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",
        doc="List of reply comments"
    )
    
    # Database constraints
    __table_args__ = (
        CheckConstraint(
            "length(content) >= 1",
            name="content_not_empty"
        ),
        CheckConstraint(
            "length(content) <= 2000",
            name="content_max_length"
        ),
        CheckConstraint(
            "(author_id IS NOT NULL) OR (author_name IS NOT NULL AND author_email IS NOT NULL)",
            name="author_required"
        ),
    )
    
    def __init__(self, content: str, article_id: int, **kwargs):
        """
        Initialize a new Comment instance.
        
        Args:
            content: Comment content
            article_id: ID of the article the comment belongs to
            **kwargs: Additional comment attributes
        
        Raises:
            ValueError: If validation fails for content or required fields
        """
        # Validate required fields
        self.validate_content(content)
        
        # Set basic attributes
        self.content = content.strip()
        self.article_id = article_id
        
        # Set additional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Validate author information
        if not self.author_id and (not self.author_name or not self.author_email):
            raise ValueError(
                "Either author_id or both author_name and author_email must be provided"
            )
    
    def approve(self) -> 'Comment':
        """
        Approve the comment for public display.
        
        Returns:
            The updated comment instance
            
        Example:
            comment.approve()
        """
        self.status = CommentStatus.APPROVED
        return self
    
    def reject(self) -> 'Comment':
        """
        Reject the comment, hiding it from public display.
        
        Returns:
            The updated comment instance
            
        Example:
            comment.reject()
        """
        self.status = CommentStatus.REJECTED
        return self
    
    def mark_as_spam(self) -> 'Comment':
        """
        Mark the comment as spam.
        
        Returns:
            The updated comment instance
            
        Example:
            comment.mark_as_spam()
        """
        self.status = CommentStatus.SPAM
        return self
    
    def mark_as_edited(self) -> 'Comment':
        """
        Mark the comment as edited.
        
        Returns:
            The updated comment instance
            
        Example:
            comment.mark_as_edited()
        """
        self.is_edited = True
        return self
    
    @staticmethod
    def validate_content(content: str) -> bool:
        """
        Validate comment content.
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is valid
            
        Raises:
            ValueError: If content doesn't meet requirements
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        
        if len(content.strip()) > 2000:
            raise ValueError("Comment content must be less than 2000 characters")
        
        # Check for potential spam patterns
        if content.lower().count('http') > 3:
            raise ValueError("Comment contains too many links")
        
        return True
    
    def is_reply(self) -> bool:
        """
        Check if this comment is a reply to another comment.
        
        Returns:
            True if this is a reply comment
        """
        return self.parent_id is not None
    
    def get_thread_depth(self) -> int:
        """
        Get the depth of this comment in the thread hierarchy.
        
        Returns:
            Thread depth (0 for top-level comments)
            
        Note:
            This method calculates depth by traversing up the parent chain.
            In a production system, you might want to cache this value.
        """
        depth = 0
        current = self
        
        # Traverse up the parent chain to calculate depth
        while current.parent_id:
            depth += 1
            # In a real implementation, you'd query the database
            # For now, we'll limit depth to prevent infinite loops
            if depth > 10:  # Maximum reasonable thread depth
                break
            current = current.parent
        
        return depth
    
    def is_approved(self) -> bool:
        """
        Check if the comment is approved for public display.
        
        Returns:
            True if the comment is approved
        """
        return self.status == CommentStatus.APPROVED
    
    def get_author_display_name(self) -> str:
        """
        Get the display name for the comment author.
        
        Returns:
            Author display name (registered user's name or guest name)
        """
        if self.author:
            return self.author.get_full_name()
        elif self.author_name:
            return self.author_name
        else:
            return "Anonymous"
    
    def validate_data(self) -> bool:
        """
        Comprehensive validation of comment data.
        
        Returns:
            True if all data is valid
            
        Raises:
            ValueError: If any validation fails
        """
        self.validate_content(self.content)
        
        # Validate guest author information
        if not self.author_id:
            if not self.author_name or not self.author_email:
                raise ValueError(
                    "Guest comments must have both author_name and author_email"
                )
            
            if len(self.author_name) > 100:
                raise ValueError("Author name must be less than 100 characters")
            
            # Basic email validation for guest users
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.author_email):
                raise ValueError("Invalid email format for guest author")
        
        return True
    
    def to_dict(self, include_sensitive: bool = False, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert comment to dictionary with additional computed fields.
        
        Args:
            include_sensitive: Whether to include sensitive information like IP address
            exclude: Additional fields to exclude
            
        Returns:
            Dictionary representation of the comment
        """
        exclude = exclude or []
        if not include_sensitive:
            exclude.extend(['ip_address', 'author_email'])
        
        result = super().to_dict(exclude=exclude)
        
        # Add computed fields
        result['is_reply'] = self.is_reply()
        result['is_approved'] = self.is_approved()
        result['thread_depth'] = self.get_thread_depth()
        result['author_display_name'] = self.get_author_display_name()
        result['reply_count'] = len(self.replies) if self.replies else 0
        
        # Add author information
        if self.author:
            result['author_username'] = self.author.username
            result['author_verified'] = self.author.is_verified
        
        return result
    
    def __repr__(self) -> str:
        """
        String representation of the Comment instance.
        
        Returns:
            String representation including content preview and status
        """
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Comment(content='{content_preview}', status='{self.status.value}')>"