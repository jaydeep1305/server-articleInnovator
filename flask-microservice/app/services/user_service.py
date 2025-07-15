"""
User service module for user management and authentication business logic.

This module provides service classes that handle complex user operations,
authentication, authorization, and user profile management. The services
implement business rules and act as a bridge between the API layer and data models.

Author: AI Assistant
Date: 2024
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models import User, UserProfile, Role, Permission, InvitationCode
from ..models.workspace import WorkspaceUser, WorkspaceRole
from .event_service import EventService, EventType


class UserService:
    """
    Service class for user management operations.
    
    This service handles all user-related business logic including user creation,
    profile management, user queries, and user lifecycle operations. It implements
    domain-specific validation and business rules.
    """
    
    def __init__(self, session: Session, event_service: Optional[EventService] = None):
        """
        Initialize the user service.
        
        Args:
            session: SQLAlchemy database session
            event_service: Optional event service for publishing events
        """
        self.session = session
        self.event_service = event_service or EventService()
    
    def create_user(self, email: str, username: str, password: str, 
                   invitation_code: Optional[str] = None, **profile_data) -> Tuple[User, UserProfile]:
        """
        Create a new user with profile and handle invitation code redemption.
        
        This method implements the complete user registration workflow including
        invitation code validation, user creation, profile setup, and event publishing.
        
        Args:
            email: User's email address
            username: User's chosen username
            password: User's password (will be hashed)
            invitation_code: Optional invitation code for registration
            **profile_data: Additional profile information
            
        Returns:
            Tuple[User, UserProfile]: Created user and profile instances
            
        Raises:
            ValueError: If user data is invalid or invitation code is invalid
            IntegrityError: If email or username already exists
            
        Example:
            >>> user, profile = user_service.create_user(
            ...     email="user@example.com",
            ...     username="newuser",
            ...     password="SecurePass123",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )
        """
        try:
            # Validate invitation code if provided
            invitation = None
            if invitation_code:
                invitation = self._validate_and_get_invitation(invitation_code)
            
            # Create user instance
            user = User(
                email=email,
                username=username,
                password=password,
                first_name=profile_data.get('first_name'),
                last_name=profile_data.get('last_name')
            )
            
            self.session.add(user)
            self.session.flush()  # Get user ID without committing
            
            # Create user profile
            profile = UserProfile(
                user_id=user.id,
                bio=profile_data.get('bio'),
                phone_number=profile_data.get('phone_number'),
                birth_date=profile_data.get('birth_date'),
                timezone=profile_data.get('timezone', 'UTC'),
                language=profile_data.get('language', 'en'),
                receive_notifications=profile_data.get('receive_notifications', True)
            )
            
            self.session.add(profile)
            
            # Handle invitation code if provided
            if invitation:
                invitation.use_invitation(str(user.id))
                
                # Create workspace user relationship if invitation has workspace limitation
                if invitation.workspace_limitation > 0:
                    self._create_default_workspace(user, invitation)
            
            # Assign default role
            self._assign_default_role(user)
            
            self.session.commit()
            
            # Publish user created event
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.USER_CREATED,
                    entity_id=str(user.id),
                    entity_type='user',
                    data={
                        'email': user.email,
                        'username': user.username,
                        'invitation_code': invitation_code
                    }
                )
            
            return user, profile
            
        except IntegrityError as e:
            self.session.rollback()
            if 'email' in str(e):
                raise ValueError("Email address already exists")
            elif 'username' in str(e):
                raise ValueError("Username already exists")
            else:
                raise ValueError("User creation failed due to data conflict")
        except Exception as e:
            self.session.rollback()
            raise
    
    def get_user_by_id(self, user_id: str, include_profile: bool = True) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: User's unique identifier
            include_profile: Whether to load the user's profile
            
        Returns:
            User instance or None if not found
        """
        user = User.get_active_query(self.session).filter(User.id == user_id).first()
        
        if user and include_profile:
            # Eager load profile to avoid lazy loading issues
            _ = user.profile
        
        return user
    
    def get_user_by_email(self, email: str, include_profile: bool = True) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: User's email address
            include_profile: Whether to load the user's profile
            
        Returns:
            User instance or None if not found
        """
        user = User.find_by_email(self.session, email)
        
        if user and include_profile:
            _ = user.profile
        
        return user
    
    def get_user_by_username(self, username: str, include_profile: bool = True) -> Optional[User]:
        """
        Retrieve a user by their username.
        
        Args:
            username: User's username
            include_profile: Whether to load the user's profile
            
        Returns:
            User instance or None if not found
        """
        user = User.find_by_username(self.session, username)
        
        if user and include_profile:
            _ = user.profile
        
        return user
    
    def update_user(self, user_id: str, user_data: Dict[str, Any], 
                   profile_data: Optional[Dict[str, Any]] = None) -> User:
        """
        Update user information and profile.
        
        Args:
            user_id: User's unique identifier
            user_data: Dictionary of user fields to update
            profile_data: Optional dictionary of profile fields to update
            
        Returns:
            Updated user instance
            
        Raises:
            ValueError: If user not found or update data is invalid
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        try:
            # Update user fields
            if user_data:
                user.update_from_dict(user_data, exclude_fields=['id', 'email', 'password_hash'])
            
            # Update profile fields
            if profile_data and user.profile:
                user.profile.update_from_dict(profile_data, exclude_fields=['id', 'user_id'])
            
            # Validate changes
            is_valid, errors = user.validate()
            if not is_valid:
                raise ValueError(f"User validation failed: {', '.join(errors)}")
            
            if user.profile:
                is_valid, errors = user.profile.validate()
                if not is_valid:
                    raise ValueError(f"Profile validation failed: {', '.join(errors)}")
            
            self.session.commit()
            
            # Publish user updated event
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.USER_UPDATED,
                    entity_id=str(user.id),
                    entity_type='user',
                    data={'updated_fields': list(user_data.keys()) + list(profile_data.keys() if profile_data else [])}
                )
            
            return user
            
        except Exception as e:
            self.session.rollback()
            raise
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change a user's password with current password verification.
        
        Args:
            user_id: User's unique identifier
            current_password: User's current password
            new_password: New password to set
            
        Returns:
            bool: True if password was changed successfully
            
        Raises:
            ValueError: If user not found or current password is incorrect
        """
        user = self.get_user_by_id(user_id, include_profile=False)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not user.check_password(current_password):
            raise ValueError("Current password is incorrect")
        
        try:
            # Set new password
            user.set_password(new_password)
            self.session.commit()
            
            # Publish password changed event
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.USER_PASSWORD_CHANGED,
                    entity_id=str(user.id),
                    entity_type='user',
                    data={'changed_at': datetime.utcnow().isoformat()}
                )
            
            return True
            
        except Exception as e:
            self.session.rollback()
            raise
    
    def deactivate_user(self, user_id: str, reason: Optional[str] = None) -> bool:
        """
        Deactivate a user account (soft delete).
        
        Args:
            user_id: User's unique identifier
            reason: Optional reason for deactivation
            
        Returns:
            bool: True if user was deactivated
            
        Raises:
            ValueError: If user not found
        """
        user = self.get_user_by_id(user_id, include_profile=False)
        if not user:
            raise ValueError("User not found")
        
        try:
            user.is_active = False
            user.soft_delete()
            
            # Also deactivate profile
            if user.profile:
                user.profile.soft_delete()
            
            self.session.commit()
            
            # Publish user deactivated event
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.USER_DEACTIVATED,
                    entity_id=str(user.id),
                    entity_type='user',
                    data={'reason': reason, 'deactivated_at': datetime.utcnow().isoformat()}
                )
            
            return True
            
        except Exception as e:
            self.session.rollback()
            raise
    
    def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all workspaces where a user is a member.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of workspace dictionaries with user's role information
        """
        workspace_users = self.session.query(WorkspaceUser).filter(
            WorkspaceUser.user_id == user_id,
            WorkspaceUser.status == True
        ).all()
        
        workspaces = []
        for workspace_user in workspace_users:
            workspace_data = workspace_user.workspace.to_dict()
            workspace_data['user_role'] = workspace_user.role
            workspace_data['joined_date'] = workspace_user.created_date.isoformat()
            workspaces.append(workspace_data)
        
        return workspaces
    
    def _validate_and_get_invitation(self, invitation_code: str) -> InvitationCode:
        """
        Validate and retrieve invitation code.
        
        Args:
            invitation_code: Invitation code to validate
            
        Returns:
            InvitationCode instance
            
        Raises:
            ValueError: If invitation code is invalid
        """
        invitation = InvitationCode.find_by_code(self.session, invitation_code)
        if not invitation:
            raise ValueError("Invalid invitation code")
        
        is_valid, reason = invitation.is_valid_for_use()
        if not is_valid:
            raise ValueError(f"Invitation code cannot be used: {reason}")
        
        return invitation
    
    def _assign_default_role(self, user: User) -> None:
        """
        Assign default role to a new user.
        
        Args:
            user: User instance to assign role to
        """
        # This would typically assign a default "user" role
        # Implementation depends on your role management system
        pass
    
    def _create_default_workspace(self, user: User, invitation: InvitationCode) -> None:
        """
        Create default workspace for user based on invitation.
        
        Args:
            user: User instance
            invitation: Invitation code with workspace settings
        """
        # This would create a default workspace for the user
        # Implementation depends on your workspace management requirements
        pass


