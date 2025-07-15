"""
User model module for the Blog Microservice.

This module defines the User model with comprehensive validation,
security features, and relationship management.

Classes:
    User: User entity with authentication and profile management
"""

import re
from typing import Optional, List
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import String, Text, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class User(BaseModel):
    """
    User model representing registered users in the blog system.
    
    This model handles user authentication, profile management,
    and relationships with articles and comments.
    
    Attributes:
        username: Unique username for the user
        email: Unique email address for the user
        password_hash: Hashed password for authentication
        first_name: User's first name
        last_name: User's last name
        bio: User's biography/description
        is_active: Whether the user account is active
        is_verified: Whether the user's email is verified
        articles: List of articles written by the user
        comments: List of comments made by the user
    
    Methods:
        set_password: Hash and set user password
        check_password: Verify user password
        validate_email: Validate email format
        validate_username: Validate username format
        get_full_name: Get user's full name
        validate_data: Comprehensive data validation
    """
    
    __tablename__ = 'users'
    
    # User identification and authentication
    username: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username for the user"
    )
    
    email: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique email address for the user"
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Hashed password for authentication"
    )
    
    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="User's first name"
    )
    
    last_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="User's last name"
    )
    
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User's biography or description"
    )
    
    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the user account is active"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user's email is verified"
    )
    
    # Relationships
    articles: Mapped[List["Article"]] = relationship(
        "Article",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="List of articles written by the user"
    )
    
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="List of comments made by the user"
    )
    
    # Database constraints
    __table_args__ = (
        CheckConstraint(
            "length(username) >= 3",
            name="username_min_length"
        ),
        CheckConstraint(
            "length(email) >= 5",
            name="email_min_length"
        ),
        CheckConstraint(
            "email LIKE '%@%'",
            name="email_format"
        ),
    )
    
    def __init__(self, username: str, email: str, password: str, **kwargs):
        """
        Initialize a new User instance.
        
        Args:
            username: Unique username for the user
            email: Email address for the user
            password: Plain text password (will be hashed)
            **kwargs: Additional user attributes
        
        Raises:
            ValueError: If validation fails for username, email, or password
        """
        # Validate input data
        self.validate_username(username)
        self.validate_email(email)
        self.validate_password(password)
        
        # Set validated attributes
        self.username = username.lower().strip()
        self.email = email.lower().strip()
        self.set_password(password)
        
        # Set additional attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password.
        
        Args:
            password: Plain text password to hash
            
        Raises:
            ValueError: If password doesn't meet requirements
            
        Example:
            user.set_password('secure_password123')
        """
        self.validate_password(password)
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Verify the user's password against the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
            
        Example:
            if user.check_password('user_input_password'):
                # Authenticate user
                pass
        """
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid
            
        Raises:
            ValueError: If email format is invalid
            
        Example:
            User.validate_email('user@example.com')  # Returns True
            User.validate_email('invalid-email')     # Raises ValueError
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email or len(email) < 5:
            raise ValueError("Email must be at least 5 characters long")
        
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 120:
            raise ValueError("Email must be less than 120 characters")
        
        return True
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate username format and requirements.
        
        Args:
            username: Username to validate
            
        Returns:
            True if username is valid
            
        Raises:
            ValueError: If username doesn't meet requirements
            
        Example:
            User.validate_username('john_doe')      # Returns True
            User.validate_username('ab')            # Raises ValueError
        """
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if len(username) > 80:
            raise ValueError("Username must be less than 80 characters")
        
        # Allow alphanumeric characters, underscores, and hyphens
        username_pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(username_pattern, username):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        
        return True
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """
        Validate password strength and requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements
            
        Raises:
            ValueError: If password doesn't meet requirements
            
        Example:
            User.validate_password('SecurePass123!')  # Returns True
            User.validate_password('weak')            # Raises ValueError
        """
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if len(password) > 128:
            raise ValueError("Password must be less than 128 characters")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one number")
        
        return True
    
    def get_full_name(self) -> str:
        """
        Get the user's full name.
        
        Returns:
            Full name if first_name and last_name are set, otherwise username
            
        Example:
            user.get_full_name()  # Returns "John Doe" or "john_doe"
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    def validate_data(self) -> bool:
        """
        Comprehensive validation of all user data.
        
        Returns:
            True if all data is valid
            
        Raises:
            ValueError: If any validation fails
            
        Note:
            This method performs validation on all user attributes
            and is typically called before saving to the database.
        """
        self.validate_username(self.username)
        self.validate_email(self.email)
        
        # Validate profile information
        if self.first_name and len(self.first_name) > 50:
            raise ValueError("First name must be less than 50 characters")
        
        if self.last_name and len(self.last_name) > 50:
            raise ValueError("Last name must be less than 50 characters")
        
        if self.bio and len(self.bio) > 1000:
            raise ValueError("Bio must be less than 1000 characters")
        
        return True
    
    def to_dict(self, exclude: Optional[List[str]] = None) -> dict:
        """
        Convert user to dictionary, excluding sensitive information by default.
        
        Args:
            exclude: Additional fields to exclude
            
        Returns:
            Dictionary representation of the user
        """
        default_exclude = ['password_hash']
        if exclude:
            default_exclude.extend(exclude)
        
        result = super().to_dict(exclude=default_exclude)
        result['full_name'] = self.get_full_name()
        result['article_count'] = self.articles.count() if self.articles else 0
        result['comment_count'] = self.comments.count() if self.comments else 0
        
        return result
    
    def __repr__(self) -> str:
        """
        String representation of the User instance.
        
        Returns:
            String representation including username and email
        """
        return f"<User(username='{self.username}', email='{self.email}')>"