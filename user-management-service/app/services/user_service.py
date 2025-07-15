"""
User service for business logic and CRUD operations.

This module implements the business logic layer for user management operations,
including user creation, authentication, profile management, and role assignments.
It follows DDD patterns with comprehensive validation and cognitive business rules.

Author: AI Assistant
Date: 2024
"""

import logging
import uuid
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func

from app.models import User, Role, Permission
from app import db

logger = logging.getLogger(__name__)


class UserService:
    """
    User service class for business logic and CRUD operations.
    
    This service implements comprehensive user management operations including
    user lifecycle management, authentication support, profile management,
    and role-based access control integration. It follows cognitive business
    patterns with proper validation, error handling, and audit trails.
    
    Responsibilities:
        - User CRUD operations with business validation
        - Profile management and data integrity
        - Role and permission management
        - User authentication support
        - Search and filtering capabilities
        - Bulk operations with transaction safety
        - Audit trail management
    """
    
    def __init__(self, session: Session) -> None:
        """
        Initialize the user service with database session.
        
        Args:
            session: SQLAlchemy database session
            
        Example:
            >>> with db.session() as session:
            ...     user_service = UserService(session)
            ...     user = user_service.create_user(...)
        """
        self.session = session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_user(self, email: str, username: str, password: str, 
                   first_name: Optional[str] = None, last_name: Optional[str] = None,
                   **kwargs) -> Tuple[User, bool]:
        """
        Create a new user with comprehensive validation and business logic.
        
        This method implements cognitive user creation patterns with duplicate
        checking, validation, automatic role assignment, and audit logging.
        
        Args:
            email: User's email address (will be normalized)
            username: User's chosen username (will be normalized)
            password: Plain text password (will be hashed)
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            **kwargs: Additional user attributes
            
        Returns:
            Tuple[User, bool]: (created_user, is_new_user)
            
        Raises:
            ValueError: If validation fails or user already exists
            IntegrityError: If database constraints are violated
            
        Example:
            >>> user, is_new = user_service.create_user(
            ...     email="john@example.com",
            ...     username="johndoe",
            ...     password="SecurePass123!",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )
        """
        try:
            self.logger.info(f"Creating user with email: {email}")
            
            # Check for existing users (cognitive duplicate prevention)
            existing_user = self._check_user_exists(email, username)
            if existing_user:
                if existing_user.email.lower() == email.lower():
                    raise ValueError(f"User with email '{email}' already exists")
                else:
                    raise ValueError(f"User with username '{username}' already exists")
            
            # Prepare user data with cognitive defaults
            user_data = {
                'email': email,
                'username': username,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
                **kwargs
            }
            
            # Create user instance with validation
            user = User(**user_data)
            
            # Add to session and flush to get ID
            self.session.add(user)
            self.session.flush()
            
            # Assign default role (cognitive business rule)
            self._assign_default_role(user)
            
            # Commit transaction
            self.session.commit()
            
            self.logger.info(f"Successfully created user: {user.id}")
            return user, True
            
        except ValueError as e:
            self.session.rollback()
            self.logger.warning(f"User creation validation failed: {e}")
            raise
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"Database integrity error during user creation: {e}")
            raise ValueError("User creation failed due to data constraints")
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Unexpected error during user creation: {e}")
            raise
    
    def get_user_by_id(self, user_id: uuid.UUID, include_roles: bool = False) -> Optional[User]:
        """
        Retrieve a user by their ID with cognitive loading patterns.
        
        Args:
            user_id: UUID of the user to retrieve
            include_roles: Whether to eagerly load user roles
            
        Returns:
            User instance or None if not found
            
        Example:
            >>> user = user_service.get_user_by_id(user_id, include_roles=True)
            >>> if user:
            ...     print(user.roles)
        """
        try:
            query = User.get_active_query(self.session)
            
            if include_roles:
                # Eagerly load roles to avoid N+1 queries (cognitive optimization)
                query = query.options(db.joinedload(User.roles))
            
            return query.filter(User.id == user_id).first()
            
        except Exception as e:
            self.logger.error(f"Error retrieving user {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address with cognitive normalization.
        
        Args:
            email: Email address to search for
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.find_by_email(self.session, email)
        except Exception as e:
            self.logger.error(f"Error retrieving user by email {email}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by their username with cognitive normalization.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.find_by_username(self.session, username)
        except Exception as e:
            self.logger.error(f"Error retrieving user by username {username}: {e}")
            return None
    
    def update_user(self, user_id: uuid.UUID, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user information with comprehensive validation and business logic.
        
        This method implements cognitive update patterns with field validation,
        business rule enforcement, and audit trail management.
        
        Args:
            user_id: UUID of the user to update
            update_data: Dictionary of fields to update
            
        Returns:
            Updated User instance or None if not found
            
        Raises:
            ValueError: If validation fails or update is not allowed
            
        Example:
            >>> user = user_service.update_user(user_id, {
            ...     "first_name": "Jane",
            ...     "phone_number": "+1234567890"
            ... })
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Validate update permissions (cognitive business rule)
            self._validate_update_permissions(user, update_data)
            
            # Special handling for sensitive fields
            if 'email' in update_data:
                new_email = update_data['email']
                if new_email != user.email:
                    # Check for email conflicts
                    existing_user = self.get_user_by_email(new_email)
                    if existing_user and existing_user.id != user.id:
                        raise ValueError(f"Email '{new_email}' is already in use")
                    
                    # Email change requires re-verification (cognitive security pattern)
                    update_data['is_verified'] = False
                    self.logger.info(f"Email changed for user {user_id}, verification reset")
            
            if 'username' in update_data:
                new_username = update_data['username']
                if new_username != user.username:
                    # Check for username conflicts
                    existing_user = self.get_user_by_username(new_username)
                    if existing_user and existing_user.id != user.id:
                        raise ValueError(f"Username '{new_username}' is already in use")
            
            # Update user with validation
            original_data = user.to_dict()
            user.update_from_dict(update_data)
            
            # Validate updated user
            is_valid, errors = user.validate()
            if not is_valid:
                raise ValueError(f"User validation failed: {', '.join(errors)}")
            
            self.session.commit()
            
            # Log significant changes (cognitive audit pattern)
            self._log_user_changes(user, original_data, update_data)
            
            self.logger.info(f"Successfully updated user: {user_id}")
            return user
            
        except ValueError as e:
            self.session.rollback()
            self.logger.warning(f"User update validation failed for {user_id}: {e}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    def change_password(self, user_id: uuid.UUID, old_password: str, 
                       new_password: str) -> bool:
        """
        Change user password with security validation and cognitive patterns.
        
        Args:
            user_id: UUID of the user
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            bool: True if password was changed successfully
            
        Raises:
            ValueError: If current password is incorrect or new password is invalid
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Verify current password (cognitive security pattern)
            if not user.check_password(old_password):
                # Log failed password change attempt
                self.logger.warning(f"Failed password change attempt for user {user_id}")
                user.increment_failed_login()
                self.session.commit()
                raise ValueError("Current password is incorrect")
            
            # Set new password (includes validation)
            user.set_password(new_password)
            
            # Reset failed login attempts on successful password change
            user.reset_failed_login()
            
            self.session.commit()
            
            self.logger.info(f"Password changed successfully for user: {user_id}")
            return True
            
        except ValueError as e:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error changing password for user {user_id}: {e}")
            raise
    
    def delete_user(self, user_id: uuid.UUID, hard_delete: bool = False) -> bool:
        """
        Delete user with cognitive deletion patterns (soft delete by default).
        
        Args:
            user_id: UUID of the user to delete
            hard_delete: Whether to permanently delete (use with caution)
            
        Returns:
            bool: True if user was deleted successfully
            
        Raises:
            ValueError: If user cannot be deleted due to business rules
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Validate deletion permissions (cognitive business rule)
            if user.is_admin and not hard_delete:
                # Check if this is the last admin
                admin_count = self._count_active_admins()
                if admin_count <= 1:
                    raise ValueError("Cannot delete the last admin user")
            
            # Perform deletion
            user.delete(self.session, hard_delete=hard_delete)
            self.session.commit()
            
            deletion_type = "hard" if hard_delete else "soft"
            self.logger.info(f"User {user_id} {deletion_type} deleted successfully")
            return True
            
        except ValueError as e:
            self.session.rollback()
            self.logger.warning(f"User deletion failed for {user_id}: {e}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error deleting user {user_id}: {e}")
            raise
    
    def assign_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        """
        Assign a role to a user with cognitive validation patterns.
        
        Args:
            user_id: UUID of the user
            role_id: UUID of the role to assign
            
        Returns:
            bool: True if role was assigned successfully
            
        Raises:
            ValueError: If assignment is not allowed or role/user not found
        """
        try:
            user = self.get_user_by_id(user_id, include_roles=True)
            if not user:
                raise ValueError("User not found")
            
            role = Role.find_by_id(self.session, role_id)
            if not role:
                raise ValueError("Role not found")
            
            # Validate role assignment (cognitive business rules)
            self._validate_role_assignment(user, role)
            
            user.add_role(self.session, role)
            self.session.commit()
            
            self.logger.info(f"Role '{role.name}' assigned to user {user_id}")
            return True
            
        except ValueError as e:
            self.session.rollback()
            self.logger.warning(f"Role assignment failed: {e}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error assigning role to user {user_id}: {e}")
            raise
    
    def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        """
        Remove a role from a user with cognitive validation patterns.
        
        Args:
            user_id: UUID of the user
            role_id: UUID of the role to remove
            
        Returns:
            bool: True if role was removed successfully
        """
        try:
            user = self.get_user_by_id(user_id, include_roles=True)
            if not user:
                raise ValueError("User not found")
            
            role = Role.find_by_id(self.session, role_id)
            if not role:
                raise ValueError("Role not found")
            
            # Validate role removal (cognitive business rules)
            self._validate_role_removal(user, role)
            
            removed = user.remove_role(self.session, role)
            if removed:
                self.session.commit()
                self.logger.info(f"Role '{role.name}' removed from user {user_id}")
                return True
            else:
                return False
                
        except ValueError as e:
            self.session.rollback()
            self.logger.warning(f"Role removal failed: {e}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error removing role from user {user_id}: {e}")
            raise
    
    def search_users(self, query: str, page: int = 1, per_page: int = 20,
                    include_inactive: bool = False) -> Tuple[List[User], int]:
        """
        Search users with cognitive search patterns and pagination.
        
        Args:
            query: Search query string
            page: Page number (1-based)
            per_page: Number of results per page
            include_inactive: Whether to include soft-deleted users
            
        Returns:
            Tuple[List[User], int]: (users, total_count)
            
        Example:
            >>> users, total = user_service.search_users("john", page=1, per_page=10)
            >>> print(f"Found {total} users, showing {len(users)}")
        """
        try:
            base_query = self.session.query(User)
            
            # Filter active users unless specified otherwise
            if not include_inactive:
                base_query = base_query.filter(User.is_active == True)
            
            # Apply search filters (cognitive search patterns)
            if query:
                search_term = f"%{query.strip().lower()}%"
                base_query = base_query.filter(
                    or_(
                        User.email.ilike(search_term),
                        User.username.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term),
                        func.concat(User.first_name, ' ', User.last_name).ilike(search_term)
                    )
                )
            
            # Get total count
            total_count = base_query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            users = base_query.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()
            
            return users, total_count
            
        except Exception as e:
            self.logger.error(f"Error searching users: {e}")
            return [], 0
    
    def get_users_by_role(self, role_name: str) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            role_name: Name of the role
            
        Returns:
            List[User]: Users with the specified role
        """
        try:
            return (User.get_active_query(self.session)
                   .join(User.roles)
                   .filter(Role.name == role_name.lower())
                   .all())
        except Exception as e:
            self.logger.error(f"Error getting users by role {role_name}: {e}")
            return []
    
    def verify_user_email(self, user_id: uuid.UUID) -> bool:
        """
        Mark user's email as verified with cognitive patterns.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            bool: True if email was verified successfully
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.verify_email()
            self.session.commit()
            
            self.logger.info(f"Email verified for user: {user_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error verifying email for user {user_id}: {e}")
            return False
    
    def get_user_permissions(self, user_id: uuid.UUID) -> Set[str]:
        """
        Get all permissions for a user across all their roles.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Set[str]: Set of permission names
        """
        try:
            user = self.get_user_by_id(user_id, include_roles=True)
            if not user:
                return set()
            
            return user.get_permissions()
            
        except Exception as e:
            self.logger.error(f"Error getting permissions for user {user_id}: {e}")
            return set()
    
    def _check_user_exists(self, email: str, username: str) -> Optional[User]:
        """
        Check if a user with the given email or username already exists.
        
        Args:
            email: Email to check
            username: Username to check
            
        Returns:
            User instance if exists, None otherwise
        """
        existing_by_email = self.get_user_by_email(email)
        if existing_by_email:
            return existing_by_email
        
        existing_by_username = self.get_user_by_username(username)
        if existing_by_username:
            return existing_by_username
        
        return None
    
    def _assign_default_role(self, user: User) -> None:
        """
        Assign default role to a new user (cognitive business pattern).
        
        Args:
            user: User instance to assign role to
        """
        try:
            # Find default user role
            default_role = Role.find_by_name(self.session, 'user')
            if default_role:
                user.add_role(self.session, default_role)
                self.logger.debug(f"Default role 'user' assigned to {user.id}")
            else:
                self.logger.warning("Default 'user' role not found")
        except Exception as e:
            self.logger.error(f"Error assigning default role: {e}")
    
    def _validate_update_permissions(self, user: User, update_data: Dict[str, Any]) -> None:
        """
        Validate that the update is allowed based on business rules.
        
        Args:
            user: User being updated
            update_data: Data being updated
            
        Raises:
            ValueError: If update is not allowed
        """
        # Protect system fields (cognitive security pattern)
        protected_fields = {'id', 'created_at', 'password_hash'}
        for field in protected_fields:
            if field in update_data:
                raise ValueError(f"Field '{field}' cannot be updated directly")
        
        # Additional business rules can be added here
        # For example, preventing email changes for verified admin users
        if 'email' in update_data and user.is_admin and user.is_verified:
            # Require additional verification for admin email changes
            pass  # Could implement additional security checks
    
    def _validate_role_assignment(self, user: User, role: Role) -> None:
        """
        Validate that a role can be assigned to a user.
        
        Args:
            user: User to assign role to
            role: Role to assign
            
        Raises:
            ValueError: If assignment is not allowed
        """
        # Check if role is already assigned
        if role in user.roles:
            raise ValueError(f"Role '{role.name}' is already assigned to user")
        
        # Business rule: prevent multiple admin roles (cognitive security pattern)
        if role.name == 'admin':
            existing_admin_roles = [r for r in user.roles if 'admin' in r.name]
            if existing_admin_roles:
                raise ValueError("User already has admin privileges")
    
    def _validate_role_removal(self, user: User, role: Role) -> None:
        """
        Validate that a role can be removed from a user.
        
        Args:
            user: User to remove role from
            role: Role to remove
            
        Raises:
            ValueError: If removal is not allowed
        """
        # Prevent removing the last admin role (cognitive business rule)
        if role.name == 'admin' and user.is_admin:
            admin_count = self._count_active_admins()
            if admin_count <= 1:
                raise ValueError("Cannot remove admin role from the last admin user")
    
    def _count_active_admins(self) -> int:
        """
        Count the number of active admin users.
        
        Returns:
            int: Number of active admin users
        """
        try:
            return (User.get_active_query(self.session)
                   .filter(User.is_admin == True)
                   .count())
        except Exception as e:
            self.logger.error(f"Error counting admin users: {e}")
            return 0
    
    def _log_user_changes(self, user: User, original_data: Dict[str, Any], 
                         update_data: Dict[str, Any]) -> None:
        """
        Log significant user changes for audit purposes (cognitive audit pattern).
        
        Args:
            user: Updated user
            original_data: Original user data
            update_data: Update data that was applied
        """
        significant_fields = {'email', 'username', 'is_admin', 'is_verified'}
        
        for field in significant_fields:
            if field in update_data:
                old_value = original_data.get(field)
                new_value = getattr(user, field)
                if old_value != new_value:
                    self.logger.info(f"User {user.id} {field} changed from '{old_value}' to '{new_value}'")
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics for administrative dashboards.
        
        Returns:
            Dict[str, Any]: Dictionary containing user statistics
        """
        try:
            stats = {}
            
            # Total users
            stats['total_users'] = User.get_active_query(self.session).count()
            
            # Verified users
            stats['verified_users'] = (User.get_active_query(self.session)
                                     .filter(User.is_verified == True)
                                     .count())
            
            # Admin users
            stats['admin_users'] = (User.get_active_query(self.session)
                                  .filter(User.is_admin == True)
                                  .count())
            
            # Recent registrations (last 30 days)
            thirty_days_ago = datetime.utcnow().replace(day=datetime.utcnow().day-30)
            stats['recent_registrations'] = (User.get_active_query(self.session)
                                            .filter(User.created_at >= thirty_days_ago)
                                            .count())
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating user statistics: {e}")
            return {}