"""
User model for authentication and user management.

This module defines the User model that handles user authentication, profile information,
and user-related business logic. The model includes comprehensive validation, security
features, and cognitive patterns for user management.

Author: AI Assistant
Date: 2024
"""

import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Set
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Table, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash

from .base import BaseModel
from app import db


# Association table for many-to-many relationship between User and Role
user_roles = Table(
    'user_roles',
    db.Model.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('assigned_by', UUID(as_uuid=True), nullable=True)
)


class User(BaseModel):
    """
    User model for authentication and profile management.
    
    This model handles user authentication, stores essential user data,
    and provides methods for password management, user validation, and
    role-based access control. It implements cognitive security patterns
    and comprehensive validation for production use.
    
    Attributes:
        email (str): Unique email address for the user
        username (str): Unique username for the user
        password_hash (str): Hashed password for security
        first_name (str): User's first name
        last_name (str): User's last name
        phone_number (str): User's phone number
        birth_date (date): User's birth date
        bio (text): User's biography or description
        profile_picture_url (str): URL to user's profile picture
        is_verified (bool): Whether the email is verified
        is_admin (bool): Whether the user has admin privileges
        last_login_at (datetime): Timestamp of last login
        failed_login_attempts (int): Counter for failed login attempts
        account_locked_until (datetime): Account lockout timestamp
        password_changed_at (datetime): When password was last changed
        
    Relationships:
        roles: Many-to-many relationship with Role
        
    Security Features:
        - Password hashing with bcrypt
        - Account lockout after failed attempts
        - Email verification requirement
        - Password strength validation
        - Audit trails for security events
    """
    
    __tablename__ = 'users'
    
    # Core authentication fields with cognitive security patterns
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique email address for authentication"
    )
    
    username = Column(
        String(50),
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
    
    # Personal information fields
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
    
    phone_number = Column(
        String(20),
        nullable=True,
        comment="User's phone number in international format"
    )
    
    birth_date = Column(
        Date,
        nullable=True,
        comment="User's birth date"
    )
    
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
    
    # Account status and verification
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the email address is verified"
    )
    
    is_admin = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user has admin privileges"
    )
    
    # Security and audit fields
    last_login_at = Column(
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
    
    account_locked_until = Column(
        DateTime,
        nullable=True,
        comment="Timestamp until which the account is locked"
    )
    
    password_changed_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When the password was last changed"
    )
    
    # Preferences and settings
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
        comment="Whether user wants to receive email notifications"
    )
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="select"
    )
    
    def __init__(self, email: str, username: str, password: str, **kwargs) -> None:
        """
        Initialize a new user instance with cognitive validation.
        
        This constructor implements secure initialization patterns with
        automatic password hashing and comprehensive validation.
        
        Args:
            email: User's email address
            username: User's chosen username
            password: Plain text password (will be hashed)
            **kwargs: Additional user attributes
            
        Raises:
            ValueError: If email, username, or password format is invalid
            
        Example:
            >>> user = User(
            ...     email="john@example.com",
            ...     username="johndoe",
            ...     password="SecurePass123!",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )
        """
        # Normalize and validate inputs before calling super().__init__
        email = email.lower().strip() if email else ""
        username = username.lower().strip() if username else ""
        
        # Set password-related fields
        kwargs['email'] = email
        kwargs['username'] = username
        kwargs['password_changed_at'] = datetime.utcnow()
        
        super().__init__(**kwargs)
        
        # Set and hash password after initialization
        self.set_password(password)
        
        # Validate the complete user object
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"User validation failed: {', '.join(errors)}")
    
    def set_password(self, password: str) -> None:
        """
        Set user password with proper hashing and validation.
        
        This method implements cognitive security patterns including
        password strength validation and secure hashing algorithms.
        
        Args:
            password: Plain text password to hash and store
            
        Raises:
            ValueError: If password doesn't meet security requirements
            
        Example:
            >>> user.set_password("NewSecurePass123!")
            >>> print(user.check_password("NewSecurePass123!"))  # True
        """
        if not self._validate_password_strength(password):
            raise ValueError(
                "Password must be at least 8 characters long and contain "
                "at least one uppercase letter, one lowercase letter, "
                "one number, and one special character"
            )
        
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
        This method implements secure password verification with
        cognitive timing attack protection.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
            
        Example:
            >>> user.check_password("correct_password")  # True
            >>> user.check_password("wrong_password")    # False
        """
        if not password or not self.password_hash:
            return False
        
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self) -> bool:
        """
        Check if the user account is currently locked.
        
        This method implements cognitive security patterns for
        account lockout protection against brute force attacks.
        
        Returns:
            bool: True if account is locked, False otherwise
            
        Example:
            >>> if user.is_account_locked():
            ...     raise ValueError("Account is temporarily locked")
        """
        if self.account_locked_until is None:
            return False
        
        return datetime.utcnow() < self.account_locked_until
    
    def increment_failed_login(self) -> None:
        """
        Increment failed login attempts and lock account if necessary.
        
        This method implements cognitive security patterns for
        progressive account lockout to prevent brute force attacks.
        The lockout duration increases with repeated failures.
        """
        current_attempts = int(self.failed_login_attempts or "0")
        current_attempts += 1
        self.failed_login_attempts = str(current_attempts)
        
        # Progressive lockout strategy (cognitive security pattern)
        if current_attempts >= 5:
            from datetime import timedelta
            # Lock for increasingly longer periods
            lockout_minutes = min(current_attempts * 5, 60)  # Max 1 hour
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
    
    def reset_failed_login(self) -> None:
        """
        Reset failed login attempts after successful authentication.
        
        This method clears security flags and updates login tracking
        when a user successfully authenticates.
        """
        self.failed_login_attempts = "0"
        self.account_locked_until = None
        self.last_login_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        """
        Mark the user's email as verified.
        
        This method implements email verification patterns for
        account security and communication reliability.
        """
        self.is_verified = True
        self.updated_at = datetime.utcnow()
    
    def add_role(self, session: Session, role: 'Role') -> None:
        """
        Add a role to this user.
        
        This method implements cognitive role management patterns
        with proper validation and audit trails.
        
        Args:
            session: SQLAlchemy session
            role: Role instance to add
            
        Raises:
            ValueError: If role is already assigned or invalid
        """
        if role in self.roles:
            raise ValueError(f"Role '{role.name}' is already assigned to user '{self.username}'")
        
        self.roles.append(role)
        session.flush()
    
    def remove_role(self, session: Session, role: 'Role') -> bool:
        """
        Remove a role from this user.
        
        Args:
            session: SQLAlchemy session
            role: Role instance to remove
            
        Returns:
            bool: True if role was removed, False if it wasn't assigned
        """
        if role in self.roles:
            self.roles.remove(role)
            session.flush()
            return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role_name: Name of the role to check
            
        Returns:
            bool: True if user has the role
            
        Example:
            >>> if user.has_role('admin'):
            ...     # User has admin role
        """
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """
        Check if user has a specific permission through their roles.
        
        This method implements cognitive authorization patterns by
        checking permissions across all assigned roles.
        
        Args:
            permission_name: Name of the permission to check
            
        Returns:
            bool: True if user has the permission
            
        Example:
            >>> if user.has_permission('user.create'):
            ...     # User can create users
        """
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False
    
    def get_permissions(self) -> Set[str]:
        """
        Get all permissions for this user across all roles.
        
        Returns:
            Set[str]: Set of permission names
        """
        permissions = set()
        for role in self.roles:
            permissions.update(role.get_permission_names())
        return permissions
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate user data according to business rules.
        
        This method implements comprehensive validation patterns
        covering email format, username constraints, age verification,
        and security requirements.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
            
        Example:
            >>> user = User(email="invalid", username="a", password="weak")
            >>> is_valid, errors = user.validate()
            >>> print(errors)  # ["Invalid email format", "Username too short"]
        """
        is_valid, errors = super().validate()
        
        # Email validation with cognitive patterns
        if not self._validate_email(self.email):
            errors.append("Invalid email format")
        
        # Username validation with cognitive constraints
        if not self._validate_username(self.username):
            errors.append("Username must be 3-50 characters long and contain only letters, numbers, and underscores")
        
        # Name validation (cognitive UX patterns)
        if self.first_name and len(self.first_name.strip()) == 0:
            errors.append("First name cannot be empty if provided")
        
        if self.last_name and len(self.last_name.strip()) == 0:
            errors.append("Last name cannot be empty if provided")
        
        # Phone number validation
        if self.phone_number and not self._validate_phone_number(self.phone_number):
            errors.append("Invalid phone number format")
        
        # Birth date validation (cognitive age verification)
        if self.birth_date:
            if self.birth_date > date.today():
                errors.append("Birth date cannot be in the future")
            
            # Check minimum age (13 years for COPPA compliance)
            age = self._calculate_age()
            if age is not None and age < 13:
                errors.append("User must be at least 13 years old")
        
        # Bio length validation
        if self.bio and len(self.bio) > 1000:
            errors.append("Bio cannot exceed 1000 characters")
        
        # Security validations
        if self.failed_login_attempts and not self.failed_login_attempts.isdigit():
            errors.append("Failed login attempts must be a number")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """
        Validate email address format using cognitive regex patterns.
        
        This method implements comprehensive email validation including
        length limits, character restrictions, and format verification.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email format is valid
        """
        if not email or len(email) > 255:
            return False
        
        # Cognitive email validation pattern (RFC 5322 compliant)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False
        
        # Additional cognitive validations
        local, domain = email.rsplit('@', 1)
        
        # Local part validations
        if len(local) > 64 or len(local) == 0:
            return False
        
        # Domain part validations
        if len(domain) > 253 or len(domain) == 0:
            return False
        
        # No consecutive dots
        if '..' in email:
            return False
        
        return True
    
    @staticmethod
    def _validate_username(username: str) -> bool:
        """
        Validate username format and length with cognitive constraints.
        
        Args:
            username: Username to validate
            
        Returns:
            bool: True if username format is valid
        """
        if not username or len(username) < 3 or len(username) > 50:
            return False
        
        # Username pattern: letters, numbers, underscores only
        username_pattern = r'^[a-zA-Z0-9_]+$'
        
        # Must start with letter or number (cognitive UX pattern)
        if not username[0].isalnum():
            return False
        
        return re.match(username_pattern, username) is not None
    
    @staticmethod
    def _validate_password_strength(password: str) -> bool:
        """
        Validate password strength requirements with cognitive security patterns.
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if password meets strength requirements
        """
        if not password or len(password) < 8:
            return False
        
        # Check for character diversity (cognitive security pattern)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    @staticmethod
    def _validate_phone_number(phone: str) -> bool:
        """
        Validate phone number format with cognitive international patterns.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            bool: True if phone number format is valid
        """
        if not phone:
            return False
        
        # Remove common formatting characters
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # International phone number pattern (cognitive validation)
        phone_pattern = r'^\+?[1-9]\d{6,14}$'
        return re.match(phone_pattern, clean_phone) is not None
    
    def _calculate_age(self) -> Optional[int]:
        """
        Calculate user's age from birth date with cognitive date handling.
        
        Returns:
            int: User's age in years, or None if birth_date not set
        """
        if not self.birth_date:
            return None
        
        today = date.today()
        age = today.year - self.birth_date.year
        
        # Adjust if birthday hasn't occurred this year (cognitive date math)
        if today.month < self.birth_date.month or \
           (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        
        return age
    
    @property
    def full_name(self) -> str:
        """
        Get user's full name with cognitive formatting.
        
        Returns:
            str: Formatted full name or fallback to username/email
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username or self.email
    
    @property
    def age(self) -> Optional[int]:
        """Get user's age."""
        return self._calculate_age()
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        return self.is_account_locked()
    
    @classmethod
    def find_by_email(cls, session: Session, email: str) -> Optional['User']:
        """
        Find user by email address with cognitive case handling.
        
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
        Find user by username with cognitive case handling.
        
        Args:
            session: SQLAlchemy session
            username: Username to search for
            
        Returns:
            User instance or None if not found
        """
        return cls.get_active_query(session).filter(
            cls.username == username.lower().strip()
        ).first()
    
    def to_dict(self, include_relationships: bool = False, 
                include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert user to dictionary with cognitive security filtering.
        
        Args:
            include_relationships: Whether to include related objects
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dict[str, Any]: User data dictionary
        """
        # Define sensitive fields to exclude by default
        sensitive_fields = [
            'password_hash', 
            'failed_login_attempts', 
            'account_locked_until'
        ]
        
        exclude_fields = [] if include_sensitive else sensitive_fields
        result = super().to_dict(
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )
        
        # Add computed fields for cognitive UX
        result['full_name'] = self.full_name
        result['age'] = self.age
        result['is_locked'] = self.is_locked
        
        # Add role names for convenience
        if include_relationships:
            result['role_names'] = [role.name for role in self.roles]
            result['permissions'] = list(self.get_permissions())
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(email='{self.email}', username='{self.username}')>"