"""
Role Model for User Management Microservice.

This module defines the Role model for implementing role-based access control (RBAC)
with hierarchical permissions and comprehensive role management.
"""

import re
from typing import Optional, List, Dict, Any, Set
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from .base import BaseModel

# Association table for many-to-many relationship between Role and Permission
role_permissions = Table(
    'role_permissions',
    db.Model.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class Permission(BaseModel):
    """
    Permission model for fine-grained access control.
    
    Represents individual permissions that can be assigned to roles.
    Uses a resource-action pattern for flexible permission management.
    
    Attributes:
        name: Unique permission name (e.g., 'user:read', 'post:create')
        resource: Resource type this permission applies to (e.g., 'user', 'post')
        action: Action this permission allows (e.g., 'read', 'create', 'update', 'delete')
        description: Human-readable description of the permission
        is_system: Whether this is a system-level permission (cannot be deleted)
    
    Relationships:
        roles: Many-to-many relationship with Role model
    """
    
    __tablename__ = 'permissions'
    
    name = Column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="Unique permission name in resource:action format"
    )
    
    resource = Column(
        String(50), 
        nullable=False, 
        index=True,
        doc="Resource type this permission applies to"
    )
    
    action = Column(
        String(50), 
        nullable=False,
        doc="Action this permission allows (read, create, update, delete, etc.)"
    )
    
    description = Column(
        Text(500), 
        nullable=True,
        doc="Human-readable description of what this permission allows"
    )
    
    is_system = Column(
        Boolean, 
        default=False, 
        nullable=False,
        doc="System-level permissions cannot be deleted or modified"
    )
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        doc="Many-to-many relationship with roles"
    )
    
    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """
        Validate permission name format (resource:action).
        
        Args:
            key: Field name being validated
            name: Permission name to validate
            
        Returns:
            Validated permission name
            
        Raises:
            ValueError: If name format is invalid
        """
        if not name:
            raise ValueError("Permission name is required")
        
        name = name.strip().lower()
        
        # Validate resource:action format
        if ':' not in name:
            raise ValueError("Permission name must be in 'resource:action' format")
        
        parts = name.split(':')
        if len(parts) != 2:
            raise ValueError("Permission name must have exactly one colon separator")
        
        resource, action = parts
        if not resource or not action:
            raise ValueError("Both resource and action parts are required")
        
        # Validate format (alphanumeric, underscores, hyphens)
        if not re.match(r'^[a-z0-9_-]+:[a-z0-9_-]+$', name):
            raise ValueError(
                "Permission name can only contain lowercase letters, numbers, "
                "underscores, and hyphens"
            )
        
        return name
    
    @validates('resource', 'action')
    def validate_resource_action(self, key: str, value: str) -> str:
        """
        Validate resource and action components.
        
        Args:
            key: Field name being validated
            value: Value to validate
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If format is invalid
        """
        if not value:
            raise ValueError(f"{key.title()} is required")
        
        value = value.strip().lower()
        
        if not re.match(r'^[a-z0-9_-]+$', value):
            raise ValueError(
                f"{key.title()} can only contain lowercase letters, numbers, "
                "underscores, and hyphens"
            )
        
        return value
    
    def __repr__(self) -> str:
        """String representation of the permission."""
        return f"<Permission(id={self.id}, name='{self.name}')>"


