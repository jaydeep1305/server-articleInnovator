"""
Models package initialization.

This module exposes all database models for easy importing throughout the application.
All models inherit from a common base class and follow strict typing conventions.

Author: AI Assistant
Date: 2024
"""

from .base import BaseModel
from .user import User, UserProfile
from .role import Role, Permission, RolePermission
from .invitation import InvitationCode
from .workspace import Workspace, WorkspaceUser

__all__ = [
    'BaseModel',
    'User',
    'UserProfile',
    'Role',
    'Permission',
    'RolePermission',
    'InvitationCode',
    'Workspace',
    'WorkspaceUser'
]