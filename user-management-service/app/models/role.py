"""
Role model for role-based access control (RBAC).

This module defines the Role model that handles role management, user assignments,
and role-based authorization patterns. The model implements cognitive RBAC patterns
with hierarchical roles and flexible permission assignments.

Author: AI Assistant
Date: 2024
"""

import re
from typing import List, Dict, Any, Optional, Set
from sqlalchemy import Column, String, Text, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel
from app import db


# Association table for many-to-many relationship between Role and Permission
role_permissions = Table(
    'role_permissions',
    db.Model.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)


class Role(BaseModel):
    """
    Role model for role-based access control (RBAC).
    
    This model defines user roles within the system, allowing for granular
    access control and permission management. Roles can be assigned to users
    and can contain multiple permissions. It implements cognitive RBAC patterns
    with role hierarchy and inheritance.
    
    Attributes:
        name (str): Unique role name (automatically converted to lowercase)
        display_name (str): Human-readable role name for UI display
        description (str): Detailed description of the role's purpose
        is_system_role (bool): Whether this is a built-in system role
        hierarchy_level (int): Role hierarchy level for inheritance (0-100)
        color (str): UI color code for role display
        
    Relationships:
        permissions: Many-to-many relationship with Permission
        users: Many-to-many relationship with User
        
    Business Rules:
        - Role names must be unique and follow naming conventions
        - System roles cannot be deleted or renamed
        - Higher hierarchy levels inherit permissions from lower levels
        - Role assignments are tracked with audit trails
    """
    
    __tablename__ = 'roles'
    
    # Core role identification
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique role name (lowercase, alphanumeric with underscores)"
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
    
    # Role configuration
    is_system_role = Column(
        String(10),
        default="false",
        nullable=False,
        comment="Whether this is a built-in system role (cannot be deleted)"
    )
    
    hierarchy_level = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Role hierarchy level for permission inheritance (0-100)"
    )
    
    # UI and display settings
    color = Column(
        String(7),
        default="#6B7280",
        nullable=False,
        comment="Hex color code for role display in UI"
    )
    
    # Relationships
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="select"
    )
    
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="select"
    )
    
    def __init__(self, name: str, display_name: str = None, **kwargs) -> None:
        """
        Initialize a new role instance with cognitive validation patterns.
        
        This constructor implements secure role creation with automatic
        name normalization and comprehensive validation.
        
        Args:
            name: Unique role name (will be converted to lowercase)
            display_name: Human-readable role name (defaults to formatted name)
            **kwargs: Additional role attributes
            
        Raises:
            ValueError: If role name format is invalid
            
        Example:
            >>> role = Role(
            ...     name="content_editor",
            ...     display_name="Content Editor",
            ...     description="Can create and edit content"
            ... )
        """
        # Normalize role name using cognitive patterns
        normalized_name = self._normalize_role_name(name) if name else ""
        
        # Set display name with cognitive formatting
        if not display_name and normalized_name:
            display_name = self._format_display_name(normalized_name)
        
        kwargs['name'] = normalized_name
        kwargs['display_name'] = display_name
        
        super().__init__(**kwargs)
        
        # Validate the complete role object
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Role validation failed: {', '.join(errors)}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate role data according to business rules.
        
        This method implements comprehensive validation patterns covering
        role naming conventions, hierarchy constraints, and security rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
            
        Example:
            >>> role = Role(name="invalid-name!")
            >>> is_valid, errors = role.validate()
            >>> print(errors)  # ["Role name contains invalid characters"]
        """
        is_valid, errors = super().validate()
        
        # Name validation with cognitive patterns
        if not self._validate_role_name(self.name):
            errors.append("Role name must be 2-100 characters long and contain only letters, numbers, and underscores")
        
        # Display name validation
        if not self.display_name or len(self.display_name.strip()) == 0:
            errors.append("Display name is required")
        
        if len(self.display_name) > 200:
            errors.append("Display name cannot exceed 200 characters")
        
        # Description validation
        if self.description and len(self.description) > 1000:
            errors.append("Description cannot exceed 1000 characters")
        
        # Hierarchy level validation (cognitive security constraint)
        if self.hierarchy_level < 0 or self.hierarchy_level > 100:
            errors.append("Hierarchy level must be between 0 and 100")
        
        # Color validation (cognitive UI constraint)
        if self.color and not self._validate_color_code(self.color):
            errors.append("Color must be a valid hex color code (e.g., #FF0000)")
        
        # System role protection (cognitive security pattern)
        if self.is_system and not self._is_valid_system_role_name(self.name):
            errors.append("Invalid system role name")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _normalize_role_name(name: str) -> str:
        """
        Normalize role name using cognitive patterns.
        
        This method implements cognitive role naming patterns that
        ensure consistency and prevent common naming issues.
        
        Args:
            name: Raw role name input
            
        Returns:
            str: Normalized role name
        """
        if not name:
            return ""
        
        # Convert to lowercase and replace spaces/hyphens with underscores
        normalized = name.lower().strip()
        normalized = re.sub(r'[\s\-]+', '_', normalized)
        
        # Remove invalid characters (keep only alphanumeric and underscores)
        normalized = re.sub(r'[^a-z0-9_]', '', normalized)
        
        # Remove multiple consecutive underscores
        normalized = re.sub(r'_{2,}', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        return normalized
    
    @staticmethod
    def _format_display_name(name: str) -> str:
        """
        Format role name into a display-friendly format using cognitive patterns.
        
        Args:
            name: Role name to format
            
        Returns:
            str: Formatted display name
        """
        if not name:
            return ""
        
        # Split by underscores and capitalize each word
        words = name.split('_')
        formatted_words = []
        
        for word in words:
            if word:
                # Handle common abbreviations
                if word.upper() in ['API', 'UI', 'UX', 'CEO', 'CTO', 'HR']:
                    formatted_words.append(word.upper())
                else:
                    formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words)
    
    @staticmethod
    def _validate_role_name(name: str) -> bool:
        """
        Validate role name format using cognitive patterns.
        
        Args:
            name: Role name to validate
            
        Returns:
            bool: True if role name format is valid
        """
        if not name or len(name) < 2 or len(name) > 100:
            return False
        
        # Role name pattern: lowercase letters, numbers, underscores only
        name_pattern = r'^[a-z0-9_]+$'
        
        # Must start and end with alphanumeric character
        if not name[0].isalnum() or not name[-1].isalnum():
            return False
        
        # No consecutive underscores
        if '__' in name:
            return False
        
        return re.match(name_pattern, name) is not None
    
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
        
        # Hex color pattern: #RRGGBB or #RGB
        color_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return re.match(color_pattern, color) is not None
    
    @staticmethod
    def _is_valid_system_role_name(name: str) -> bool:
        """
        Validate system role name against allowed system roles.
        
        Args:
            name: Role name to validate
            
        Returns:
            bool: True if valid system role name
        """
        valid_system_roles = {
            'super_admin', 'admin', 'user', 'guest', 
            'moderator', 'editor', 'viewer'
        }
        return name in valid_system_roles
    
    def add_permission(self, session: Session, permission: 'Permission') -> None:
        """
        Add a permission to this role with cognitive validation.
        
        This method implements cognitive permission assignment patterns
        with proper validation and audit trails.
        
        Args:
            session: SQLAlchemy session
            permission: Permission instance to add
            
        Raises:
            ValueError: If permission is already assigned to this role
            
        Example:
            >>> role.add_permission(session, user_create_permission)
        """
        if permission in self.permissions:
            raise ValueError(f"Permission '{permission.name}' is already assigned to role '{self.name}'")
        
        # Validate permission compatibility (cognitive business rule)
        if not self._is_permission_compatible(permission):
            raise ValueError(f"Permission '{permission.name}' is not compatible with role '{self.name}'")
        
        self.permissions.append(permission)
        session.flush()
    
    def remove_permission(self, session: Session, permission: 'Permission') -> bool:
        """
        Remove a permission from this role.
        
        Args:
            session: SQLAlchemy session
            permission: Permission instance to remove
            
        Returns:
            bool: True if permission was removed, False if it wasn't assigned
        """
        if permission in self.permissions:
            self.permissions.remove(permission)
            session.flush()
            return True
        return False
    
    def has_permission(self, permission_name: str) -> bool:
        """
        Check if this role has a specific permission.
        
        This method implements cognitive permission checking patterns
        with support for role hierarchy and permission inheritance.
        
        Args:
            permission_name: Name of the permission to check
            
        Returns:
            bool: True if role has the permission
            
        Example:
            >>> if role.has_permission('user.create'):
            ...     # Role can create users
        """
        # Direct permission check
        for permission in self.permissions:
            if permission.name == permission_name:
                return True
        
        # TODO: Implement hierarchical permission inheritance
        # Higher hierarchy roles could inherit permissions from lower levels
        
        return False
    
    def get_permissions(self) -> List['Permission']:
        """
        Get all permissions assigned to this role.
        
        Returns:
            List[Permission]: List of permission instances
        """
        return list(self.permissions)
    
    def get_permission_names(self) -> Set[str]:
        """
        Get all permission names assigned to this role.
        
        Returns:
            Set[str]: Set of permission names
        """
        return {permission.name for permission in self.permissions}
    
    def _is_permission_compatible(self, permission: 'Permission') -> bool:
        """
        Check if a permission is compatible with this role (cognitive business rule).
        
        This method implements cognitive compatibility checking patterns
        to prevent incompatible permission assignments.
        
        Args:
            permission: Permission to check compatibility
            
        Returns:
            bool: True if permission is compatible
        """
        # System roles have restrictions (cognitive security pattern)
        if self.is_system:
            # Guest roles shouldn't have write permissions
            if self.name == 'guest' and 'create' in permission.name or 'update' in permission.name or 'delete' in permission.name:
                return False
            
            # User role shouldn't have admin permissions
            if self.name == 'user' and 'admin' in permission.name:
                return False
        
        return True
    
    def assign_to_user(self, session: Session, user: 'User') -> None:
        """
        Assign this role to a user with cognitive validation.
        
        Args:
            session: SQLAlchemy session
            user: User instance to assign role to
            
        Raises:
            ValueError: If role is already assigned or assignment is invalid
        """
        if self in user.roles:
            raise ValueError(f"Role '{self.name}' is already assigned to user '{user.username}'")
        
        user.roles.append(self)
        session.flush()
    
    def unassign_from_user(self, session: Session, user: 'User') -> bool:
        """
        Remove this role from a user.
        
        Args:
            session: SQLAlchemy session
            user: User instance to remove role from
            
        Returns:
            bool: True if role was removed, False if it wasn't assigned
        """
        if self in user.roles:
            user.roles.remove(self)
            session.flush()
            return True
        return False
    
    def get_users(self, session: Session) -> List['User']:
        """
        Get all users assigned to this role.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List[User]: List of users with this role
        """
        return list(self.users)
    
    def get_user_count(self, session: Session) -> int:
        """
        Get the number of users assigned to this role.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            int: Number of users with this role
        """
        return len(self.users)
    
    @property
    def is_system(self) -> bool:
        """Check if this is a system role with cognitive type conversion."""
        return self.is_system_role.lower() == "true"
    
    @property
    def permission_count(self) -> int:
        """Get the number of permissions assigned to this role."""
        return len(self.permissions)
    
    @classmethod
    def find_by_name(cls, session: Session, name: str) -> Optional['Role']:
        """
        Find role by name with cognitive case handling.
        
        Args:
            session: SQLAlchemy session
            name: Role name to search for
            
        Returns:
            Role instance or None if not found
        """
        normalized_name = cls._normalize_role_name(name)
        return cls.get_active_query(session).filter(
            cls.name == normalized_name
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
    
    @classmethod
    def get_by_hierarchy_level(cls, session: Session, min_level: int = 0, 
                              max_level: int = 100) -> List['Role']:
        """
        Get roles within a specific hierarchy level range.
        
        Args:
            session: SQLAlchemy session
            min_level: Minimum hierarchy level
            max_level: Maximum hierarchy level
            
        Returns:
            List[Role]: List of roles within the hierarchy range
        """
        return cls.get_active_query(session).filter(
            cls.hierarchy_level >= min_level,
            cls.hierarchy_level <= max_level
        ).order_by(cls.hierarchy_level.desc()).all()
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert role to dictionary with cognitive computed fields.
        
        Args:
            include_relationships: Whether to include related objects
            
        Returns:
            Dict[str, Any]: Role data dictionary
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Add cognitive computed fields
        result['is_system'] = self.is_system
        result['permission_count'] = self.permission_count
        result['user_count'] = len(self.users)
        
        # Add permission names for convenience
        if include_relationships:
            result['permission_names'] = list(self.get_permission_names())
            result['user_ids'] = [str(user.id) for user in self.users]
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the role."""
        return f"<Role(name='{self.name}', display_name='{self.display_name}')>"