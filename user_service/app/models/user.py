"""
User Model for User Management Microservice.

This module defines the User model with comprehensive validation,
relationships, and security features including password hashing.
"""

import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Table, ForeignKey, Integer
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import bcrypt

from app import db
from .base import BaseModel

# Association table for many-to-many relationship between User and Role
user_roles = Table(
    'user_roles',
    db.Model.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow)
)


class User(BaseModel):
    """
    User model representing system users with authentication and authorization.
    
    This model includes:
    - Unique username and email validation
    - Secure password hashing using bcrypt
    - Account status management (active/inactive)
    - Many-to-many relationship with roles
    - One-to-one relationship with user profile
    
    Attributes:
        username: Unique username for the user (3-50 characters)
        email: Unique email address with format validation
        password_hash: Bcrypt hashed password (never store plain text)
        first_name: User's first name (optional, max 100 characters)
        last_name: User's last name (optional, max 100 characters)
        is_active: Account status flag (default: True)
        is_verified: Email verification status (default: False)
        last_login: Timestamp of last successful login
        failed_login_attempts: Counter for security monitoring
        locked_until: Account lock timestamp for security
    
    Relationships:
        profile: One-to-one relationship with Profile model
        roles: Many-to-many relationship with Role model
    """
    
    __tablename__ = 'users'
    
    # Core user fields with validation
    username = Column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="Unique username (3-50 characters, alphanumeric and underscores only)"
    )
    
    email = Column(
        String(120), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="Unique email address with format validation"
    )
    
    _password_hash = Column(
        'password_hash',
        String(128), 
        nullable=False,
        doc="Bcrypt hashed password (never store plain text)"
    )
    
    # Personal information (optional)
    first_name = Column(
        String(100), 
        nullable=True,
        doc="User's first name (optional, max 100 characters)"
    )
    
    last_name = Column(
        String(100), 
        nullable=True,
        doc="User's last name (optional, max 100 characters)"
    )
    
    # Account status and security
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        doc="Account status flag (default: True)"
    )
    
    is_verified = Column(
        Boolean, 
        default=False, 
        nullable=False,
        doc="Email verification status (default: False)"
    )
    
    last_login = Column(
        DateTime, 
        nullable=True,
        doc="Timestamp of last successful login"
    )
    
    failed_login_attempts = Column(
        Integer, 
        default=0, 
        nullable=False,
        doc="Counter for failed login attempts (security monitoring)"
    )
    
    locked_until = Column(
        DateTime, 
        nullable=True,
        doc="Account lock timestamp for security (None if not locked)"
    )
    
    # Relationships
    profile = relationship(
        "Profile", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan",
        doc="One-to-one relationship with user profile"
    )
    
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        doc="Many-to-many relationship with roles"
    )
    
    @hybrid_property
    def password(self) -> None:
        """
        Password property that prevents direct access to password hash.
        
        Raises:
            AttributeError: Always, as passwords should never be readable
        """
        raise AttributeError("Password is not readable. Use check_password() method.")
    
    @password.setter
    def password(self, plain_password: str) -> None:
        """
        Set password by hashing the plain text password.
        
        Args:
            plain_password: Plain text password to hash and store
            
        Raises:
            ValueError: If password doesn't meet complexity requirements
        """
        if not self._validate_password_complexity(plain_password):
            raise ValueError(
                "Password must be at least 8 characters long and contain "
                "at least one uppercase letter, one lowercase letter, "
                "one digit, and one special character"
            )
        
        # Generate salt and hash password using bcrypt
        salt = bcrypt.gensalt()
        self._password_hash = bcrypt.hashpw(
            plain_password.encode('utf-8'), 
            salt
        ).decode('utf-8')
    
    def check_password(self, plain_password: str) -> bool:
        """
        Verify a plain text password against the stored hash.
        
        Args:
            plain_password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
            
        Example:
            >>> user = User(username='john', email='john@example.com')
            >>> user.password = 'SecurePass123!'
            >>> user.check_password('SecurePass123!')  # Returns True
            >>> user.check_password('wrongpassword')   # Returns False
        """
        if not self._password_hash:
            return False
        
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            self._password_hash.encode('utf-8')
        )
    
    @validates('username')
    def validate_username(self, key: str, username: str) -> str:
        """
        Validate username format and length.
        
        Args:
            key: Field name being validated
            username: Username value to validate
            
        Returns:
            Validated username
            
        Raises:
            ValueError: If username format is invalid
        """
        if not username or len(username.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if len(username) > 50:
            raise ValueError("Username cannot exceed 50 characters")
        
        # Only allow alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )
        
        return username.strip().lower()
    
    @validates('email')
    def validate_email(self, key: str, email: str) -> str:
        """
        Validate email format using regex pattern.
        
        Args:
            key: Field name being validated
            email: Email value to validate
            
        Returns:
            Validated email in lowercase
            
        Raises:
            ValueError: If email format is invalid
        """
        if not email:
            raise ValueError("Email is required")
        
        # Basic email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email.strip().lower()
    
    @validates('first_name', 'last_name')
    def validate_name_fields(self, key: str, value: str) -> Optional[str]:
        """
        Validate name fields (first_name, last_name).
        
        Args:
            key: Field name being validated
            value: Name value to validate
            
        Returns:
            Validated name or None if empty
            
        Raises:
            ValueError: If name contains invalid characters
        """
        if not value:
            return None
        
        value = value.strip()
        if len(value) > 100:
            raise ValueError(f"{key.replace('_', ' ').title()} cannot exceed 100 characters")
        
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise ValueError(
                f"{key.replace('_', ' ').title()} can only contain letters, "
                "spaces, hyphens, and apostrophes"
            )
        
        return value.title()
    
    def _validate_password_complexity(self, password: str) -> bool:
        """
        Validate password complexity requirements.
        
        Args:
            password: Plain text password to validate
            
        Returns:
            True if password meets complexity requirements
        """
        if len(password) < 8:
            return False
        
        # Check for required character types
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return all([has_upper, has_lower, has_digit, has_special])
    
    def is_account_locked(self) -> bool:
        """
        Check if the user account is currently locked.
        
        Returns:
            True if account is locked, False otherwise
        """
        if not self.locked_until:
            return False
        
        return datetime.utcnow() < self.locked_until
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        Lock the user account for a specified duration.
        
        Args:
            duration_minutes: Lock duration in minutes (default: 30)
        """
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.save()
    
    def unlock_account(self) -> None:
        """Unlock the user account and reset failed login attempts."""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def increment_failed_login(self) -> None:
        """
        Increment failed login attempts and lock account if threshold reached.
        
        Locks account for 30 minutes after 5 failed attempts.
        """
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account(30)
        
        self.save()
    
    def record_successful_login(self) -> None:
        """Record successful login and reset security counters."""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save()
    
    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role_name: Name of the role to check
            
        Returns:
            True if user has the role, False otherwise
        """
        return any(role.name == role_name for role in self.roles)
    
    def add_role(self, role: 'Role') -> None:
        """
        Add a role to the user.
        
        Args:
            role: Role instance to add
        """
        if role not in self.roles:
            self.roles.append(role)
            self.save()
    
    def remove_role(self, role: 'Role') -> None:
        """
        Remove a role from the user.
        
        Args:
            role: Role instance to remove
        """
        if role in self.roles:
            self.roles.remove(role)
            self.save()
    
    @property
    def full_name(self) -> str:
        """
        Get user's full name.
        
        Returns:
            Full name or username if names not provided
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert user instance to dictionary, excluding sensitive fields.
        
        Args:
            exclude_fields: Additional fields to exclude
            
        Returns:
            Dictionary representation excluding password hash
        """
        default_exclude = ['_password_hash', 'password_hash']
        exclude_fields = exclude_fields or []
        exclude_fields.extend(default_exclude)
        
        user_dict = super().to_dict(exclude_fields=exclude_fields)
        
        # Add computed fields
        user_dict['full_name'] = self.full_name
        user_dict['is_locked'] = self.is_account_locked()
        user_dict['role_names'] = [role.name for role in self.roles]
        
        return user_dict
    
    def validate(self) -> bool:
        """
        Comprehensive validation of user instance.
        
        Returns:
            True if all validations pass
            
        Raises:
            ValueError: If any validation fails
        """
        # Validate required fields
        if not self.username:
            raise ValueError("Username is required")
        
        if not self.email:
            raise ValueError("Email is required")
        
        if not self._password_hash:
            raise ValueError("Password is required")
        
        return True
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"