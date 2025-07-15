"""
Permission Service for User Management Microservice.

This module provides permission management functionality for
fine-grained access control in the RBAC system.
"""

from typing import Optional, Dict, Any, List
from flask import current_app

from app.models.role import Permission, Role
from .base_service import BaseService, ValidationError, NotFoundError, ServiceError


class PermissionService(BaseService):
    """
    Service class for comprehensive permission management operations.
    
    This service handles permission creation, management, and analysis
    for implementing fine-grained access control in the RBAC system.
    
    Features:
    - Permission creation and management
    - Resource-action pattern enforcement
    - System permission protection
    - Permission usage analysis
    - Bulk operations
    """
    
    def __init__(self):
        """Initialize the permission service with the Permission model."""
        super().__init__(Permission)
    
    def create_permission(self, name: str, resource: str, action: str,
                         description: Optional[str] = None,
                         is_system: bool = False) -> Permission:
        """
        Create a new permission with validation.
        
        Args:
            name: Unique permission name (resource:action format)
            resource: Resource type the permission applies to
            action: Action the permission allows
            description: Optional description of the permission
            is_system: Whether this is a system permission
            
        Returns:
            Created permission instance
            
        Raises:
            ValidationError: If permission data is invalid
            ServiceError: For other creation errors
            
        Example:
            >>> permission = permission_service.create_permission(
            ...     name='user:create',
            ...     resource='user',
            ...     action='create',
            ...     description='Allow creating new users'
            ... )
        """
        # Check if permission already exists
        if self.exists(name=name):
            raise ValidationError(f"Permission '{name}' already exists")
        
        # Validate name format matches resource:action
        expected_name = f"{resource}:{action}"
        if name != expected_name:
            raise ValidationError(
                f"Permission name '{name}' does not match resource:action format '{expected_name}'"
            )
        
        permission_data = {
            'name': name,
            'resource': resource,
            'action': action,
            'description': description,
            'is_system': is_system
        }
        
        permission = self.create(permission_data)
        
        current_app.logger.info(f"Permission created: {name}")
        
        return permission
    
    def create_permissions_bulk(self, permissions_data: List[Dict[str, Any]]) -> List[Permission]:
        """
        Create multiple permissions in a single transaction.
        
        Args:
            permissions_data: List of permission dictionaries
            
        Returns:
            List of created permission instances
            
        Raises:
            ValidationError: If any permission data is invalid
            ServiceError: For database errors
            
        Example:
            >>> permissions = [
            ...     {'name': 'user:read', 'resource': 'user', 'action': 'read'},
            ...     {'name': 'user:create', 'resource': 'user', 'action': 'create'},
            ...     {'name': 'user:update', 'resource': 'user', 'action': 'update'}
            ... ]
            >>> created = permission_service.create_permissions_bulk(permissions)
        """
        # Validate all permissions first
        for perm_data in permissions_data:
            name = perm_data.get('name')
            resource = perm_data.get('resource')
            action = perm_data.get('action')
            
            if not name or not resource or not action:
                raise ValidationError("Name, resource, and action are required for all permissions")
            
            expected_name = f"{resource}:{action}"
            if name != expected_name:
                raise ValidationError(
                    f"Permission name '{name}' does not match resource:action format '{expected_name}'"
                )
            
            if self.exists(name=name):
                raise ValidationError(f"Permission '{name}' already exists")
        
        permissions = self.bulk_create(permissions_data)
        
        current_app.logger.info(f"Bulk created {len(permissions)} permissions")
        
        return permissions
    
    def get_permissions_by_resource(self, resource: str) -> List[Permission]:
        """
        Get all permissions for a specific resource.
        
        Args:
            resource: Resource name to filter by
            
        Returns:
            List of permissions for the resource
            
        Example:
            >>> user_permissions = permission_service.get_permissions_by_resource('user')
        """
        return self.find_by(resource=resource)
    
    def get_permissions_by_action(self, action: str) -> List[Permission]:
        """
        Get all permissions for a specific action.
        
        Args:
            action: Action name to filter by
            
        Returns:
            List of permissions for the action
            
        Example:
            >>> read_permissions = permission_service.get_permissions_by_action('read')
        """
        return self.find_by(action=action)
    
    def get_system_permissions(self) -> List[Permission]:
        """
        Get all system permissions.
        
        Returns:
            List of system permissions
        """
        return self.find_by(is_system=True)
    
    def get_custom_permissions(self) -> List[Permission]:
        """
        Get all custom (non-system) permissions.
        
        Returns:
            List of custom permissions
        """
        return self.find_by(is_system=False)
    
    def delete_permission(self, permission_id: int) -> bool:
        """
        Delete a permission if it's not a system permission and not in use.
        
        Args:
            permission_id: ID of the permission to delete
            
        Returns:
            True if permission was deleted successfully
            
        Raises:
            NotFoundError: If permission is not found
            ValidationError: If permission is system permission or in use
            
        Example:
            >>> success = permission_service.delete_permission(123)
        """
        permission = self.get_by_id_or_404(permission_id)
        
        if permission.is_system:
            raise ValidationError("Cannot delete system permissions")
        
        # Check if permission is assigned to any roles
        if permission.roles:
            role_names = [role.name for role in permission.roles]
            raise ValidationError(
                f"Cannot delete permission '{permission.name}' - it is assigned to roles: {', '.join(role_names)}"
            )
        
        self.delete(permission_id)
        
        current_app.logger.info(f"Permission deleted: {permission.name}")
        
        return True
    
    def get_permission_usage(self, permission_id: int) -> Dict[str, Any]:
        """
        Get usage information for a permission.
        
        Args:
            permission_id: ID of the permission
            
        Returns:
            Dictionary containing usage information
            
        Raises:
            NotFoundError: If permission is not found
            
        Example:
            >>> usage = permission_service.get_permission_usage(123)
            >>> print(f"Used by {usage['role_count']} roles")
        """
        permission = self.get_by_id_or_404(permission_id)
        
        roles_with_permission = permission.roles
        role_details = []
        
        for role in roles_with_permission:
            role_details.append({
                'id': role.id,
                'name': role.name,
                'display_name': role.display_name,
                'user_count': role.get_user_count(),
                'is_active': role.is_active
            })
        
        # Calculate total users affected
        total_users_affected = sum(role['user_count'] for role in role_details)
        
        return {
            'permission': permission.to_dict(),
            'role_count': len(roles_with_permission),
            'roles': role_details,
            'total_users_affected': total_users_affected,
            'is_in_use': len(roles_with_permission) > 0
        }
    
    def search_permissions(self, query: str, filters: Optional[Dict[str, Any]] = None,
                          page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search permissions by name, resource, action, or description.
        
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
        search_query = Permission.query.filter(
            or_(
                Permission.name.ilike(f'%{query}%'),
                Permission.resource.ilike(f'%{query}%'),
                Permission.action.ilike(f'%{query}%'),
                Permission.description.ilike(f'%{query}%')
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
            'items': pagination.items,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'query': query
        }
    
    def get_permissions_by_pattern(self, resource_pattern: Optional[str] = None,
                                  action_pattern: Optional[str] = None) -> List[Permission]:
        """
        Get permissions matching resource and/or action patterns.
        
        Args:
            resource_pattern: Resource pattern to match (supports wildcards)
            action_pattern: Action pattern to match (supports wildcards)
            
        Returns:
            List of matching permissions
            
        Example:
            >>> user_read_perms = permission_service.get_permissions_by_pattern(
            ...     resource_pattern='user%',
            ...     action_pattern='read'
            ... )
        """
        query = Permission.query
        
        if resource_pattern:
            query = query.filter(Permission.resource.like(resource_pattern))
        
        if action_pattern:
            query = query.filter(Permission.action.like(action_pattern))
        
        return query.all()
    
    def get_unused_permissions(self) -> List[Permission]:
        """
        Get permissions that are not assigned to any roles.
        
        Returns:
            List of unused permissions
        """
        return Permission.query.filter(~Permission.roles.any()).all()
    
    def get_permission_statistics(self) -> Dict[str, Any]:
        """
        Get permission statistics for admin dashboard.
        
        Returns:
            Dictionary containing various permission statistics
        """
        total_permissions = self.count()
        system_permissions = self.count({'is_system': True})
        custom_permissions = self.count({'is_system': False})
        
        # Unused permissions
        unused_permissions = len(self.get_unused_permissions())
        
        # Permissions by resource
        resource_stats = {}
        for permission in Permission.query.all():
            resource = permission.resource
            if resource not in resource_stats:
                resource_stats[resource] = {
                    'count': 0,
                    'used': 0,
                    'system': 0
                }
            resource_stats[resource]['count'] += 1
            if permission.roles:
                resource_stats[resource]['used'] += 1
            if permission.is_system:
                resource_stats[resource]['system'] += 1
        
        # Most used permission
        permission_usage = {}
        for permission in Permission.query.all():
            permission_usage[permission.name] = len(permission.roles)
        
        most_used_permission = max(
            permission_usage.items(), 
            key=lambda x: x[1]
        ) if permission_usage else None
        
        return {
            'total_permissions': total_permissions,
            'system_permissions': system_permissions,
            'custom_permissions': custom_permissions,
            'unused_permissions': unused_permissions,
            'usage_rate': ((total_permissions - unused_permissions) / total_permissions * 100) if total_permissions > 0 else 0,
            'resource_statistics': resource_stats,
            'most_used_permission': {
                'name': most_used_permission[0],
                'role_count': most_used_permission[1]
            } if most_used_permission else None
        }
    
    def validate_permission_name(self, name: str) -> Dict[str, Any]:
        """
        Validate a permission name format.
        
        Args:
            name: Permission name to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'parsed': None
        }
        
        # Check basic format
        if ':' not in name:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Permission name must contain ':' separator")
            return validation_result
        
        parts = name.split(':')
        if len(parts) != 2:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Permission name must have exactly one ':' separator")
            return validation_result
        
        resource, action = parts
        
        # Validate resource and action parts
        if not resource or not resource.strip():
            validation_result['is_valid'] = False
            validation_result['errors'].append("Resource part cannot be empty")
        
        if not action or not action.strip():
            validation_result['is_valid'] = False
            validation_result['errors'].append("Action part cannot be empty")
        
        # Check if name already exists
        if self.exists(name=name):
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Permission '{name}' already exists")
        
        if validation_result['is_valid']:
            validation_result['parsed'] = {
                'resource': resource.strip(),
                'action': action.strip()
            }
        
        return validation_result