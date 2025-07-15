"""
Role and Permission models for authorization and access control.

This module defines the Role, Permission, and RolePermission models that handle
user authorization, role-based access control (RBAC), and permission management.
The models support hierarchical roles and flexible permission assignments.

Author: AI Assistant
Date: 2024
"""

from typing import List, Dict, Any, Optional, Set
from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel


class Role(BaseModel):
    """
    Role model for role-based access control (RBAC).
    
    This model defines user roles within the system, allowing for granular
    access control and permission management. Roles can be assigned to users
    and can contain multiple permissions.
    
    Attributes:
        name (str): Unique role name (automatically converted to lowercase)
        display_name (str): Human-readable role name for UI display
        description (str): Detailed description of the role's purpose
        is_system_role (bool): Whether this is a built-in system role
        hierarchy_level (int): Role hierarchy level for inheritance
        
    Relationships:
        permissions: Many-to-many relationship with Permission through RolePermission
        users: Many-to-many relationship with User through UserRole
    """
    
    __tablename__ = 'roles'
    
    # Role identification
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique role name (lowercase)"
    )
    
    display_name = Column(
        String(200),
        nullable=False,
        comment="Human-readable role name for UI display"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the role's purpose and scope"
    )
    
    is_system_role = Column(
        String(10),
        default="false",
        nullable=False,
        comment="Whether this is a built-in system role (cannot be deleted)"
    )
    
    hierarchy_level = Column(
        String(10),
        default="0",
        nullable=False,
        comment="Role hierarchy level for permission inheritance"
    )
    
    # Relationships
    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __init__(self, name: str, display_name: str = None, **kwargs) -> None:
        """
        Initialize a new role instance.
        
        Args:
            name: Unique role name (will be converted to lowercase)
            display_name: Human-readable role name (defaults to formatted name)
            **kwargs: Additional role attributes
            
        Raises:
            ValueError: If role name format is invalid
        """
        super().__init__(**kwargs)
        
        # Convert name to lowercase and validate
        self.name = name.lower().strip().replace(' ', '_')
        self.display_name = display_name or self._format_display_name(self.name)
        
        # Validate during initialization
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Role validation failed: {', '.join(errors)}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate role data according to business rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        is_valid, errors = super().validate()
        
        # Name validation
        if not self._validate_role_name(self.name):
            errors.append("Role name must be 2-50 characters long and contain only letters, numbers, and underscores")
        
        # Display name validation
        if not self.display_name or len(self.display_name.strip()) == 0:
            errors.append("Display name is required")
        
        if len(self.display_name) > 200:
            errors.append("Display name cannot exceed 200 characters")
        
        # Description validation
        if self.description and len(self.description) > 1000:
            errors.append("Description cannot exceed 1000 characters")
        
        # Hierarchy level validation
        try:
            level = int(self.hierarchy_level or "0")
            if level < 0 or level > 100:
                errors.append("Hierarchy level must be between 0 and 100")
        except ValueError:
            errors.append("Hierarchy level must be a valid integer")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_role_name(name: str) -> bool:
        """
        Validate role name format.
        
        Args:
            name: Role name to validate
            
        Returns:
            bool: True if role name format is valid
        """
        import re
        
        if not name or len(name) < 2 or len(name) > 50:
            return False
        
        # Allow letters, numbers, and underscores only
        name_pattern = r'^[a-z0-9_]+$'
        return re.match(name_pattern, name) is not None
    
    @staticmethod
    def _format_display_name(name: str) -> str:
        """
        Format role name into a display-friendly format.
        
        Args:
            name: Role name to format
            
        Returns:
            str: Formatted display name
        """
        return ' '.join(word.capitalize() for word in name.split('_'))
    
    def add_permission(self, session: Session, permission: 'Permission') -> None:
        """
        Add a permission to this role.
        
        Args:
            session: SQLAlchemy session
            permission: Permission instance to add
            
        Raises:
            ValueError: If permission is already assigned to this role
        """
        # Check if permission is already assigned
        existing = session.query(RolePermission).filter(
            RolePermission.role_id == self.id,
            RolePermission.permission_id == permission.id
        ).first()
        
        if existing:
            raise ValueError(f"Permission '{permission.name}' is already assigned to role '{self.name}'")
        
        # Create new role-permission association
        role_permission = RolePermission(role_id=self.id, permission_id=permission.id)
        session.add(role_permission)
    
    def remove_permission(self, session: Session, permission: 'Permission') -> bool:
        """
        Remove a permission from this role.
        
        Args:
            session: SQLAlchemy session
            permission: Permission instance to remove
            
        Returns:
            bool: True if permission was removed, False if it wasn't assigned
        """
        role_permission = session.query(RolePermission).filter(
            RolePermission.role_id == self.id,
            RolePermission.permission_id == permission.id
        ).first()
        
        if role_permission:
            session.delete(role_permission)
            return True
        
        return False
    
    def has_permission(self, session: Session, permission_name: str) -> bool:
        """
        Check if this role has a specific permission.
        
        Args:
            session: SQLAlchemy session
            permission_name: Name of the permission to check
            
        Returns:
            bool: True if role has the permission
        """
        return session.query(RolePermission).join(Permission).filter(
            RolePermission.role_id == self.id,
            Permission.name == permission_name,
            Permission.status == True
        ).first() is not None
    
    def get_permissions(self, session: Session) -> List['Permission']:
        """
        Get all permissions assigned to this role.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List[Permission]: List of permission instances
        """
        return session.query(Permission).join(RolePermission).filter(
            RolePermission.role_id == self.id,
            Permission.status == True
        ).all()
    
    def get_permission_names(self, session: Session) -> Set[str]:
        """
        Get all permission names assigned to this role.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            Set[str]: Set of permission names
        """
        permissions = self.get_permissions(session)
        return {permission.name for permission in permissions}
    
    @property
    def is_system(self) -> bool:
        """Check if this is a system role."""
        return self.is_system_role.lower() == "true"
    
    @property
    def level(self) -> int:
        """Get hierarchy level as integer."""
        try:
            return int(self.hierarchy_level or "0")
        except ValueError:
            return 0
    
    @classmethod
    def find_by_name(cls, session: Session, name: str) -> Optional['Role']:
        """
        Find role by name.
        
        Args:
            session: SQLAlchemy session
            name: Role name to search for
            
        Returns:
            Role instance or None if not found
        """
        return cls.get_active_query(session).filter(
            cls.name == name.lower().strip()
        ).first()
    
    @classmethod
    def get_system_roles(cls, session: Session) -> List['Role']:
        """
        Get all system roles.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List[Role]: List of system roles
        """
        return cls.get_active_query(session).filter(
            cls.is_system_role == "true"
        ).all()
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert role to dictionary with computed fields.
        
        Args:
            include_relationships: Whether to include related objects
            
        Returns:
            Dict[str, Any]: Role data dictionary
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Add computed fields
        result['is_system'] = self.is_system
        result['level'] = self.level
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the role."""
        return f"<Role(name='{self.name}', display_name='{self.display_name}')>"


class Permission(BaseModel):
    """
    Permission model for fine-grained access control.
    
    This model defines specific permissions that can be granted to roles.
    Permissions are organized by groups and provide granular control over
    system resources and actions.
    
    Attributes:
        name (str): Unique permission name
        description (str): Human-readable permission description
        group (str): Permission group for organization
        resource (str): The resource this permission applies to
        action (str): The action this permission allows
        
    Relationships:
        roles: Many-to-many relationship with Role through RolePermission
    """
    
    __tablename__ = 'permissions'
    
    # Permission identification
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique permission name (e.g., 'user.create')"
    )
    
    description = Column(
        String(500),
        nullable=False,
        comment="Human-readable description of what this permission allows"
    )
    
    group = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Permission group for organization (e.g., 'user', 'workspace')"
    )
    
    resource = Column(
        String(50),
        nullable=False,
        comment="The resource this permission applies to"
    )
    
    action = Column(
        String(50),
        nullable=False,
        comment="The action this permission allows (create, read, update, delete)"
    )
    
    # Relationships
    role_permissions = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Add index for efficient permission checks
    __table_args__ = (
        Index('idx_permission_group_action', 'group', 'action'),
        Index('idx_permission_resource_action', 'resource', 'action'),
    )
    
    def __init__(self, name: str, description: str, group: str, 
                 resource: str = None, action: str = None, **kwargs) -> None:
        """
        Initialize a new permission instance.
        
        Args:
            name: Unique permission name
            description: Human-readable permission description
            group: Permission group for organization
            resource: Resource this permission applies to (defaults to group)
            action: Action this permission allows (extracted from name if not provided)
            **kwargs: Additional permission attributes
            
        Raises:
            ValueError: If permission format is invalid
        """
        super().__init__(**kwargs)
        
        self.name = name.lower().strip()
        self.description = description.strip()
        self.group = group.lower().strip()
        
        # Auto-extract resource and action from name if not provided
        if not resource or not action:
            parts = self.name.split('.')
            if len(parts) >= 2:
                self.resource = resource or parts[0]
                self.action = action or parts[1]
            else:
                self.resource = resource or group
                self.action = action or "access"
        else:
            self.resource = resource.lower().strip()
            self.action = action.lower().strip()
        
        # Validate during initialization
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Permission validation failed: {', '.join(errors)}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate permission data according to business rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        is_valid, errors = super().validate()
        
        # Name validation
        if not self._validate_permission_name(self.name):
            errors.append("Permission name must follow format 'resource.action' and be 3-100 characters")
        
        # Description validation
        if not self.description or len(self.description.strip()) == 0:
            errors.append("Description is required")
        
        if len(self.description) > 500:
            errors.append("Description cannot exceed 500 characters")
        
        # Group validation
        if not self.group or len(self.group) < 2 or len(self.group) > 50:
            errors.append("Group must be 2-50 characters long")
        
        # Resource validation
        if not self.resource or len(self.resource) < 2 or len(self.resource) > 50:
            errors.append("Resource must be 2-50 characters long")
        
        # Action validation
        valid_actions = {'create', 'read', 'update', 'delete', 'list', 'access', 'manage', 'admin'}
        if self.action not in valid_actions:
            errors.append(f"Action must be one of: {', '.join(valid_actions)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_permission_name(name: str) -> bool:
        """
        Validate permission name format.
        
        Args:
            name: Permission name to validate
            
        Returns:
            bool: True if permission name format is valid
        """
        import re
        
        if not name or len(name) < 3 or len(name) > 100:
            return False
        
        # Should follow pattern: resource.action or group.resource.action
        name_pattern = r'^[a-z0-9_]+(\.[a-z0-9_]+)+$'
        return re.match(name_pattern, name) is not None
    
    @classmethod
    def find_by_name(cls, session: Session, name: str) -> Optional['Permission']:
        """
        Find permission by name.
        
        Args:
            session: SQLAlchemy session
            name: Permission name to search for
            
        Returns:
            Permission instance or None if not found
        """
        return cls.get_active_query(session).filter(
            cls.name == name.lower().strip()
        ).first()
    
    @classmethod
    def get_by_group(cls, session: Session, group: str) -> List['Permission']:
        """
        Get all permissions in a specific group.
        
        Args:
            session: SQLAlchemy session
            group: Permission group name
            
        Returns:
            List[Permission]: List of permissions in the group
        """
        return cls.get_active_query(session).filter(
            cls.group == group.lower().strip()
        ).order_by(cls.name).all()
    
    @classmethod
    def get_by_resource(cls, session: Session, resource: str) -> List['Permission']:
        """
        Get all permissions for a specific resource.
        
        Args:
            session: SQLAlchemy session
            resource: Resource name
            
        Returns:
            List[Permission]: List of permissions for the resource
        """
        return cls.get_active_query(session).filter(
            cls.resource == resource.lower().strip()
        ).order_by(cls.action).all()
    
    def __repr__(self) -> str:
        """String representation of the permission."""
        return f"<Permission(name='{self.name}', group='{self.group}')>"


class RolePermission(BaseModel):
    """
    Association model for Role-Permission many-to-many relationship.
    
    This model manages the assignment of permissions to roles, providing
    audit trails and additional metadata for permission assignments.
    
    Attributes:
        role_id (UUID): Foreign key to Role model
        permission_id (UUID): Foreign key to Permission model
        granted_by (UUID): ID of user who granted this permission
        granted_date (datetime): When this permission was granted
        
    Relationships:
        role: Many-to-one relationship with Role
        permission: Many-to-one relationship with Permission
    """
    
    __tablename__ = 'role_permissions'
    
    # Foreign keys
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey('roles.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the role"
    )
    
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey('permissions.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the permission"
    )
    
    granted_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of user who granted this permission"
    )
    
    # Relationships
    role = relationship(
        "Role",
        back_populates="role_permissions",
        lazy="select"
    )
    
    permission = relationship(
        "Permission",
        back_populates="role_permissions",
        lazy="select"
    )
    
    # Ensure unique role-permission combinations
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),
        Index('idx_role_permission_role', 'role_id'),
        Index('idx_role_permission_permission', 'permission_id'),
    )
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate role-permission assignment.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        is_valid, errors = super().validate()
        
        if not self.role_id:
            errors.append("Role ID is required")
        
        if not self.permission_id:
            errors.append("Permission ID is required")
        
        return len(errors) == 0, errors
    
    def __repr__(self) -> str:
        """String representation of the role-permission assignment."""
        return f"<RolePermission(role_id='{self.role_id}', permission_id='{self.permission_id}')>"