class Role(BaseModel):
    """
    Role model for implementing role-based access control (RBAC).
    
    Supports hierarchical role structures with inheritance and provides
    comprehensive role management capabilities including:
    - Permission assignment and inheritance
    - Role hierarchy with parent-child relationships
    - Built-in and custom role types
    - Role activation/deactivation
    
    Attributes:
        name: Unique role name (e.g., 'admin', 'user', 'moderator')
        display_name: Human-readable role name for UI display
        description: Detailed description of role purpose and capabilities
        is_active: Whether the role is currently active and assignable
        is_system: Whether this is a system role (cannot be deleted)
        priority: Role priority for hierarchical ordering (higher = more privileged)
        parent_id: Foreign key to parent role for inheritance
        max_users: Maximum number of users that can have this role (None = unlimited)
    
    Relationships:
        users: Many-to-many relationship with User model
        permissions: Many-to-many relationship with Permission model
        parent: Self-referential relationship to parent role
        children: Self-referential relationship to child roles
    """
    
    __tablename__ = 'roles'
    
    name = Column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="Unique role name (lowercase, alphanumeric, underscores)"
    )
    
    display_name = Column(
        String(100), 
        nullable=False,
        doc="Human-readable role name for UI display"
    )
    
    description = Column(
        Text(1000), 
        nullable=True,
        doc="Detailed description of role purpose and capabilities"
    )
    
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        doc="Whether the role is currently active and assignable"
    )
    
    is_system = Column(
        Boolean, 
        default=False, 
        nullable=False,
        doc="System roles cannot be deleted or have core attributes modified"
    )
    
    priority = Column(
        Integer, 
        default=0, 
        nullable=False,
        doc="Role priority for hierarchical ordering (higher = more privileged)"
    )
    
    # Hierarchical structure
    parent_id = Column(
        Integer, 
        ForeignKey('roles.id'), 
        nullable=True,
        doc="Foreign key to parent role for inheritance"
    )
    
    max_users = Column(
        Integer, 
        nullable=True,
        doc="Maximum number of users that can have this role (None = unlimited)"
    )
    
    # Relationships
    users = relationship(
        "User",
        secondary="user_roles",  # Reference the table name as string
        back_populates="roles",
        doc="Many-to-many relationship with users"
    )
    
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        doc="Many-to-many relationship with permissions"
    )
    
    # Self-referential relationships for hierarchy
    parent = relationship(
        "Role", 
        remote_side="Role.id", 
        backref="children",
        doc="Parent role for inheritance"
    )
    
    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """
        Validate role name format.
        
        Args:
            key: Field name being validated
            name: Role name to validate
            
        Returns:
            Validated role name
            
        Raises:
            ValueError: If name format is invalid
        """
        if not name:
            raise ValueError("Role name is required")
        
        name = name.strip().lower()
        
        if len(name) < 2:
            raise ValueError("Role name must be at least 2 characters long")
        
        if len(name) > 50:
            raise ValueError("Role name cannot exceed 50 characters")
        
        # Only allow alphanumeric characters and underscores
        if not re.match(r'^[a-z0-9_]+$', name):
            raise ValueError(
                "Role name can only contain lowercase letters, numbers, and underscores"
            )
        
        return name
    
    @validates('display_name')
    def validate_display_name(self, key: str, display_name: str) -> str:
        """
        Validate display name format.
        
        Args:
            key: Field name being validated
            display_name: Display name to validate
            
        Returns:
            Validated display name
            
        Raises:
            ValueError: If display name is invalid
        """
        if not display_name:
            raise ValueError("Display name is required")
        
        display_name = display_name.strip()
        
        if len(display_name) < 2:
            raise ValueError("Display name must be at least 2 characters long")
        
        if len(display_name) > 100:
            raise ValueError("Display name cannot exceed 100 characters")
        
        return display_name
    
    @validates('priority')
    def validate_priority(self, key: str, priority: int) -> int:
        """
        Validate role priority value.
        
        Args:
            key: Field name being validated
            priority: Priority value to validate
            
        Returns:
            Validated priority
            
        Raises:
            ValueError: If priority is out of valid range
        """
        if priority < 0 or priority > 1000:
            raise ValueError("Role priority must be between 0 and 1000")
        
        return priority
    
    @validates('max_users')
    def validate_max_users(self, key: str, max_users: Optional[int]) -> Optional[int]:
        """
        Validate maximum users limit.
        
        Args:
            key: Field name being validated
            max_users: Maximum users value to validate
            
        Returns:
            Validated max_users value
            
        Raises:
            ValueError: If max_users is invalid
        """
        if max_users is not None and max_users < 1:
            raise ValueError("Maximum users must be at least 1 or None for unlimited")
        
        return max_users
    
    def get_all_permissions(self) -> Set[str]:
        """
        Get all permissions for this role, including inherited ones.
        
        Returns:
            Set of permission names including those inherited from parent roles
            
        Example:
            >>> role = Role.query.filter_by(name='editor').first()
            >>> permissions = role.get_all_permissions()
            >>> 'user:read' in permissions
            True
        """
        permissions = {perm.name for perm in self.permissions}
        
        # Add inherited permissions from parent roles
        if self.parent:
            permissions.update(self.parent.get_all_permissions())
        
        return permissions
    
    def has_permission(self, permission_name: str) -> bool:
        """
        Check if role has a specific permission (including inherited).
        
        Args:
            permission_name: Name of the permission to check
            
        Returns:
            True if role has the permission, False otherwise
            
        Example:
            >>> role.has_permission('user:read')
            True
        """
        return permission_name in self.get_all_permissions()
    
    def add_permission(self, permission: Permission) -> None:
        """
        Add a permission to this role.
        
        Args:
            permission: Permission instance to add
            
        Raises:
            ValueError: If permission is already assigned or role is system role
        """
        if self.is_system:
            raise ValueError("Cannot modify permissions for system roles")
        
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.save()
    
    def remove_permission(self, permission: Permission) -> None:
        """
        Remove a permission from this role.
        
        Args:
            permission: Permission instance to remove
            
        Raises:
            ValueError: If role is system role
        """
        if self.is_system:
            raise ValueError("Cannot modify permissions for system roles")
        
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.save()
    
    def can_assign_to_user(self) -> bool:
        """
        Check if this role can be assigned to a new user.
        
        Returns:
            True if role can be assigned (active and under user limit)
        """
        if not self.is_active:
            return False
        
        if self.max_users is None:
            return True
        
        current_user_count = len(self.users)
        return current_user_count < self.max_users
    
    def get_user_count(self) -> int:
        """
        Get the number of users currently assigned to this role.
        
        Returns:
            Number of users with this role
        """
        return len(self.users)
    
    def is_higher_priority_than(self, other_role: 'Role') -> bool:
        """
        Compare priority with another role.
        
        Args:
            other_role: Role to compare with
            
        Returns:
            True if this role has higher priority
        """
        return self.priority > other_role.priority
    
    def get_hierarchy_path(self) -> List['Role']:
        """
        Get the complete hierarchy path from root to this role.
        
        Returns:
            List of roles from root parent to this role
            
        Example:
            >>> role.get_hierarchy_path()
            [<Role(name='user')>, <Role(name='moderator')>, <Role(name='admin')>]
        """
        path = []
        current_role = self
        
        # Build path from current role to root
        while current_role:
            path.insert(0, current_role)
            current_role = current_role.parent
        
        return path
    
    def get_all_descendants(self) -> List['Role']:
        """
        Get all descendant roles (children, grandchildren, etc.).
        
        Returns:
            List of all descendant roles
        """
        descendants = []
        
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        
        return descendants
    
    @classmethod
    def get_system_roles(cls) -> List['Role']:
        """
        Get all system roles.
        
        Returns:
            List of system roles
        """
        return cls.query.filter_by(is_system=True).all()
    
    @classmethod
    def get_assignable_roles(cls) -> List['Role']:
        """
        Get all roles that can be assigned to users.
        
        Returns:
            List of active, non-system roles that haven't reached user limits
        """
        roles = cls.query.filter_by(is_active=True, is_system=False).all()
        return [role for role in roles if role.can_assign_to_user()]
    
    def to_dict(self, include_permissions: bool = False, 
                include_hierarchy: bool = False) -> Dict[str, Any]:
        """
        Convert role instance to dictionary with optional additional data.
        
        Args:
            include_permissions: Whether to include permission details
            include_hierarchy: Whether to include hierarchy information
            
        Returns:
            Dictionary representation of the role
        """
        role_dict = super().to_dict()
        
        # Add computed fields
        role_dict['user_count'] = self.get_user_count()
        role_dict['can_assign'] = self.can_assign_to_user()
        
        if include_permissions:
            role_dict['permissions'] = [perm.name for perm in self.permissions]
            role_dict['all_permissions'] = list(self.get_all_permissions())
        
        if include_hierarchy:
            role_dict['parent_name'] = self.parent.name if self.parent else None
            role_dict['children_names'] = [child.name for child in self.children]
            role_dict['hierarchy_path'] = [role.name for role in self.get_hierarchy_path()]
        
        return role_dict
    
    def validate(self) -> bool:
        """
        Comprehensive validation of role instance.
        
        Returns:
            True if all validations pass
            
        Raises:
            ValueError: If any validation fails
        """
        # Validate required fields
        if not self.name:
            raise ValueError("Role name is required")
        
        if not self.display_name:
            raise ValueError("Display name is required")
        
        # Validate hierarchy doesn't create cycles
        if self.parent_id:
            if self.parent_id == self.id:
                raise ValueError("Role cannot be its own parent")
            
            # Check for circular references (simplified check)
            current_parent = self.parent
            visited = {self.id}
            while current_parent:
                if current_parent.id in visited:
                    raise ValueError("Circular reference detected in role hierarchy")
                visited.add(current_parent.id)
                current_parent = current_parent.parent
        
        return True
    
    def __repr__(self) -> str:
        """String representation of the role."""
        return f"<Role(id={self.id}, name='{self.name}', priority={self.priority})>"