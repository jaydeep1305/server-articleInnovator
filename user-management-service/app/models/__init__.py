"""
Models package initialization for User Management Service.

This module exposes all database models with proper imports and initialization.
All models follow SQLAlchemy best practices with type hints and validation.

Author: AI Assistant
Date: 2024
"""

from .base import BaseModel
from .user import User
from .role import Role
from .permission import Permission

__all__ = [
    'BaseModel',
    'User', 
    'Role',
    'Permission'
]