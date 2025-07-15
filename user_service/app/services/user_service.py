"""
User Service for User Management Microservice.

This module provides comprehensive user management functionality including
authentication, authorization, and user lifecycle management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from flask import current_app

from app.models.user import User
from app.models.role import Role
from app.models.profile import Profile
from .base_service import BaseService, ValidationError, NotFoundError, ServiceError


class AuthenticationError(ServiceError):
    """Exception raised for authentication failures."""
    pass


class AuthorizationError(ServiceError):
    """Exception raised for authorization failures."""
    pass


class UserService(BaseService):
    """
    Service class for comprehensive user management operations.
    
    This service handles user creation, authentication, authorization,
    account management, and related business logic while maintaining
    security best practices.
    
    Features:
    - User registration and account creation
    - Authentication with password verification
    - Account security (locking, failed attempts)
    - Role and permission management
    - Profile integration
    - Account status management
    """
    
    def __init__(self):
        """Initialize the user service with the User model."""
        super().__init__(User)
    
    def register_user(self, username: str, email: str, password: str, 
                     first_name: Optional[str] = None,
                     last_name: Optional[str] = None,
                     create_profile: bool = True) -> User:
        """
        Register a new user with comprehensive validation and setup.
        
        Args:
            username: Unique username for the user
            email: Unique email address
            password: Plain text password (will be hashed)
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            create_profile: Whether to create an associated profile
            
        Returns:
            Created user instance with optional profile
            
        Raises:
            ValidationError: If user data is invalid
            DuplicateError: If username or email already exists
            ServiceError: For other registration errors
            
        Example:
            >>> user = user_service.register_user(
            ...     username='johndoe',
            ...     email='john@example.com',
            ...     password='SecurePass123!',
            ...     first_name='John',
            ...     last_name='Doe'
            ... )
        """
        # Check for existing user with same username or email
        if self.exists(username=username):
            raise ValidationError(f"Username '{username}' is already taken")
        
        if self.exists(email=email):
            raise ValidationError(f"Email '{email}' is already registered")
        
        try:
            # Create user data
            user_data = {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
                'is_verified': False  # Require email verification
            }
            
            # Create user instance
            user = self.create(user_data)
            
            # Set password (will be hashed automatically)
            user.password = password
            user.save()
            
            # Assign default role
            self._assign_default_role(user)
            
            # Create profile if requested
            if create_profile:
                self._create_user_profile(user)
            
            current_app.logger.info(f"Successfully registered user: {username}")
            
            return user
            
        except Exception as e:
            current_app.logger.error(f"User registration failed: {str(e)}")
            raise
    
    def authenticate_user(self, identifier: str, password: str) -> User:
        """
        Authenticate a user by username/email and password.
        
        Args:
            identifier: Username or email address
            password: Plain text password
            
        Returns:
            Authenticated user instance
            
        Raises:
            AuthenticationError: If authentication fails
            
        Example:
            >>> user = user_service.authenticate_user('john@example.com', 'password123')
        """
        # Find user by username or email
        user = self.find_one_by(username=identifier) or self.find_one_by(email=identifier)
        
        if not user:
            raise AuthenticationError("Invalid username/email or password")
        
        # Check if account is locked
        if user.is_account_locked():
            raise AuthenticationError(
                f"Account is locked until {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        # Check if account is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        
        # Verify password
        if not user.check_password(password):
            # Increment failed login attempts
            user.increment_failed_login()
            raise AuthenticationError("Invalid username/email or password")
        
        # Successful login - update login info
        user.record_successful_login()
        
        current_app.logger.info(f"User authenticated successfully: {user.username}")
        
        return user
    
    def change_password(self, user_id: int, current_password: str, 
                       new_password: str) -> bool:
        """
        Change a user's password with current password verification.
        
        Args:
            user_id: ID of the user
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password was changed successfully
            
        Raises:
            NotFoundError: If user is not found
            AuthenticationError: If current password is incorrect
            ValidationError: If new password is invalid
            
        Example:
            >>> success = user_service.change_password(
            ...     user_id=123,
            ...     current_password='oldpass',
            ...     new_password='NewSecurePass123!'
            ... )
        """
        user = self.get_by_id_or_404(user_id)
        
        # Verify current password
        if not user.check_password(current_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Set new password (validation happens in the model)
        user.password = new_password
        user.save()
        
        current_app.logger.info(f"Password changed for user: {user.username}")
        
        return True
    
    def reset_password(self, identifier: str) -> str:
        """
        Initiate password reset process for a user.
        
        Args:
            identifier: Username or email address
            
        Returns:
            Reset token (in real implementation, this would be sent via email)
            
        Raises:
            NotFoundError: If user is not found
            
        Note:
            In a production system, this would generate a secure token,
            store it temporarily, and send it via email.
        """
        user = self.find_one_by(username=identifier) or self.find_one_by(email=identifier)
        
        if not user:
            raise NotFoundError("User not found")
        
        # Generate reset token (simplified - use JWT or similar in production)
        import secrets
        reset_token = secrets.token_urlsafe(32)
        
        # In production, store token with expiration and send email
        current_app.logger.info(f"Password reset initiated for user: {user.username}")
        
        return reset_token
    
    def verify_email(self, user_id: int) -> bool:
        """
        Mark a user's email as verified.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if email was verified successfully
            
        Raises:
            NotFoundError: If user is not found
        """
        user = self.get_by_id_or_404(user_id)
        user.is_verified = True
        user.save()
        
        current_app.logger.info(f"Email verified for user: {user.username}")
        
        return True
    
    def deactivate_user(self, user_id: int, reason: Optional[str] = None) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: ID of the user to deactivate
            reason: Optional reason for deactivation
            
        Returns:
            True if user was deactivated successfully
            
        Raises:
            NotFoundError: If user is not found
        """
        user = self.get_by_id_or_404(user_id)
        user.is_active = False
        user.save()
        
        current_app.logger.info(
            f"User deactivated: {user.username}" + 
            (f" (Reason: {reason})" if reason else "")
        )
        
        return True
    
    def reactivate_user(self, user_id: int) -> bool:
        """
        Reactivate a deactivated user account.
        
        Args:
            user_id: ID of the user to reactivate
            
        Returns:
            True if user was reactivated successfully
            
        Raises:
            NotFoundError: If user is not found
        """
        user = self.get_by_id_or_404(user_id)
        user.is_active = True
        user.unlock_account()  # Also unlock if locked
        
        current_app.logger.info(f"User reactivated: {user.username}")
        
        return True
    
    def assign_role(self, user_id: int, role_name: str) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: ID of the user
            role_name: Name of the role to assign
            
        Returns:
            True if role was assigned successfully
            
        Raises:
            NotFoundError: If user or role is not found
            ValidationError: If role cannot be assigned
        """
        user = self.get_by_id_or_404(user_id)
        role = Role.query.filter_by(name=role_name).first()
        
        if not role:
            raise NotFoundError(f"Role '{role_name}' not found")
        
        if not role.can_assign_to_user():
            raise ValidationError(f"Role '{role_name}' cannot be assigned")
        
        user.add_role(role)
        
        current_app.logger.info(
            f"Role '{role_name}' assigned to user: {user.username}"
        )
        
        return True
    
    def remove_role(self, user_id: int, role_name: str) -> bool:
        """
        Remove a role from a user.
        
        Args:
            user_id: ID of the user
            role_name: Name of the role to remove
            
        Returns:
            True if role was removed successfully
            
        Raises:
            NotFoundError: If user or role is not found
        """
        user = self.get_by_id_or_404(user_id)
        role = Role.query.filter_by(name=role_name).first()
        
        if not role:
            raise NotFoundError(f"Role '{role_name}' not found")
        
        user.remove_role(role)
        
        current_app.logger.info(
            f"Role '{role_name}' removed from user: {user.username}"
        )
        
        return True
    
    def check_permission(self, user_id: int, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: ID of the user
            permission: Permission name to check (e.g., 'user:read')
            
        Returns:
            True if user has the permission
            
        Raises:
            NotFoundError: If user is not found
        """
        user = self.get_by_id_or_404(user_id)
        
        # Check all user's roles for the permission
        for role in user.roles:
            if role.has_permission(permission):
                return True
        
        return False
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of permission names
            
        Raises:
            NotFoundError: If user is not found
        """
        user = self.get_by_id_or_404(user_id)
        
        all_permissions = set()
        for role in user.roles:
            all_permissions.update(role.get_all_permissions())
        
        return list(all_permissions)
    
    def search_users(self, query: str, filters: Optional[Dict[str, Any]] = None,
                    page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search users by username, email, or name.
        
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
        search_query = User.query.filter(
            or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%')
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
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics for admin dashboard.
        
        Returns:
            Dictionary containing various user statistics
        """
        total_users = self.count()
        active_users = self.count({'is_active': True})
        verified_users = self.count({'is_verified': True})
        locked_users = User.query.filter(
            User.locked_until > datetime.utcnow()
        ).count()
        
        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = User.query.filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'locked_users': locked_users,
            'recent_registrations': recent_registrations,
            'verification_rate': (verified_users / total_users * 100) if total_users > 0 else 0
        }
    
    def _assign_default_role(self, user: User) -> None:
        """
        Assign the default role to a new user.
        
        Args:
            user: User instance to assign role to
        """
        default_role = Role.query.filter_by(name='user', is_system=True).first()
        if default_role:
            user.add_role(default_role)
    
    def _create_user_profile(self, user: User) -> Profile:
        """
        Create a basic profile for a new user.
        
        Args:
            user: User instance to create profile for
            
        Returns:
            Created profile instance
        """
        from .profile_service import ProfileService
        
        profile_service = ProfileService()
        profile_data = {
            'user_id': user.id,
            'timezone': 'UTC',
            'language_preference': 'en'
        }
        
        return profile_service.create(profile_data)