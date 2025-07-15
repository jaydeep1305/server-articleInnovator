"""
User model module for authentication and user management.

This module defines the User and UserProfile models that handle user authentication,
profile information, and user-related business logic. The models are designed
to support JWT authentication and comprehensive user management features.

Author: AI Assistant
Date: 2024
"""

import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash

from .base import BaseModel


class User(BaseModel):
    """
    User model for authentication and basic user information.
    
    This model handles user authentication, stores essential user data,
    and provides methods for password management and user validation.
    It serves as the core entity for the user management microservice.
    
    Attributes:
        email (str): Unique email address for the user
        username (str): Unique username for the user
        password_hash (str): Hashed password for security
        first_name (str): User's first name
        last_name (str): User's last name
        is_active (bool): Whether the user account is active
        is_verified (bool): Whether the email is verified
        last_login (datetime): Timestamp of last login
        failed_login_attempts (int): Counter for failed login attempts
        lockout_until (datetime): Account lockout timestamp
        
    Relationships:
        profile: One-to-one relationship with UserProfile
        workspaces: Many-to-many relationship with Workspace through WorkspaceUser
        roles: Many-to-many relationship with Role through UserRole
    """
    
    __tablename__ = 'users'
    
    # Core authentication fields
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique email address for authentication"
    )
    
    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for the user"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Hashed password for security"
    )
    
    # Personal information
    first_name = Column(
        String(100),
        nullable=True,
        comment="User's first name"
    )
    
    last_name = Column(
        String(100),
        nullable=True,
        comment="User's last name"
    )
    
    # Account status and security
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user account is active"
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the email address is verified"
    )
    
    last_login = Column(
        DateTime,
        nullable=True,
        comment="Timestamp of the last successful login"
    )
    
    failed_login_attempts = Column(
        String(10),
        default="0",
        nullable=False,
        comment="Number of consecutive failed login attempts"
    )
    
    lockout_until = Column(
        DateTime,
        nullable=True,
        comment="Timestamp until which the account is locked"
    )
    
    # Relationships
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Note: workspace_users and user_roles relationships would be defined 
    # in their respective models to avoid circular imports
    
    def __init__(self, email: str, username: str, password: str, **kwargs) -> None:
        """
        Initialize a new user instance.
        
        Args:
            email: User's email address
            username: User's chosen username
            password: Plain text password (will be hashed)
            **kwargs: Additional user attributes
            
        Raises:
            ValueError: If email or username format is invalid
        """
        super().__init__(**kwargs)
        
        self.email = email.lower().strip()
        self.username = username.lower().strip()
        self.set_password(password)
        
        # Validate during initialization
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"User validation failed: {', '.join(errors)}")
    
    def set_password(self, password: str) -> None:
        """
        Set user password with proper hashing.
        
        This method hashes the provided password using Werkzeug's secure
        password hashing algorithm and stores it in the password_hash field.
        
        Args:
            password: Plain text password to hash and store
            
        Raises:
            ValueError: If password doesn't meet security requirements
            
        Example:
            >>> user.set_password("secure_password123")
            >>> print(user.check_password("secure_password123"))  # True
        """
        if not self._validate_password_strength(password):
            raise ValueError(
                "Password must be at least 8 characters long and contain "
                "at least one uppercase letter, one lowercase letter, and one number"
            )
        
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
            
        Example:
            >>> user.check_password("correct_password")  # True
            >>> user.check_password("wrong_password")    # False
        """
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self) -> bool:
        """
        Check if the user account is currently locked.
        
        Returns:
            bool: True if account is locked, False otherwise
            
        Example:
            >>> if user.is_account_locked():
            ...     return {"error": "Account is temporarily locked"}
        """
        if self.lockout_until is None:
            return False
        
        return datetime.utcnow() < self.lockout_until
    
    def increment_failed_login(self) -> None:
        """
        Increment failed login attempts and lock account if necessary.
        
        This method implements account security by tracking failed login
        attempts and temporarily locking the account after too many failures.
        """
        current_attempts = int(self.failed_login_attempts or "0")
        current_attempts += 1
        self.failed_login_attempts = str(current_attempts)
        
        # Lock account after 5 failed attempts for 30 minutes
        if current_attempts >= 5:
            from datetime import timedelta
            self.lockout_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_login(self) -> None:
        """
        Reset failed login attempts after successful authentication.
        """
        self.failed_login_attempts = "0"
        self.lockout_until = None
        self.last_login = datetime.utcnow()
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate user data according to business rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
            
        Example:
            >>> user = User(email="invalid", username="a", password="weak")
            >>> is_valid, errors = user.validate()
            >>> print(errors)  # ["Invalid email format", "Username too short"]
        """
        is_valid, errors = super().validate()
        
        # Email validation
        if not self._validate_email(self.email):
            errors.append("Invalid email format")
        
        # Username validation
        if not self._validate_username(self.username):
            errors.append("Username must be 3-30 characters long and contain only letters, numbers, and underscores")
        
        # Name validation
        if self.first_name and len(self.first_name.strip()) == 0:
            errors.append("First name cannot be empty if provided")
        
        if self.last_name and len(self.last_name.strip()) == 0:
            errors.append("Last name cannot be empty if provided")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """
        Validate email address format using regex.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email format is valid
        """
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    @staticmethod
    def _validate_username(username: str) -> bool:
        """
        Validate username format and length.
        
        Args:
            username: Username to validate
            
        Returns:
            bool: True if username format is valid
        """
        if not username or len(username) < 3 or len(username) > 30:
            return False
        
        username_pattern = r'^[a-zA-Z0-9_]+$'
        return re.match(username_pattern, username) is not None
    
    @staticmethod
    def _validate_password_strength(password: str) -> bool:
        """
        Validate password strength requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if password meets strength requirements
        """
        if not password or len(password) < 8:
            return False
        
        # Check for at least one uppercase, one lowercase, and one number
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit
    
    @property
    def full_name(self) -> str:
        """
        Get user's full name.
        
        Returns:
            str: Formatted full name or email if names not provided
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email
    
    @classmethod
    def find_by_email(cls, session: Session, email: str) -> Optional['User']:
        """
        Find user by email address.
        
        Args:
            session: SQLAlchemy session
            email: Email address to search for
            
        Returns:
            User instance or None if not found
        """
        return cls.get_active_query(session).filter(
            cls.email == email.lower().strip()
        ).first()
    
    @classmethod
    def find_by_username(cls, session: Session, username: str) -> Optional['User']:
        """
        Find user by username.
        
        Args:
            session: SQLAlchemy session
            username: Username to search for
            
        Returns:
            User instance or None if not found
        """
        return cls.get_active_query(session).filter(
            cls.username == username.lower().strip()
        ).first()
    
    def to_dict(self, include_relationships: bool = False, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert user to dictionary, excluding sensitive information by default.
        
        Args:
            include_relationships: Whether to include related objects
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dict[str, Any]: User data dictionary
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Remove sensitive information unless explicitly requested
        if not include_sensitive:
            sensitive_fields = ['password_hash', 'failed_login_attempts', 'lockout_until']
            for field in sensitive_fields:
                result.pop(field, None)
        
        # Add computed fields
        result['full_name'] = self.full_name
        result['is_locked'] = self.is_account_locked()
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(email='{self.email}', username='{self.username}')>"


class UserProfile(BaseModel):
    """
    Extended user profile information.
    
    This model stores additional user information that doesn't belong
    in the core User model, such as profile pictures, bio, preferences,
    and other extended attributes.
    
    Attributes:
        user_id (UUID): Foreign key to User model
        bio (str): User's biography or description
        profile_picture_url (str): URL to user's profile picture
        phone_number (str): User's phone number
        birth_date (date): User's birth date
        timezone (str): User's preferred timezone
        language (str): User's preferred language
        receive_notifications (bool): Whether user wants to receive notifications
        
    Relationships:
        user: One-to-one relationship with User
    """
    
    __tablename__ = 'user_profiles'
    
    # Foreign key to User
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        comment="Reference to the user this profile belongs to"
    )
    
    # Extended profile information
    bio = Column(
        Text,
        nullable=True,
        comment="User's biography or description"
    )
    
    profile_picture_url = Column(
        String(500),
        nullable=True,
        comment="URL to user's profile picture"
    )
    
    phone_number = Column(
        String(20),
        nullable=True,
        comment="User's phone number"
    )
    
    birth_date = Column(
        Date,
        nullable=True,
        comment="User's birth date"
    )
    
    timezone = Column(
        String(50),
        default='UTC',
        nullable=False,
        comment="User's preferred timezone"
    )
    
    language = Column(
        String(10),
        default='en',
        nullable=False,
        comment="User's preferred language code"
    )
    
    receive_notifications = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether user wants to receive notifications"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="profile",
        lazy="select"
    )
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate user profile data.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        is_valid, errors = super().validate()
        
        # Phone number validation
        if self.phone_number and not self._validate_phone_number(self.phone_number):
            errors.append("Invalid phone number format")
        
        # Birth date validation
        if self.birth_date and self.birth_date > date.today():
            errors.append("Birth date cannot be in the future")
        
        # Bio length validation
        if self.bio and len(self.bio) > 1000:
            errors.append("Bio cannot exceed 1000 characters")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_phone_number(phone: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            bool: True if phone number format is valid
        """
        if not phone:
            return False
        
        # Simple phone number validation (international format)
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        return re.match(phone_pattern, clean_phone) is not None
    
    @property
    def age(self) -> Optional[int]:
        """
        Calculate user's age from birth date.
        
        Returns:
            int: User's age in years, or None if birth_date not set
        """
        if not self.birth_date:
            return None
        
        today = date.today()
        age = today.year - self.birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.birth_date.month or \
           (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        
        return age
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert profile to dictionary with computed fields.
        
        Args:
            include_relationships: Whether to include related objects
            
        Returns:
            Dict[str, Any]: Profile data dictionary
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Add computed fields
        result['age'] = self.age
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the user profile."""
        return f"<UserProfile(user_id='{self.user_id}')>"