class AuthenticationService:
    """
    Service class for user authentication and session management.
    
    This service handles user authentication, JWT token generation and validation,
    session management, and security-related operations.
    """
    
    def __init__(self, session: Session, jwt_secret: str, jwt_expiry_hours: int = 24,
                 event_service: Optional[EventService] = None):
        """
        Initialize the authentication service.
        
        Args:
            session: SQLAlchemy database session
            jwt_secret: Secret key for JWT token signing
            jwt_expiry_hours: JWT token expiry time in hours
            event_service: Optional event service for publishing events
        """
        self.session = session
        self.jwt_secret = jwt_secret
        self.jwt_expiry_hours = jwt_expiry_hours
        self.event_service = event_service or EventService()
    
    def authenticate_user(self, email_or_username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate user with email/username and password.
        
        This method handles the complete authentication workflow including
        account lockout protection, failed attempt tracking, and token generation.
        
        Args:
            email_or_username: User's email address or username
            password: User's password
            
        Returns:
            Tuple[User, token]: User instance and JWT token if successful, (None, None) if failed
            
        Raises:
            ValueError: If account is locked or authentication fails
            
        Example:
            >>> user, token = auth_service.authenticate_user("user@example.com", "password")
            >>> if user:
            ...     print(f"Welcome {user.full_name}")
        """
        # Find user by email or username
        user = self._find_user_by_identifier(email_or_username)
        
        if not user:
            # Log failed attempt for non-existent user
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.LOGIN_FAILED,
                    entity_id='unknown',
                    entity_type='user',
                    data={'identifier': email_or_username, 'reason': 'user_not_found'}
                )
            return None, None
        
        # Check if account is locked
        if user.is_account_locked():
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.LOGIN_FAILED,
                    entity_id=str(user.id),
                    entity_type='user',
                    data={'identifier': email_or_username, 'reason': 'account_locked'}
                )
            raise ValueError("Account is temporarily locked due to too many failed login attempts")
        
        # Check if account is active
        if not user.is_active:
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.LOGIN_FAILED,
                    entity_id=str(user.id),
                    entity_type='user',
                    data={'identifier': email_or_username, 'reason': 'account_inactive'}
                )
            raise ValueError("Account is not active")
        
        # Verify password
        if not user.check_password(password):
            # Increment failed login attempts
            user.increment_failed_login()
            self.session.commit()
            
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.LOGIN_FAILED,
                    entity_id=str(user.id),
                    entity_type='user',
                    data={'identifier': email_or_username, 'reason': 'invalid_password'}
                )
            
            return None, None
        
        # Successful authentication
        try:
            # Reset failed login attempts
            user.reset_failed_login()
            
            # Generate JWT token
            token = self.generate_jwt_token(user)
            
            self.session.commit()
            
            # Publish successful login event
            if self.event_service:
                self.event_service.publish_event(
                    event_type=EventType.USER_LOGIN,
                    entity_id=str(user.id),
                    entity_type='user',
                    data={'identifier': email_or_username, 'login_time': datetime.utcnow().isoformat()}
                )
            
            return user, token
            
        except Exception as e:
            self.session.rollback()
            raise
    
    def generate_jwt_token(self, user: User) -> str:
        """
        Generate JWT token for authenticated user.
        
        Args:
            user: Authenticated user instance
            
        Returns:
            str: JWT token string
        """
        now = datetime.utcnow()
        payload = {
            'user_id': str(user.id),
            'email': user.email,
            'username': user.username,
            'iat': now,
            'exp': now + timedelta(hours=self.jwt_expiry_hours),
            'iss': 'flask-microservice'
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Dict containing token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Additional validation if needed
            user = User.get_active_query(self.session).filter(
                User.id == payload['user_id']
            ).first()
            
            if not user or not user.is_active:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def logout_user(self, user_id: str) -> bool:
        """
        Handle user logout (for event tracking).
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            bool: True if logout was recorded
        """
        if self.event_service:
            self.event_service.publish_event(
                event_type=EventType.USER_LOGOUT,
                entity_id=user_id,
                entity_type='user',
                data={'logout_time': datetime.utcnow().isoformat()}
            )
        
        return True
    
    def refresh_token(self, current_token: str) -> Optional[str]:
        """
        Refresh an existing JWT token.
        
        Args:
            current_token: Current JWT token
            
        Returns:
            str: New JWT token if successful, None if failed
        """
        payload = self.validate_jwt_token(current_token)
        if not payload:
            return None
        
        user = User.get_active_query(self.session).filter(
            User.id == payload['user_id']
        ).first()
        
        if not user:
            return None
        
        return self.generate_jwt_token(user)
    
    def _find_user_by_identifier(self, identifier: str) -> Optional[User]:
        """
        Find user by email or username.
        
        Args:
            identifier: Email address or username
            
        Returns:
            User instance or None if not found
        """
        identifier = identifier.lower().strip()
        
        # Try email first
        if '@' in identifier:
            return User.find_by_email(self.session, identifier)
        else:
            return User.find_by_username(self.session, identifier)