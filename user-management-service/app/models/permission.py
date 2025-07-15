"""
Permission model for fine-grained access control.

This module defines the Permission model that handles specific permissions
that can be granted to roles. Permissions provide granular control over
system resources and actions with cognitive authorization patterns.

Author: AI Assistant
Date: 2024
"""

import re
from typing import List, Dict, Any, Optional, Set
from sqlalchemy import Column, String, Text, Index
from sqlalchemy.orm import relationship, Session

from .base import BaseModel


class Permission(BaseModel):
    """
    Permission model for fine-grained access control.
    
    This model defines specific permissions that can be granted to roles.
    Permissions are organized by groups and provide granular control over
    system resources and actions. It implements cognitive authorization
    patterns with resource-action mapping and scope-based permissions.
    
    Attributes:
        name (str): Unique permission name (e.g., 'user.create')
        display_name (str): Human-readable permission name
        description (str): Human-readable permission description
        group (str): Permission group for organization
        resource (str): The resource this permission applies to
        action (str): The action this permission allows
        scope (str): Permission scope (global, workspace, personal)
        
    Relationships:
        roles: Many-to-many relationship with Role
        
    Business Rules:
        - Permission names follow format: 'resource.action' or 'group.resource.action'
        - System permissions cannot be deleted or modified
        - Permissions are grouped logically for management
        - Scopes determine the context where permissions apply
    """
    
    __tablename__ = 'permissions'
    
    # Core permission identification
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique permission name (e.g., 'user.create', 'workspace.article.edit')"
    )
    
    display_name = Column(
        String(200),
        nullable=False,
        comment="Human-readable permission name for UI display"
    )
    
    description = Column(
        String(500),
        nullable=False,
        comment="Human-readable description of what this permission allows"
    )
    
    # Organization and categorization
    group = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Permission group for organization (e.g., 'user', 'workspace', 'system')"
    )
    
    resource = Column(
        String(50),
        nullable=False,
        comment="The resource this permission applies to (e.g., 'user', 'article', 'role')"
    )
    
    action = Column(
        String(50),
        nullable=False,
        comment="The action this permission allows (e.g., 'create', 'read', 'update', 'delete')"
    )
    
    # Permission scope and context
    scope = Column(
        String(20),
        default='global',
        nullable=False,
        comment="Permission scope: 'global', 'workspace', or 'personal'"
    )
    
    # System permission flag
    is_system_permission = Column(
        String(10),
        default="false",
        nullable=False,
        comment="Whether this is a built-in system permission (cannot be deleted)"
    )
    
    # Relationships
    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="select"
    )
    
    # Add compound indexes for efficient permission checks
    __table_args__ = (
        Index('idx_permission_group_action', 'group', 'action'),
        Index('idx_permission_resource_action', 'resource', 'action'),
        Index('idx_permission_scope', 'scope'),
    )
    
    def __init__(self, name: str, description: str, group: str, 
                 resource: str = None, action: str = None, **kwargs) -> None:
        """
        Initialize a new permission instance with cognitive validation patterns.
        
        This constructor implements secure permission creation with automatic
        name normalization, resource/action extraction, and validation.
        
        Args:
            name: Unique permission name
            description: Human-readable permission description
            group: Permission group for organization
            resource: Resource this permission applies to (auto-extracted if not provided)
            action: Action this permission allows (auto-extracted if not provided)
            **kwargs: Additional permission attributes
            
        Raises:
            ValueError: If permission format is invalid
            
        Example:
            >>> permission = Permission(
            ...     name="user.create",
            ...     description="Create new users",
            ...     group="user"
            ... )
        """
        # Normalize permission name using cognitive patterns
        normalized_name = self._normalize_permission_name(name) if name else ""
        
        # Auto-extract resource and action from name if not provided
        if not resource or not action:
            extracted_resource, extracted_action = self._extract_resource_action(normalized_name)
            resource = resource or extracted_resource
            action = action or extracted_action
        
        # Normalize inputs
        normalized_group = group.lower().strip() if group else ""
        normalized_resource = resource.lower().strip() if resource else ""
        normalized_action = action.lower().strip() if action else ""
        
        # Generate display name if not provided
        display_name = kwargs.get('display_name')
        if not display_name:
            display_name = self._generate_display_name(normalized_name, normalized_resource, normalized_action)
        
        # Set normalized values
        kwargs.update({
            'name': normalized_name,
            'display_name': display_name,
            'description': description.strip() if description else "",
            'group': normalized_group,
            'resource': normalized_resource,
            'action': normalized_action
        })
        
        super().__init__(**kwargs)
        
        # Validate the complete permission object
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Permission validation failed: {', '.join(errors)}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate permission data according to business rules.
        
        This method implements comprehensive validation patterns covering
        permission naming conventions, resource/action constraints, and security rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
            
        Example:
            >>> permission = Permission(name="invalid!", description="test", group="test")
            >>> is_valid, errors = permission.validate()
            >>> print(errors)  # ["Permission name format is invalid"]
        """
        is_valid, errors = super().validate()
        
        # Name validation with cognitive patterns
        if not self._validate_permission_name(self.name):
            errors.append("Permission name must follow format 'resource.action' and be 3-100 characters")
        
        # Description validation
        if not self.description or len(self.description.strip()) == 0:
            errors.append("Description is required")
        
        if len(self.description) > 500:
            errors.append("Description cannot exceed 500 characters")
        
        # Display name validation
        if not self.display_name or len(self.display_name.strip()) == 0:
            errors.append("Display name is required")
        
        if len(self.display_name) > 200:
            errors.append("Display name cannot exceed 200 characters")
        
        # Group validation
        if not self.group or len(self.group) < 2 or len(self.group) > 50:
            errors.append("Group must be 2-50 characters long")
        
        # Resource validation
        if not self.resource or len(self.resource) < 2 or len(self.resource) > 50:
            errors.append("Resource must be 2-50 characters long")
        
        # Action validation with cognitive constraints
        valid_actions = {
            'create', 'read', 'update', 'delete', 'list', 'view',
            'edit', 'manage', 'admin', 'access', 'execute', 'approve'
        }
        if self.action not in valid_actions:
            errors.append(f"Action must be one of: {', '.join(sorted(valid_actions))}")
        
        # Scope validation
        valid_scopes = {'global', 'workspace', 'personal'}
        if self.scope not in valid_scopes:
            errors.append(f"Scope must be one of: {', '.join(valid_scopes)}")
        
        # Cross-field validation (cognitive business rules)
        if not self._validate_name_consistency():
            errors.append("Permission name must be consistent with resource and action")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _normalize_permission_name(name: str) -> str:
        """
        Normalize permission name using cognitive patterns.
        
        This method implements cognitive permission naming patterns that
        ensure consistency and prevent common naming issues.
        
        Args:
            name: Raw permission name input
            
        Returns:
            str: Normalized permission name
        """
        if not name:
            return ""
        
        # Convert to lowercase and clean up
        normalized = name.lower().strip()
        
        # Replace spaces and hyphens with dots
        normalized = re.sub(r'[\s\-]+', '.', normalized)
        
        # Remove invalid characters (keep only alphanumeric, dots, and underscores)
        normalized = re.sub(r'[^a-z0-9._]', '', normalized)
        
        # Remove multiple consecutive dots
        normalized = re.sub(r'\.{2,}', '.', normalized)
        
        # Remove leading/trailing dots
        normalized = normalized.strip('.')
        
        return normalized
    
    @staticmethod
    def _extract_resource_action(name: str) -> tuple[str, str]:
        """
        Extract resource and action from permission name using cognitive patterns.
        
        Args:
            name: Permission name to parse
            
        Returns:
            tuple[str, str]: (resource, action)
        """
        if not name:
            return "", ""
        
        parts = name.split('.')
        
        if len(parts) >= 2:
            # Standard format: resource.action or group.resource.action
            if len(parts) == 2:
                return parts[0], parts[1]
            elif len(parts) >= 3:
                # Use last two parts as resource.action
                return parts[-2], parts[-1]
        
        # Fallback: assume name is the resource, default action
        return name, "access"
    
    @staticmethod
    def _generate_display_name(name: str, resource: str, action: str) -> str:
        """
        Generate display name from permission components using cognitive patterns.
        
        Args:
            name: Permission name
            resource: Resource name
            action: Action name
            
        Returns:
            str: Generated display name
        """
        if not name:
            return ""
        
        # Map actions to human-readable verbs
        action_map = {
            'create': 'Create',
            'read': 'Read',
            'view': 'View',
            'update': 'Update',
            'edit': 'Edit',
            'delete': 'Delete',
            'list': 'List',
            'manage': 'Manage',
            'admin': 'Administer',
            'access': 'Access',
            'execute': 'Execute',
            'approve': 'Approve'
        }
        
        # Map resources to human-readable nouns
        resource_map = {
            'user': 'Users',
            'role': 'Roles',
            'permission': 'Permissions',
            'workspace': 'Workspaces',
            'article': 'Articles',
            'domain': 'Domains',
            'image': 'Images',
            'notification': 'Notifications'
        }
        
        action_verb = action_map.get(action, action.capitalize())
        resource_noun = resource_map.get(resource, resource.capitalize())
        
        return f"{action_verb} {resource_noun}"
    
    @staticmethod
    def _validate_permission_name(name: str) -> bool:
        """
        Validate permission name format using cognitive patterns.
        
        Args:
            name: Permission name to validate
            
        Returns:
            bool: True if permission name format is valid
        """
        if not name or len(name) < 3 or len(name) > 100:
            return False
        
        # Permission name pattern: resource.action or group.resource.action
        name_pattern = r'^[a-z0-9_]+(\.[a-z0-9_]+)+$'
        
        if not re.match(name_pattern, name):
            return False
        
        # Must have at least one dot
        if '.' not in name:
            return False
        
        # Parts must not be empty
        parts = name.split('.')
        if any(len(part) == 0 for part in parts):
            return False
        
        return True
    
    def _validate_name_consistency(self) -> bool:
        """
        Validate that permission name is consistent with resource and action.
        
        This method implements cognitive consistency checking to ensure
        the permission name accurately reflects its components.
        
        Returns:
            bool: True if name is consistent with resource and action
        """
        if not self.name or not self.resource or not self.action:
            return False
        
        # Extract resource and action from name
        extracted_resource, extracted_action = self._extract_resource_action(self.name)
        
        # Check consistency (allow some flexibility for legacy permissions)
        resource_match = (extracted_resource == self.resource or 
                         extracted_resource in self.resource or 
                         self.resource in extracted_resource)
        
        action_match = (extracted_action == self.action or
                       extracted_action in self.action or
                       self.action in extracted_action)
        
        return resource_match and action_match
    
    def is_applicable_to_resource(self, resource_type: str) -> bool:
        """
        Check if this permission applies to a specific resource type.
        
        This method implements cognitive resource matching patterns
        for flexible permission checking across different contexts.
        
        Args:
            resource_type: Type of resource to check
            
        Returns:
            bool: True if permission applies to the resource type
            
        Example:
            >>> permission = Permission(name="user.create", ...)
            >>> permission.is_applicable_to_resource("user")  # True
        """
        if not resource_type:
            return False
        
        resource_type = resource_type.lower()
        
        # Direct match
        if self.resource == resource_type:
            return True
        
        # Wildcard permissions (admin, manage)
        if self.action in ['admin', 'manage'] and self.resource in ['system', 'all']:
            return True
        
        # Group-level permissions
        if self.group == resource_type and self.action in ['admin', 'manage']:
            return True
        
        return False
    
    def get_scope_description(self) -> str:
        """
        Get human-readable description of permission scope.
        
        Returns:
            str: Description of what the scope means
        """
        scope_descriptions = {
            'global': 'Applies across the entire system',
            'workspace': 'Applies within specific workspaces',
            'personal': 'Applies only to user\'s own resources'
        }
        
        return scope_descriptions.get(self.scope, 'Unknown scope')
    
    @property
    def is_system(self) -> bool:
        """Check if this is a system permission with cognitive type conversion."""
        return self.is_system_permission.lower() == "true"
    
    @property
    def permission_level(self) -> str:
        """
        Get the permission level based on action (cognitive security pattern).
        
        Returns:
            str: Permission level (read, write, admin)
        """
        read_actions = {'read', 'view', 'list', 'access'}
        write_actions = {'create', 'update', 'edit', 'delete'}
        admin_actions = {'manage', 'admin', 'approve', 'execute'}
        
        if self.action in admin_actions:
            return 'admin'
        elif self.action in write_actions:
            return 'write'
        elif self.action in read_actions:
            return 'read'
        else:
            return 'custom'
    
    @classmethod
    def find_by_name(cls, session: Session, name: str) -> Optional['Permission']:
        """
        Find permission by name with cognitive case handling.
        
        Args:
            session: SQLAlchemy session
            name: Permission name to search for
            
        Returns:
            Permission instance or None if not found
        """
        normalized_name = cls._normalize_permission_name(name)
        return cls.get_active_query(session).filter(
            cls.name == normalized_name
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
    
    @classmethod
    def get_by_action(cls, session: Session, action: str) -> List['Permission']:
        """
        Get all permissions for a specific action.
        
        Args:
            session: SQLAlchemy session
            action: Action name
            
        Returns:
            List[Permission]: List of permissions for the action
        """
        return cls.get_active_query(session).filter(
            cls.action == action.lower().strip()
        ).order_by(cls.resource).all()
    
    @classmethod
    def get_by_scope(cls, session: Session, scope: str) -> List['Permission']:
        """
        Get all permissions with a specific scope.
        
        Args:
            session: SQLAlchemy session
            scope: Permission scope
            
        Returns:
            List[Permission]: List of permissions with the scope
        """
        return cls.get_active_query(session).filter(
            cls.scope == scope.lower().strip()
        ).order_by(cls.group, cls.name).all()
    
    @classmethod
    def get_system_permissions(cls, session: Session) -> List['Permission']:
        """
        Get all system permissions.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            List[Permission]: List of system permissions
        """
        return cls.get_active_query(session).filter(
            cls.is_system_permission == "true"
        ).order_by(cls.group, cls.name).all()
    
    @classmethod
    def search_permissions(cls, session: Session, query: str) -> List['Permission']:
        """
        Search permissions by name, description, or group using cognitive patterns.
        
        Args:
            session: SQLAlchemy session
            query: Search query string
            
        Returns:
            List[Permission]: List of matching permissions
        """
        if not query:
            return []
        
        search_term = f"%{query.lower()}%"
        
        return cls.get_active_query(session).filter(
            cls.name.ilike(search_term) |
            cls.description.ilike(search_term) |
            cls.group.ilike(search_term) |
            cls.resource.ilike(search_term)
        ).order_by(cls.name).all()
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert permission to dictionary with cognitive computed fields.
        
        Args:
            include_relationships: Whether to include related objects
            
        Returns:
            Dict[str, Any]: Permission data dictionary
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Add cognitive computed fields
        result['is_system'] = self.is_system
        result['permission_level'] = self.permission_level
        result['scope_description'] = self.get_scope_description()
        
        # Add role information for convenience
        if include_relationships:
            result['role_names'] = [role.name for role in self.roles]
            result['role_count'] = len(self.roles)
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the permission."""
        return f"<Permission(name='{self.name}', group='{self.group}')>"