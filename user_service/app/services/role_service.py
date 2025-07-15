"""
Role Service for User Management Microservice.

This module provides role and permission management functionality
for implementing role-based access control (RBAC).
"""

from typing import Optional, Dict, Any, List, Set
from flask import current_app

from app.models.role import Role, Permission
from app.models.user import User
from .base_service import BaseService, ValidationError, NotFoundError, ServiceError


class RoleService(BaseService):
    """
    Service class for comprehensive role management operations.
    
    This service handles role creation, permission assignment,
    hierarchy management, and RBAC operations while maintaining
    security and data integrity.
    
    Features:
    - Role creation and management
    - Permission assignment and removal
    - Role hierarchy management
    - User assignment validation
    - System role protection
    - Role analytics and reporting
    """
    
    def __init__(self):
        """Initialize the role service with the Role model."""
        super().__init__(Role)
    
    def create_role(self, name: str, display_name: str, 
                   description: Optional[str] = None,
                   priority: int = 0,
                   parent_name: Optional[str] = None,
                   max_users: Optional[int] = None,
                   permissions: Optional[List[str]] = None) -> Role:
        """
        Create a new role with optional parent and permissions.
        
        Args:
            name: Unique role name
            display_name: Human-readable role name
            description: Optional role description
            priority: Role priority (0-1000)
            parent_name: Name of parent role for hierarchy
            max_users: Maximum users that can have this role
            permissions: List of permission names to assign
            
        Returns:
            Created role instance
            
        Raises:
            ValidationError: If role data is invalid
            NotFoundError: If parent role is not found
            ServiceError: For other creation errors
            
        Example:
            >>> role = role_service.create_role(
            ...     name='editor',
            ...     display_name='Content Editor',
            ...     description='Can create and edit content',
            ...     priority=50,
            ...     parent_name='user',
            ...     permissions=['content:create', 'content:edit']
            ... )
        """
        # Check if role name already exists
        if self.exists(name=name):
            raise ValidationError(f"Role '{name}' already exists")
        
        # Validate parent role if specified
        parent_role = None
        if parent_name:
            parent_role = self.find_one_by(name=parent_name)
            if not parent_role:
                raise NotFoundError(f"Parent role '{parent_name}' not found")
        
        # Create role data
        role_data = {
            'name': name,
            'display_name': display_name,
            'description': description,
            'priority': priority,
            'max_users': max_users,
            'parent_id': parent_role.id if parent_role else None
        }
        
        # Create role
        role = self.create(role_data)
        
        # Assign permissions if provided
        if permissions:
            self.assign_permissions(role.id, permissions)
        
        current_app.logger.info(f"Role created: {name}")
        
        return role
    
    def assign_permission(self, role_id: int, permission_name: str) -> bool:
        """
        Assign a single permission to a role.
        
        Args:
            role_id: ID of the role
            permission_name: Name of the permission to assign
            
        Returns:
            True if permission was assigned successfully
            
        Raises:
            NotFoundError: If role or permission is not found
            ValidationError: If role is system role or permission already assigned
            
        Example:
            >>> success = role_service.assign_permission(123, 'user:read')
        """
        role = self.get_by_id_or_404(role_id)
        
        if role.is_system:
            raise ValidationError("Cannot modify permissions for system roles")
        
        permission = Permission.query.filter_by(name=permission_name).first()
        if not permission:
            raise NotFoundError(f"Permission '{permission_name}' not found")
        
        if permission in role.permissions:
            raise ValidationError(f"Permission '{permission_name}' already assigned to role")
        
        role.add_permission(permission)
        
        current_app.logger.info(
            f"Permission '{permission_name}' assigned to role '{role.name}'"
        )
        
        return True
    
    def assign_permissions(self, role_id: int, permission_names: List[str]) -> int:
        """
        Assign multiple permissions to a role.
        
        Args:
            role_id: ID of the role
            permission_names: List of permission names to assign
            
        Returns:
            Number of permissions successfully assigned
            
        Raises:
            NotFoundError: If role is not found
            ValidationError: If role is system role
            
        Example:
            >>> assigned = role_service.assign_permissions(
            ...     123, 
            ...     ['user:read', 'user:create', 'user:update']
            ... )
        """
        role = self.get_by_id_or_404(role_id)
        
        if role.is_system:
            raise ValidationError("Cannot modify permissions for system roles")
        
        assigned_count = 0
        
        for permission_name in permission_names:
            try:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission and permission not in role.permissions:
                    role.add_permission(permission)
                    assigned_count += 1
            except Exception as e:
                current_app.logger.warning(
                    f"Failed to assign permission '{permission_name}': {str(e)}"
                )
        
        current_app.logger.info(
            f"Assigned {assigned_count} permissions to role '{role.name}'"
        )
        
        return assigned_count
    
    def remove_permission(self, role_id: int, permission_name: str) -> bool:
        """
        Remove a permission from a role.
        
        Args:
            role_id: ID of the role
            permission_name: Name of the permission to remove
            
        Returns:
            True if permission was removed successfully
            
        Raises:
            NotFoundError: If role or permission is not found
            ValidationError: If role is system role
            
        Example:
            >>> success = role_service.remove_permission(123, 'user:delete')
        """
        role = self.get_by_id_or_404(role_id)
        
        if role.is_system:
            raise ValidationError("Cannot modify permissions for system roles")
        
        permission = Permission.query.filter_by(name=permission_name).first()
        if not permission:
            raise NotFoundError(f"Permission '{permission_name}' not found")
        
        role.remove_permission(permission)
        
        current_app.logger.info(
            f"Permission '{permission_name}' removed from role '{role.name}'"
        )
        
        return True
    
    def get_role_permissions(self, role_id: int, 
                           include_inherited: bool = True) -> List[str]:
        """
        Get all permissions for a role.
        
        Args:
            role_id: ID of the role
            include_inherited: Whether to include inherited permissions
            
        Returns:
            List of permission names
            
        Raises:
            NotFoundError: If role is not found
            
        Example:
            >>> permissions = role_service.get_role_permissions(123)
        """
        role = self.get_by_id_or_404(role_id)
        
        if include_inherited:
            return list(role.get_all_permissions())
        else:
            return [perm.name for perm in role.permissions]
    
    def check_role_permission(self, role_id: int, permission_name: str) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role_id: ID of the role
            permission_name: Permission name to check
            
        Returns:
            True if role has the permission
            
        Raises:
            NotFoundError: If role is not found
        """
        role = self.get_by_id_or_404(role_id)
        return role.has_permission(permission_name)
    
    def get_role_hierarchy(self, role_id: int) -> Dict[str, Any]:
        """
        Get the complete hierarchy for a role.
        
        Args:
            role_id: ID of the role
            
        Returns:
            Dictionary containing hierarchy information
            
        Raises:
            NotFoundError: If role is not found
        """
        role = self.get_by_id_or_404(role_id)
        
        hierarchy_path = role.get_hierarchy_path()
        descendants = role.get_all_descendants()
        
        return {
            'role': role.to_dict(),
            'hierarchy_path': [r.to_dict() for r in hierarchy_path],
            'parent': role.parent.to_dict() if role.parent else None,
            'children': [child.to_dict() for child in role.children],
            'descendants': [desc.to_dict() for desc in descendants],
            'depth': len(hierarchy_path) - 1
        }
    
    def get_assignable_roles(self) -> List[Role]:
        """
        Get all roles that can be assigned to users.
        
        Returns:
            List of assignable roles
        """
        return Role.get_assignable_roles()
    
    def get_system_roles(self) -> List[Role]:
        """
        Get all system roles.
        
        Returns:
            List of system roles
        """
        return Role.get_system_roles()
    
    def deactivate_role(self, role_id: int) -> bool:
        """
        Deactivate a role (prevent new assignments).
        
        Args:
            role_id: ID of the role to deactivate
            
        Returns:
            True if role was deactivated successfully
            
        Raises:
            NotFoundError: If role is not found
            ValidationError: If role is system role
        """
        role = self.get_by_id_or_404(role_id)
        
        if role.is_system:
            raise ValidationError("Cannot deactivate system roles")
        
        role.is_active = False
        role.save()
        
        current_app.logger.info(f"Role deactivated: {role.name}")
        
        return True
    
    def activate_role(self, role_id: int) -> bool:
        """
        Activate a role (allow new assignments).
        
        Args:
            role_id: ID of the role to activate
            
        Returns:
            True if role was activated successfully
            
        Raises:
            NotFoundError: If role is not found
        """
        role = self.get_by_id_or_404(role_id)
        
        role.is_active = True
        role.save()
        
        current_app.logger.info(f"Role activated: {role.name}")
        
        return True
    
    def get_role_users(self, role_id: int, page: int = 1, 
                      per_page: int = 20) -> Dict[str, Any]:
        """
        Get users assigned to a role with pagination.
        
        Args:
            role_id: ID of the role
            page: Page number for pagination
            per_page: Items per page
            
        Returns:
            Dictionary containing users and pagination info
            
        Raises:
            NotFoundError: If role is not found
        """
        role = self.get_by_id_or_404(role_id)
        
        # Query users with this role
        users_query = User.query.join(User.roles).filter(Role.id == role_id)
        
        pagination = users_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'role': role.to_dict(),
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    
    def search_roles(self, query: str, filters: Optional[Dict[str, Any]] = None,
                    page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search roles by name, display name, or description.
        
        Args:
            query: Search query string
            filters: Additional filters to apply
            page: Page number for pagination
            per_page: Items per page
            
        Returns:
            Dictionary containing search results and pagination info
        """
        from sqlalchemy import or_
        
        # Build search query
        search_query = Role.query.filter(
            or_(
                Role.name.ilike(f'%{query}%'),
                Role.display_name.ilike(f'%{query}%'),
                Role.description.ilike(f'%{query}%')
            )
        )
        
        # Apply additional filters
        if filters:
            search_query = self._apply_filters(search_query, filters)
        
        # Execute paginated search
        pagination = search_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'items': [role.to_dict(include_permissions=True) for role in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'query': query
        }
    
    def get_role_statistics(self) -> Dict[str, Any]:
        """
        Get role statistics for admin dashboard.
        
        Returns:
            Dictionary containing various role statistics
        """
        total_roles = self.count()
        active_roles = self.count({'is_active': True})
        system_roles = self.count({'is_system': True})
        custom_roles = self.count({'is_system': False})
        
        # Roles with user limits
        limited_roles = Role.query.filter(
            Role.max_users.isnot(None)
        ).count()
        
        # Most assigned role
        role_usage = {}
        for role in Role.query.all():
            role_usage[role.name] = role.get_user_count()
        
        most_assigned_role = max(role_usage.items(), key=lambda x: x[1]) if role_usage else None
        
        return {
            'total_roles': total_roles,
            'active_roles': active_roles,
            'system_roles': system_roles,
            'custom_roles': custom_roles,
            'limited_roles': limited_roles,
            'most_assigned_role': {
                'name': most_assigned_role[0],
                'user_count': most_assigned_role[1]
            } if most_assigned_role else None,
            'role_usage': role_usage
        }
    
    def validate_role_assignment(self, role_id: int, user_id: int) -> Dict[str, Any]:
        """
        Validate if a role can be assigned to a user.
        
        Args:
            role_id: ID of the role
            user_id: ID of the user
            
        Returns:
            Dictionary containing validation results
            
        Raises:
            NotFoundError: If role or user is not found
        """
        role = self.get_by_id_or_404(role_id)
        user = User.query.get(user_id)
        
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        validation_result = {
            'can_assign': True,
            'reasons': []
        }
        
        # Check if role is active
        if not role.is_active:
            validation_result['can_assign'] = False
            validation_result['reasons'].append("Role is not active")
        
        # Check user limit
        if not role.can_assign_to_user():
            validation_result['can_assign'] = False
            validation_result['reasons'].append(
                f"Role has reached maximum user limit ({role.max_users})"
            )
        
        # Check if user already has role
        if user.has_role(role.name):
            validation_result['can_assign'] = False
            validation_result['reasons'].append("User already has this role")
        
        # Check if user is active
        if not user.is_active:
            validation_result['can_assign'] = False
            validation_result['reasons'].append("User account is not active")
        
        return validation_result