"""
Services package initialization.

This module exposes all service classes that contain business logic for the microservice.
Services act as an intermediary layer between routes and models, implementing
domain-specific business rules and complex operations.

Author: AI Assistant
Date: 2024
"""

from .user_service import UserService, AuthenticationService
from .role_service import RoleService, PermissionService
from .invitation_service import InvitationService
from .workspace_service import WorkspaceService
from .event_service import EventService

__all__ = [
    'UserService',
    'AuthenticationService',
    'RoleService',
    'PermissionService',
    'InvitationService',
    'WorkspaceService',
    'EventService'
]