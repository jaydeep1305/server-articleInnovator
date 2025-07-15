"""
Workspace model module for workspace and user-workspace management.

This module defines the Workspace and WorkspaceUser models that handle
workspace creation, user membership, and workspace-related business logic.
The models support hierarchical workspaces and role-based access control.

Author: AI Assistant
Date: 2024
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Set
from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint, Index, Integer
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel


class WorkspaceRole(Enum):
    """Enumeration for workspace-specific roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Workspace(BaseModel):
    """
    Workspace model for organizing users and resources.
    
    This model manages workspaces which serve as containers for organizing
    users, projects, and resources. Workspaces support hierarchical organization
    and provide isolation between different groups or projects.
    
    Attributes:
        name (str): Workspace name
        description (str): Workspace description
        owner_id (UUID): Foreign key to User who owns this workspace
        parent_workspace_id (UUID): Foreign key to parent workspace for hierarchy
        workspace_type (str): Type of workspace (personal, team, organization)
        is_public (bool): Whether workspace is publicly visible
        max_members (int): Maximum number of members allowed
        settings (str): JSON string of workspace settings
        
    Relationships:
        owner: Many-to-one relationship with User (workspace owner)
        parent_workspace: Self-referential relationship for hierarchy
        child_workspaces: One-to-many relationship with child workspaces
        workspace_users: One-to-many relationship with WorkspaceUser
        members: Many-to-many relationship with User through WorkspaceUser
    """
    
    __tablename__ = 'workspaces'
    
    # Core workspace data
    name = Column(
        String(200),
        nullable=False,
        comment="Workspace name"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Workspace description"
    )
    
    # Ownership and hierarchy
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the user who owns this workspace"
    )
    
    parent_workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey('workspaces.id', ondelete='CASCADE'),
        nullable=True,
        comment="Reference to parent workspace for hierarchy"
    )
    
    # Workspace configuration
    workspace_type = Column(
        String(50),
        default='team',
        nullable=False,
        comment="Type of workspace (personal, team, organization)"
    )
    
    is_public = Column(
        String(10),
        default="false",
        nullable=False,
        comment="Whether workspace is publicly visible"
    )
    
    max_members = Column(
        Integer,
        default=50,
        nullable=False,
        comment="Maximum number of members allowed"
    )
    
    settings = Column(
        Text,
        nullable=True,
        comment="JSON string of workspace settings and preferences"
    )
    
    # Relationships
    parent_workspace = relationship(
        "Workspace",
        remote_side="Workspace.id",
        back_populates="child_workspaces",
        lazy="select"
    )
    
    child_workspaces = relationship(
        "Workspace",
        back_populates="parent_workspace",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    workspace_users = relationship(
        "WorkspaceUser",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Add indexes for efficient queries
    __table_args__ = (
        Index('idx_workspace_owner', 'owner_id'),
        Index('idx_workspace_parent', 'parent_workspace_id'),
        Index('idx_workspace_type', 'workspace_type'),
        Index('idx_workspace_name', 'name'),
    )
    
    def __init__(self, name: str, owner_id: str, **kwargs) -> None:
        """
        Initialize a new workspace instance.
        
        Args:
            name: Workspace name
            owner_id: ID of the user who owns this workspace
            **kwargs: Additional workspace attributes
            
        Raises:
            ValueError: If workspace data is invalid
        """
        super().__init__(**kwargs)
        
        self.name = name.strip()
        self.owner_id = owner_id
        
        # Validate during initialization
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
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Workspace name is required")
        
        if len(self.name) > 200:
            errors.append("Workspace name cannot exceed 200 characters")
        
        # Owner validation
        if not self.owner_id:
            errors.append("Owner ID is required")
        
        # Type validation
        valid_types = {'personal', 'team', 'organization', 'project'}
        if self.workspace_type not in valid_types:
            errors.append(f"Workspace type must be one of: {', '.join(valid_types)}")
        
        # Members limit validation
        if self.max_members < 1 or self.max_members > 10000:
            errors.append("Max members must be between 1 and 10000")
        
        # Description validation
        if self.description and len(self.description) > 2000:
            errors.append("Description cannot exceed 2000 characters")
        
        # Prevent self-referencing parent
        if self.parent_workspace_id == self.id:
            errors.append("Workspace cannot be its own parent")
        
        return len(errors) == 0, errors
    
    def add_member(self, session: Session, user_id: str, 
                   role: WorkspaceRole = WorkspaceRole.MEMBER) -> 'WorkspaceUser':
        """
        Add a user to this workspace with the specified role.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user to add
            role: Role to assign to the user
            
        Returns:
            WorkspaceUser: Created workspace user association
            
        Raises:
            ValueError: If user is already a member or workspace is full
        """
        # Check if user is already a member
        existing = session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.user_id == user_id,
            WorkspaceUser.status == True
        ).first()
        
        if existing:
            raise ValueError("User is already a member of this workspace")
        
        # Check member limit
        current_members = self.get_member_count(session)
        if current_members >= self.max_members:
            raise ValueError(f"Workspace has reached its member limit of {self.max_members}")
        
        # Create workspace user association
        workspace_user = WorkspaceUser(
            workspace_id=self.id,
            user_id=user_id,
            role=role.value
        )
        
        session.add(workspace_user)
        return workspace_user
    
    def remove_member(self, session: Session, user_id: str) -> bool:
        """
        Remove a user from this workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user to remove
            
        Returns:
            bool: True if user was removed, False if they weren't a member
            
        Raises:
            ValueError: If trying to remove the workspace owner
        """
        # Prevent removing the owner
        if str(user_id) == str(self.owner_id):
            raise ValueError("Cannot remove workspace owner")
        
        workspace_user = session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.user_id == user_id,
            WorkspaceUser.status == True
        ).first()
        
        if workspace_user:
            workspace_user.soft_delete()
            return True
        
        return False
    
    def update_member_role(self, session: Session, user_id: str, 
                          new_role: WorkspaceRole) -> bool:
        """
        Update a member's role in this workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user whose role to update
            new_role: New role to assign
            
        Returns:
            bool: True if role was updated, False if user is not a member
            
        Raises:
            ValueError: If trying to change owner role without permission
        """
        workspace_user = session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.user_id == user_id,
            WorkspaceUser.status == True
        ).first()
        
        if not workspace_user:
            return False
        
        # Special handling for owner role changes
        if str(user_id) == str(self.owner_id) and new_role != WorkspaceRole.OWNER:
            raise ValueError("Cannot change owner role. Transfer ownership first.")
        
        workspace_user.role = new_role.value
        return True
    
    def transfer_ownership(self, session: Session, new_owner_id: str) -> None:
        """
        Transfer ownership of this workspace to another user.
        
        Args:
            session: SQLAlchemy session
            new_owner_id: ID of the new owner
            
        Raises:
            ValueError: If new owner is not a member or operation is invalid
        """
        # Check if new owner is a member
        new_owner_membership = session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.user_id == new_owner_id,
            WorkspaceUser.status == True
        ).first()
        
        if not new_owner_membership:
            raise ValueError("New owner must be a member of the workspace")
        
        # Update owner
        old_owner_id = self.owner_id
        self.owner_id = new_owner_id
        
        # Update roles
        new_owner_membership.role = WorkspaceRole.OWNER.value
        
        # Update old owner to admin
        old_owner_membership = session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.user_id == old_owner_id,
            WorkspaceUser.status == True
        ).first()
        
        if old_owner_membership:
            old_owner_membership.role = WorkspaceRole.ADMIN.value
    
    def get_member_count(self, session: Session) -> int:
        """
        Get the number of active members in this workspace.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            int: Number of active members
        """
        return session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.status == True
        ).count()
    
    def get_members(self, session: Session, role: Optional[WorkspaceRole] = None) -> List['WorkspaceUser']:
        """
        Get all members of this workspace, optionally filtered by role.
        
        Args:
            session: SQLAlchemy session
            role: Optional role filter
            
        Returns:
            List[WorkspaceUser]: List of workspace user associations
        """
        query = session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.status == True
        )
        
        if role:
            query = query.filter(WorkspaceUser.role == role.value)
        
        return query.all()
    
    def get_member_roles(self, session: Session) -> Dict[str, str]:
        """
        Get a mapping of user IDs to their roles in this workspace.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            Dict[str, str]: Mapping of user_id to role
        """
        members = self.get_members(session)
        return {str(member.user_id): member.role for member in members}
    
    def user_has_role(self, session: Session, user_id: str, 
                     required_roles: List[WorkspaceRole]) -> bool:
        """
        Check if a user has one of the required roles in this workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user to check
            required_roles: List of roles that satisfy the requirement
            
        Returns:
            bool: True if user has one of the required roles
        """
        workspace_user = session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.user_id == user_id,
            WorkspaceUser.status == True
        ).first()
        
        if not workspace_user:
            return False
        
        return any(workspace_user.role == role.value for role in required_roles)
    
    def is_member(self, session: Session, user_id: str) -> bool:
        """
        Check if a user is a member of this workspace.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user to check
            
        Returns:
            bool: True if user is a member
        """
        return session.query(WorkspaceUser).filter(
            WorkspaceUser.workspace_id == self.id,
            WorkspaceUser.user_id == user_id,
            WorkspaceUser.status == True
        ).first() is not None
    
    @property
    def is_public_workspace(self) -> bool:
        """Check if workspace is public."""
        return self.is_public.lower() == "true"
    
    @classmethod
    def find_by_name(cls, session: Session, name: str, owner_id: Optional[str] = None) -> Optional['Workspace']:
        """
        Find workspace by name, optionally scoped to an owner.
        
        Args:
            session: SQLAlchemy session
            name: Workspace name to search for
            owner_id: Optional owner ID to scope the search
            
        Returns:
            Workspace instance or None if not found
        """
        query = cls.get_active_query(session).filter(cls.name == name.strip())
        
        if owner_id:
            query = query.filter(cls.owner_id == owner_id)
        
        return query.first()
    
    @classmethod
    def get_user_workspaces(cls, session: Session, user_id: str) -> List['Workspace']:
        """
        Get all workspaces where a user is a member.
        
        Args:
            session: SQLAlchemy session
            user_id: ID of user
            
        Returns:
            List[Workspace]: List of workspaces where user is a member
        """
        return session.query(cls).join(WorkspaceUser).filter(
            WorkspaceUser.user_id == user_id,
            WorkspaceUser.status == True,
            cls.status == True
        ).all()
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert workspace to dictionary with computed fields.
        
        Args:
            include_relationships: Whether to include related objects
            
        Returns:
            Dict[str, Any]: Workspace data dictionary
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Add computed fields
        result['is_public_workspace'] = self.is_public_workspace
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the workspace."""
        return f"<Workspace(name='{self.name}', owner_id='{self.owner_id}')>"


class WorkspaceUser(BaseModel):
    """
    Association model for Workspace-User many-to-many relationship.
    
    This model manages user membership in workspaces, including roles,
    permissions, and membership metadata.
    
    Attributes:
        workspace_id (UUID): Foreign key to Workspace
        user_id (UUID): Foreign key to User
        role (str): User's role in the workspace
        joined_date (datetime): When user joined the workspace
        invited_by (UUID): ID of user who invited this user
        
    Relationships:
        workspace: Many-to-one relationship with Workspace
        user: Many-to-one relationship with User
    """
    
    __tablename__ = 'workspace_users'
    
    # Foreign keys
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey('workspaces.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the workspace"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the user"
    )
    
    # Membership details
    role = Column(
        String(50),
        default=WorkspaceRole.MEMBER.value,
        nullable=False,
        comment="User's role in the workspace"
    )
    
    invited_by = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="ID of user who invited this user"
    )
    
    # Relationships
    workspace = relationship(
        "Workspace",
        back_populates="workspace_users",
        lazy="select"
    )
    
    # Ensure unique user-workspace combinations
    __table_args__ = (
        UniqueConstraint('workspace_id', 'user_id', name='unique_workspace_user'),
        Index('idx_workspace_user_workspace', 'workspace_id'),
        Index('idx_workspace_user_user', 'user_id'),
        Index('idx_workspace_user_role', 'role'),
    )
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate workspace user association.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        is_valid, errors = super().validate()
        
        if not self.workspace_id:
            errors.append("Workspace ID is required")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        # Role validation
        valid_roles = {role.value for role in WorkspaceRole}
        if self.role not in valid_roles:
            errors.append(f"Role must be one of: {', '.join(valid_roles)}")
        
        return len(errors) == 0, errors
    
    @property
    def workspace_role(self) -> WorkspaceRole:
        """Get role as enum value."""
        return WorkspaceRole(self.role)
    
    def has_permission(self, required_permissions: List[WorkspaceRole]) -> bool:
        """
        Check if user has one of the required permissions.
        
        Args:
            required_permissions: List of roles that satisfy the requirement
            
        Returns:
            bool: True if user has sufficient permissions
        """
        current_role = self.workspace_role
        return current_role in required_permissions
    
    def can_manage_members(self) -> bool:
        """Check if user can manage workspace members."""
        return self.workspace_role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    
    def can_modify_workspace(self) -> bool:
        """Check if user can modify workspace settings."""
        return self.workspace_role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    
    def is_owner(self) -> bool:
        """Check if user is workspace owner."""
        return self.workspace_role == WorkspaceRole.OWNER
    
    def is_admin_or_owner(self) -> bool:
        """Check if user is admin or owner."""
        return self.workspace_role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert workspace user to dictionary with computed fields.
        
        Args:
            include_relationships: Whether to include related objects
            
        Returns:
            Dict[str, Any]: Workspace user data dictionary
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Add computed fields
        result['can_manage_members'] = self.can_manage_members()
        result['can_modify_workspace'] = self.can_modify_workspace()
        result['is_owner'] = self.is_owner()
        result['is_admin_or_owner'] = self.is_admin_or_owner()
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the workspace user association."""
        return f"<WorkspaceUser(workspace_id='{self.workspace_id}', user_id='{self.user_id}', role='{self.role}')>"