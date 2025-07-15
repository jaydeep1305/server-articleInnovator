"""
Invitation model module for user invitation management.

This module defines the InvitationCode model that handles user invitations,
account provisioning limits, and invitation tracking. The model supports
various limitation types and tracks usage patterns for analytics.

Author: AI Assistant
Date: 2024
"""

import secrets
import string
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel


class InvitationCode(BaseModel):
    """
    Invitation code model for user registration and account provisioning.
    
    This model manages invitation codes that can be used to register new users
    with specific limitations and entitlements. It tracks usage, limitations,
    and provides analytics for invitation management.
    
    Attributes:
        invitation_code (str): Unique invitation code string
        article_limitation (int): Maximum number of articles user can create
        domain_limitation (int): Maximum number of domains user can manage
        workspace_limitation (int): Maximum number of workspaces user can create
        used (bool): Whether the invitation code has been used
        used_date (date): Date when the invitation code was used
        user_id (UUID): Foreign key to User who used this invitation
        created_by (UUID): Foreign key to User who created this invitation
        expires_at (date): Expiration date for the invitation
        max_uses (int): Maximum number of times this code can be used
        current_uses (int): Current number of times this code has been used
        
    Relationships:
        user: Many-to-one relationship with User (who used the invitation)
        creator: Many-to-one relationship with User (who created the invitation)
    """
    
    __tablename__ = 'invitation_codes'
    
    # Core invitation data
    invitation_code = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique invitation code string"
    )
    
    # Limitation settings
    article_limitation = Column(
        Integer,
        default=1000,
        nullable=False,
        comment="Maximum number of articles user can create"
    )
    
    domain_limitation = Column(
        Integer,
        default=10,
        nullable=False,
        comment="Maximum number of domains user can manage"
    )
    
    workspace_limitation = Column(
        Integer,
        default=10,
        nullable=False,
        comment="Maximum number of workspaces user can create"
    )
    
    # Usage tracking
    used = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the invitation code has been used"
    )
    
    used_date = Column(
        Date,
        nullable=True,
        comment="Date when the invitation code was used"
    )
    
    # Multi-use support
    max_uses = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Maximum number of times this code can be used"
    )
    
    current_uses = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Current number of times this code has been used"
    )
    
    # Expiration
    expires_at = Column(
        Date,
        nullable=True,
        comment="Expiration date for the invitation"
    )
    
    # Relationships
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="Reference to the user who used this invitation"
    )
    
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="Reference to the user who created this invitation"
    )
    
    # Note: Actual relationship definitions would be in a separate file
    # to avoid circular imports
    
    def __init__(self, invitation_code: str = None, **kwargs) -> None:
        """
        Initialize a new invitation code instance.
        
        Args:
            invitation_code: Custom invitation code (auto-generated if not provided)
            **kwargs: Additional invitation attributes
            
        Raises:
            ValueError: If invitation data is invalid
        """
        super().__init__(**kwargs)
        
        # Generate invitation code if not provided
        if invitation_code:
            self.invitation_code = invitation_code.upper().strip()
        else:
            self.invitation_code = self._generate_invitation_code()
        
        # Set default expiration if not provided (30 days from now)
        if not self.expires_at:
            self.expires_at = date.today() + timedelta(days=30)
        
        # Validate during initialization
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Invitation validation failed: {', '.join(errors)}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate invitation code data according to business rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        is_valid, errors = super().validate()
        
        # Invitation code validation
        if not self._validate_invitation_code(self.invitation_code):
            errors.append("Invitation code must be 6-20 characters long and contain only letters and numbers")
        
        # Limitation validations
        if self.article_limitation < 0:
            errors.append("Article limitation cannot be negative")
        
        if self.domain_limitation < 0:
            errors.append("Domain limitation cannot be negative")
        
        if self.workspace_limitation < 0:
            errors.append("Workspace limitation cannot be negative")
        
        # Usage validation
        if self.max_uses < 1:
            errors.append("Max uses must be at least 1")
        
        if self.current_uses < 0:
            errors.append("Current uses cannot be negative")
        
        if self.current_uses > self.max_uses:
            errors.append("Current uses cannot exceed max uses")
        
        # Date validation
        if self.expires_at and self.expires_at < date.today():
            errors.append("Expiration date cannot be in the past")
        
        if self.used_date and self.used_date > date.today():
            errors.append("Used date cannot be in the future")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_invitation_code(code: str) -> bool:
        """
        Validate invitation code format.
        
        Args:
            code: Invitation code to validate
            
        Returns:
            bool: True if invitation code format is valid
        """
        if not code or len(code) < 6 or len(code) > 20:
            return False
        
        # Only allow letters and numbers
        return code.isalnum()
    
    @staticmethod
    def _generate_invitation_code(length: int = 12) -> str:
        """
        Generate a random invitation code.
        
        Args:
            length: Length of the invitation code
            
        Returns:
            str: Generated invitation code
        """
        # Use uppercase letters and numbers, excluding confusing characters
        alphabet = string.ascii_uppercase + string.digits
        alphabet = alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
        
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def is_valid_for_use(self) -> tuple[bool, str]:
        """
        Check if invitation code is valid for use.
        
        Returns:
            tuple[bool, str]: (is_valid, reason_if_invalid)
            
        Example:
            >>> is_valid, reason = invitation.is_valid_for_use()
            >>> if not is_valid:
            ...     return {"error": reason}
        """
        # Check if invitation is active
        if not self.status:
            return False, "Invitation code has been deactivated"
        
        # Check expiration
        if self.expires_at and self.expires_at < date.today():
            return False, "Invitation code has expired"
        
        # Check usage limits
        if self.current_uses >= self.max_uses:
            return False, "Invitation code has reached its usage limit"
        
        return True, ""
    
    def use_invitation(self, user_id: Optional[str] = None) -> bool:
        """
        Mark invitation as used and increment usage counter.
        
        Args:
            user_id: ID of user who used the invitation
            
        Returns:
            bool: True if invitation was successfully used
            
        Raises:
            ValueError: If invitation cannot be used
        """
        is_valid, reason = self.is_valid_for_use()
        if not is_valid:
            raise ValueError(f"Cannot use invitation: {reason}")
        
        # Update usage tracking
        self.current_uses += 1
        self.used_date = date.today()
        
        # Mark as fully used if at limit
        if self.current_uses >= self.max_uses:
            self.used = True
        
        # Set user if provided (for single-use invitations)
        if user_id and self.max_uses == 1:
            self.user_id = user_id
        
        return True
    
    def extend_expiration(self, days: int) -> None:
        """
        Extend the expiration date of the invitation.
        
        Args:
            days: Number of days to extend the expiration
            
        Raises:
            ValueError: If days is negative or invitation is already expired
        """
        if days <= 0:
            raise ValueError("Extension days must be positive")
        
        if self.expires_at and self.expires_at < date.today():
            raise ValueError("Cannot extend expired invitation")
        
        if self.expires_at:
            self.expires_at = self.expires_at + timedelta(days=days)
        else:
            self.expires_at = date.today() + timedelta(days=days)
    
    def reset_usage(self) -> None:
        """
        Reset the usage counter and mark as unused.
        
        This method is useful for reactivating invitations or
        resetting multi-use invitations.
        """
        self.current_uses = 0
        self.used = False
        self.used_date = None
        self.user_id = None
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return self.expires_at and self.expires_at < date.today()
    
    @property
    def is_fully_used(self) -> bool:
        """Check if invitation has reached its usage limit."""
        return self.current_uses >= self.max_uses
    
    @property
    def remaining_uses(self) -> int:
        """Get number of remaining uses."""
        return max(0, self.max_uses - self.current_uses)
    
    @property
    def days_until_expiration(self) -> Optional[int]:
        """Get number of days until expiration."""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - date.today()
        return max(0, delta.days)
    
    @classmethod
    def find_by_code(cls, session: Session, code: str) -> Optional['InvitationCode']:
        """
        Find invitation by code.
        
        Args:
            session: SQLAlchemy session
            code: Invitation code to search for
            
        Returns:
            InvitationCode instance or None if not found
        """
        return cls.get_active_query(session).filter(
            cls.invitation_code == code.upper().strip()
        ).first()
    
    @classmethod
    def get_unused_invitations(cls, session: Session) -> List['InvitationCode']:
        """
        Get all unused invitations.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List[InvitationCode]: List of unused invitations
        """
        return cls.get_active_query(session).filter(
            cls.used == False,
            cls.current_uses < cls.max_uses
        ).all()
    
    @classmethod
    def get_expired_invitations(cls, session: Session) -> List['InvitationCode']:
        """
        Get all expired invitations.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List[InvitationCode]: List of expired invitations
        """
        return cls.get_active_query(session).filter(
            cls.expires_at < date.today()
        ).all()
    
    @classmethod
    def cleanup_expired_invitations(cls, session: Session) -> int:
        """
        Soft delete expired invitations.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            int: Number of invitations cleaned up
        """
        expired_invitations = cls.get_expired_invitations(session)
        
        for invitation in expired_invitations:
            invitation.soft_delete()
        
        session.commit()
        return len(expired_invitations)
    
    @classmethod
    def generate_bulk_invitations(cls, session: Session, count: int, 
                                 creator_id: Optional[str] = None,
                                 **default_settings) -> List['InvitationCode']:
        """
        Generate multiple invitation codes with the same settings.
        
        Args:
            session: SQLAlchemy session
            count: Number of invitations to generate
            creator_id: ID of user creating the invitations
            **default_settings: Default settings for all invitations
            
        Returns:
            List[InvitationCode]: List of generated invitation codes
            
        Raises:
            ValueError: If count is invalid or settings are invalid
        """
        if count <= 0 or count > 1000:
            raise ValueError("Count must be between 1 and 1000")
        
        invitations = []
        
        for _ in range(count):
            # Generate unique code
            code = cls._generate_invitation_code()
            while cls.find_by_code(session, code):
                code = cls._generate_invitation_code()
            
            # Create invitation with settings
            invitation = cls(
                invitation_code=code,
                created_by=creator_id,
                **default_settings
            )
            
            invitations.append(invitation)
            session.add(invitation)
        
        session.commit()
        return invitations
    
    def to_dict(self, include_relationships: bool = False, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert invitation to dictionary with computed fields.
        
        Args:
            include_relationships: Whether to include related objects
            include_sensitive: Whether to include sensitive data
            
        Returns:
            Dict[str, Any]: Invitation data dictionary
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Add computed fields
        result['is_expired'] = self.is_expired
        result['is_fully_used'] = self.is_fully_used
        result['remaining_uses'] = self.remaining_uses
        result['days_until_expiration'] = self.days_until_expiration
        
        # Add validity check
        is_valid, reason = self.is_valid_for_use()
        result['is_valid_for_use'] = is_valid
        if not is_valid:
            result['invalid_reason'] = reason
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the invitation code."""
        return f"<InvitationCode(code='{self.invitation_code}', used={self.used})>"