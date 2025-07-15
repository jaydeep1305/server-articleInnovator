"""
Workspace model for workspace management and collaboration.

This module defines the Workspace model that handles workspace creation,
member management, permissions, and workspace-related business logic.
Implements cognitive patterns for collaborative workspaces.

Author: AI Assistant
Date: 2024
"""

import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel
from app import db


class WorkspaceRole(Enum):
    """Enumeration for workspace member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"


class WorkspaceStatus(Enum):
    """Enumeration for workspace status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# Association table for workspace members with roles
workspace_members = Table(
    'workspace_members',
    db.Model.metadata,
    Column('workspace_id', UUID(as_uuid=True), ForeignKey('workspaces.id'), primary_key=True),
    Column('user_id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('role', String(20), default=WorkspaceRole.MEMBER.value, nullable=False),
    Column('joined_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('invited_by', UUID(as_uuid=True), nullable=True),
    Column('is_active', Boolean, default=True, nullable=False)
)


class Workspace(BaseModel):
    """
    Workspace model for managing collaborative workspaces.
    
    This model handles workspace creation, member management, permissions,
    and workspace settings. It implements cognitive collaboration patterns
    with proper access control and resource management.
    
    Attributes:
        name (str): Workspace name (3-50 characters)
        slug (str): URL-friendly workspace identifier
        description (str): Workspace description
        owner_id (UUID): ID of the workspace owner
        status (str): Workspace status (active, archived, suspended, deleted)
        visibility (str): Workspace visibility (public, private, internal)
        max_members (int): Maximum number of members allowed
        storage_quota_gb (int): Storage quota in gigabytes
        custom_domain (str): Custom domain for workspace
        settings (JSON): Workspace-specific settings
        
    Relationships:
        owner: Many-to-one relationship with User (owner)
        members: Many-to-many relationship with User (members)
        
    Business Rules:
        - Workspace names must be unique within the system
        - Slugs are auto-generated from names and must be unique
        - Owners have full control over workspace settings
        - Member limits are enforced based on workspace plan
        - Storage quotas are tracked and enforced
    """
    
    __tablename__ = 'workspaces'
    
    # Core workspace identification
    name = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Workspace name (3-50 characters)"
    )
    
    slug = Column(
        String(60),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-friendly workspace identifier"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Workspace description and purpose"
    )
    
    # Ownership and management
    owner_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID of the workspace owner"
    )
    
    status = Column(
        String(20),
        default=WorkspaceStatus.ACTIVE.value,
        nullable=False,
        index=True,
        comment="Workspace status (active, archived, suspended, deleted)"
    )
    
    visibility = Column(
        String(20),
        default="private",
        nullable=False,
        comment="Workspace visibility (public, private, internal)"
    )
    
    # Workspace limits and quotas
    max_members = Column(
        Integer,
        default=10,
        nullable=False,
        comment="Maximum number of members allowed"
    )
    
    storage_quota_gb = Column(
        Integer,
        default=5,
        nullable=False,
        comment="Storage quota in gigabytes"
    )
    
    storage_used_mb = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Storage currently used in megabytes"
    )
    
    # Customization options
    custom_domain = Column(
        String(100),
        nullable=True,
        unique=True,
        comment="Custom domain for workspace"
    )
    
    logo_url = Column(
        String(500),
        nullable=True,
        comment="URL to workspace logo"
    )
    
    theme_color = Column(
        String(7),
        default="#6366F1",
        nullable=False,
        comment="Primary theme color for workspace"
    )
    
    # Workspace settings (stored as JSON)
    allow_guest_access = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether guests can access workspace"
    )
    
    require_approval = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether new members require approval"
    )
    
    enable_notifications = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether notifications are enabled"
    )
    
    # Timestamps for workspace lifecycle
    archived_at = Column(
        DateTime,
        nullable=True,
        comment="When workspace was archived"
    )
    
    last_activity_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Last activity in workspace"
    )
    
    def __init__(self, name: str, owner_id: uuid.UUID, **kwargs) -> None:
        """
        Initialize a new workspace with cognitive validation.
        
        Args:
            name: Workspace name
            owner_id: UUID of the workspace owner
            **kwargs: Additional workspace attributes
            
        Raises:
            ValueError: If workspace data is invalid
        """
        # Generate slug from name
        slug = kwargs.get('slug', self._generate_slug(name))
        
        # Set required fields
        kwargs.update({
            'name': name.strip(),
            'slug': slug,
            'owner_id': owner_id
        })
        
        super().__init__(**kwargs)
        
        # Validate the workspace
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Workspace validation failed: {', '.join(errors)}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate workspace data according to business rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        is_valid, errors = super().validate()
        
        # Name validation
        if not self._validate_workspace_name(self.name):
            errors.append("Workspace name must be 3-50 characters and contain valid characters")
        
        # Slug validation
        if not self._validate_slug(self.slug):
            errors.append("Workspace slug must be URL-friendly and unique")
        
        # Description validation
        if self.description and len(self.description) > 500:
            errors.append("Description cannot exceed 500 characters")
        
        # Status validation
        valid_statuses = {status.value for status in WorkspaceStatus}
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Visibility validation
        valid_visibilities = {'public', 'private', 'internal'}
        if self.visibility not in valid_visibilities:
            errors.append(f"Visibility must be one of: {', '.join(valid_visibilities)}")
        
        # Member limit validation
        if self.max_members < 1 or self.max_members > 1000:
            errors.append("Max members must be between 1 and 1000")
        
        # Storage quota validation
        if self.storage_quota_gb < 1 or self.storage_quota_gb > 100:
            errors.append("Storage quota must be between 1 and 100 GB")
        
        # Custom domain validation
        if self.custom_domain and not self._validate_domain(self.custom_domain):
            errors.append("Invalid custom domain format")
        
        # Theme color validation
        if self.theme_color and not self._validate_color_code(self.theme_color):
            errors.append("Invalid theme color format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _generate_slug(name: str) -> str:
        """
        Generate URL-friendly slug from workspace name.
        
        Args:
            name: Workspace name
            
        Returns:
            str: URL-friendly slug
        """
        if not name:
            return ""
        
        # Convert to lowercase and replace spaces with hyphens
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
        slug = re.sub(r'\s+', '-', slug)      # Replace spaces with hyphens
        slug = re.sub(r'-+', '-', slug)       # Remove multiple hyphens
        slug = slug.strip('-')                # Remove leading/trailing hyphens
        
        # Ensure minimum length
        if len(slug) < 3:
            slug = f"workspace-{uuid.uuid4().hex[:8]}"
        
        return slug[:50]  # Limit length
    
    @staticmethod
    def _validate_workspace_name(name: str) -> bool:
        """
        Validate workspace name format.
        
        Args:
            name: Workspace name to validate
            
        Returns:
            bool: True if name is valid
        """
        if not name or len(name.strip()) < 3 or len(name.strip()) > 50:
            return False
        
        # Must contain at least one alphanumeric character
        if not re.search(r'[a-zA-Z0-9]', name):
            return False
        
        # No leading/trailing whitespace
        if name != name.strip():
            return False
        
        return True
    
    @staticmethod
    def _validate_slug(slug: str) -> bool:
        """
        Validate workspace slug format.
        
        Args:
            slug: Slug to validate
            
        Returns:
            bool: True if slug is valid
        """
        if not slug or len(slug) < 3 or len(slug) > 60:
            return False
        
        # Slug pattern: lowercase letters, numbers, hyphens
        slug_pattern = r'^[a-z0-9-]+$'
        if not re.match(slug_pattern, slug):
            return False
        
        # Cannot start or end with hyphen
        if slug.startswith('-') or slug.endswith('-'):
            return False
        
        # Cannot have consecutive hyphens
        if '--' in slug:
            return False
        
        return True
    
    @staticmethod
    def _validate_domain(domain: str) -> bool:
        """
        Validate custom domain format.
        
        Args:
            domain: Domain to validate
            
        Returns:
            bool: True if domain is valid
        """
        if not domain:
            return False
        
        # Basic domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return re.match(domain_pattern, domain) is not None
    
    @staticmethod
    def _validate_color_code(color: str) -> bool:
        """
        Validate hex color code format.
        
        Args:
            color: Color code to validate
            
        Returns:
            bool: True if color code is valid
        """
        if not color:
            return False
        
        color_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return re.match(color_pattern, color) is not None
    
    def add_member(self, session: Session, user_id: uuid.UUID, 
                  role: WorkspaceRole = WorkspaceRole.MEMBER,
                  invited_by: Optional[uuid.UUID] = None) -> bool:
        """
        Add a member to the workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user to add
            role: Role to assign to the user
            invited_by: ID of user who invited this member
            
        Returns:
            bool: True if member was added successfully
            
        Raises:
            ValueError: If member cannot be added due to business rules
        """
        # Check if user is already a member
        if self.is_member(session, user_id):
            raise ValueError("User is already a member of this workspace")
        
        # Check member limit
        current_member_count = self.get_member_count(session)
        if current_member_count >= self.max_members:
            raise ValueError(f"Workspace has reached maximum member limit of {self.max_members}")
        
        # Add member using raw SQL for association table
        member_data = {
            'workspace_id': self.id,
            'user_id': user_id,
            'role': role.value,
            'joined_at': datetime.utcnow(),
            'invited_by': invited_by,
            'is_active': True
        }
        
        session.execute(workspace_members.insert().values(**member_data))
        session.flush()
        
        # Update last activity
        self.last_activity_at = datetime.utcnow()
        
        return True
    
    def remove_member(self, session: Session, user_id: uuid.UUID) -> bool:
        """
        Remove a member from the workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user to remove
            
        Returns:
            bool: True if member was removed
            
        Raises:
            ValueError: If member cannot be removed
        """
        # Cannot remove the owner
        if user_id == self.owner_id:
            raise ValueError("Cannot remove workspace owner")
        
        # Remove member
        result = session.execute(
            workspace_members.delete().where(
                workspace_members.c.workspace_id == self.id,
                workspace_members.c.user_id == user_id
            )
        )
        
        removed = result.rowcount > 0
        if removed:
            self.last_activity_at = datetime.utcnow()
        
        return removed
    
    def update_member_role(self, session: Session, user_id: uuid.UUID, 
                          new_role: WorkspaceRole) -> bool:
        """
        Update a member's role in the workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user whose role to update
            new_role: New role to assign
            
        Returns:
            bool: True if role was updated
            
        Raises:
            ValueError: If role cannot be updated
        """
        # Cannot change owner role
        if user_id == self.owner_id:
            raise ValueError("Cannot change workspace owner role")
        
        # Update role
        result = session.execute(
            workspace_members.update().where(
                workspace_members.c.workspace_id == self.id,
                workspace_members.c.user_id == user_id
            ).values(role=new_role.value)
        )
        
        updated = result.rowcount > 0
        if updated:
            self.last_activity_at = datetime.utcnow()
        
        return updated
    
    def is_member(self, session: Session, user_id: uuid.UUID) -> bool:
        """
        Check if a user is a member of the workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user to check
            
        Returns:
            bool: True if user is a member
        """
        result = session.execute(
            workspace_members.select().where(
                workspace_members.c.workspace_id == self.id,
                workspace_members.c.user_id == user_id,
                workspace_members.c.is_active == True
            )
        ).first()
        
        return result is not None
    
    def get_member_role(self, session: Session, user_id: uuid.UUID) -> Optional[WorkspaceRole]:
        """
        Get a member's role in the workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user to check
            
        Returns:
            WorkspaceRole or None if not a member
        """
        # Check if owner
        if user_id == self.owner_id:
            return WorkspaceRole.OWNER
        
        result = session.execute(
            workspace_members.select().where(
                workspace_members.c.workspace_id == self.id,
                workspace_members.c.user_id == user_id,
                workspace_members.c.is_active == True
            )
        ).first()
        
        if result:
            return WorkspaceRole(result.role)
        
        return None
    
    def get_member_count(self, session: Session) -> int:
        """
        Get the number of active members in the workspace.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            int: Number of active members (including owner)
        """
        from sqlalchemy import func
        
        result = session.execute(
            session.query(func.count(workspace_members.c.user_id)).filter(
                workspace_members.c.workspace_id == self.id,
                workspace_members.c.is_active == True
            )
        ).scalar()
        
        return (result or 0) + 1  # Add 1 for owner
    
    def get_members(self, session: Session) -> List[Dict[str, Any]]:
        """
        Get all active members of the workspace.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List of member dictionaries with user info and roles
        """
        members = []
        
        # Add owner
        members.append({
            'user_id': str(self.owner_id),
            'role': WorkspaceRole.OWNER.value,
            'joined_at': self.created_at.isoformat(),
            'invited_by': None,
            'is_owner': True
        })
        
        # Add other members
        results = session.execute(
            workspace_members.select().where(
                workspace_members.c.workspace_id == self.id,
                workspace_members.c.is_active == True
            )
        ).fetchall()
        
        for result in results:
            members.append({
                'user_id': str(result.user_id),
                'role': result.role,
                'joined_at': result.joined_at.isoformat(),
                'invited_by': str(result.invited_by) if result.invited_by else None,
                'is_owner': False
            })
        
        return members
    
    def archive(self) -> None:
        """Archive the workspace."""
        self.status = WorkspaceStatus.ARCHIVED.value
        self.archived_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore an archived workspace."""
        self.status = WorkspaceStatus.ACTIVE.value
        self.archived_at = None
        self.updated_at = datetime.utcnow()
    
    def update_storage_usage(self, session: Session, size_mb: int) -> None:
        """
        Update workspace storage usage.
        
        Args:
            session: SQLAlchemy session
            size_mb: Storage size in megabytes to add (can be negative)
        """
        self.storage_used_mb = max(0, self.storage_used_mb + size_mb)
        self.last_activity_at = datetime.utcnow()
        session.flush()
    
    def is_storage_quota_exceeded(self) -> bool:
        """
        Check if workspace storage quota is exceeded.
        
        Returns:
            bool: True if quota is exceeded
        """
        quota_mb = self.storage_quota_gb * 1024
        return self.storage_used_mb > quota_mb
    
    def get_storage_usage_percentage(self) -> float:
        """
        Get storage usage as percentage of quota.
        
        Returns:
            float: Storage usage percentage (0-100)
        """
        quota_mb = self.storage_quota_gb * 1024
        if quota_mb == 0:
            return 100.0
        
        return min(100.0, (self.storage_used_mb / quota_mb) * 100)
    
    @classmethod
    def find_by_slug(cls, session: Session, slug: str) -> Optional['Workspace']:
        """
        Find workspace by slug.
        
        Args:
            session: SQLAlchemy session
            slug: Workspace slug
            
        Returns:
            Workspace instance or None
        """
        return cls.get_active_query(session).filter(cls.slug == slug).first()
    
    @classmethod
    def find_by_owner(cls, session: Session, owner_id: uuid.UUID) -> List['Workspace']:
        """
        Find all workspaces owned by a user.
        
        Args:
            session: SQLAlchemy session
            owner_id: Owner user ID
            
        Returns:
            List of workspace instances
        """
        return cls.get_active_query(session).filter(cls.owner_id == owner_id).all()
    
    @property
    def is_active(self) -> bool:
        """Check if workspace is active."""
        return self.status == WorkspaceStatus.ACTIVE.value
    
    @property
    def is_archived(self) -> bool:
        """Check if workspace is archived."""
        return self.status == WorkspaceStatus.ARCHIVED.value
    
    @property
    def storage_quota_mb(self) -> int:
        """Get storage quota in megabytes."""
        return self.storage_quota_gb * 1024
    
    def to_dict(self, include_members: bool = False, 
                include_stats: bool = False) -> Dict[str, Any]:
        """
        Convert workspace to dictionary.
        
        Args:
            include_members: Whether to include member list
            include_stats: Whether to include usage statistics
            
        Returns:
            Dict[str, Any]: Workspace data
        """
        result = super().to_dict()
        
        # Add computed fields
        result.update({
            'is_active': self.is_active,
            'is_archived': self.is_archived,
            'storage_quota_mb': self.storage_quota_mb,
            'storage_usage_percentage': self.get_storage_usage_percentage()
        })
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the workspace."""
        return f"<Workspace(name='{self.name}', slug='{self.slug}', owner_id='{self.owner_id}')>"