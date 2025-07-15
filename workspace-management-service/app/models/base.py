"""
Base model for all database models.

This module provides the BaseModel class that includes common fields,
validation methods, and CRUD operations for all models in the service.

Author: AI Assistant
Date: 2024
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

# Create the base class
Base = declarative_base()


class BaseModel(Base, ABC):
    """
    Abstract base model class for all database models.
    
    Provides common fields, validation, and CRUD operations.
    Implements cognitive patterns for data consistency and auditability.
    """
    
    __abstract__ = True
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier"
    )
    
    # Audit timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When record was created"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="When record was last updated"
    )
    
    # Soft delete
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Soft delete flag"
    )
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="When record was deleted"
    )
    
    # Optional metadata
    metadata_json = Column(
        Text,
        nullable=True,
        comment="Additional metadata as JSON"
    )
    
    def __init__(self, **kwargs) -> None:
        """Initialize model with provided attributes."""
        # Set provided attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Set timestamps if not provided
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = datetime.utcnow()
        
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate the model data.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        errors = []
        
        # Validate ID if present
        if self.id is not None and not isinstance(self.id, uuid.UUID):
            errors.append("ID must be a valid UUID")
        
        # Validate timestamps
        if self.created_at and not isinstance(self.created_at, datetime):
            errors.append("created_at must be a datetime")
        
        if self.updated_at and not isinstance(self.updated_at, datetime):
            errors.append("updated_at must be a datetime")
        
        if self.deleted_at and not isinstance(self.deleted_at, datetime):
            errors.append("deleted_at must be a datetime")
        
        # Logical validation
        if (self.created_at and self.updated_at and 
            self.created_at > self.updated_at):
            errors.append("created_at cannot be after updated_at")
        
        if self.is_deleted and not self.deleted_at:
            errors.append("deleted_at must be set when is_deleted is True")
        
        return len(errors) == 0, errors
    
    def soft_delete(self) -> None:
        """Mark the record as deleted without removing it from database."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create(cls, session: Session, **kwargs) -> 'BaseModel':
        """
        Create a new instance and save to database.
        
        Args:
            session: SQLAlchemy session
            **kwargs: Model attributes
            
        Returns:
            Created model instance
            
        Raises:
            ValueError: If validation fails
        """
        instance = cls(**kwargs)
        
        # Validate before saving
        is_valid, errors = instance.validate()
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        session.add(instance)
        session.flush()
        return instance
    
    @classmethod
    def get_by_id(cls, session: Session, record_id: uuid.UUID) -> Optional['BaseModel']:
        """
        Get a record by ID.
        
        Args:
            session: SQLAlchemy session
            record_id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        return session.query(cls).filter(
            cls.id == record_id,
            cls.is_deleted == False
        ).first()
    
    @classmethod
    def get_all(cls, session: Session, include_deleted: bool = False) -> List['BaseModel']:
        """
        Get all records.
        
        Args:
            session: SQLAlchemy session
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            List of model instances
        """
        query = session.query(cls)
        if not include_deleted:
            query = query.filter(cls.is_deleted == False)
        
        return query.all()
    
    @classmethod
    def get_active_query(cls, session: Session):
        """
        Get query for active (non-deleted) records.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            SQLAlchemy query object
        """
        return session.query(cls).filter(cls.is_deleted == False)
    
    def update(self, **kwargs) -> None:
        """
        Update model attributes.
        
        Args:
            **kwargs: Attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def save(self, session: Session) -> None:
        """
        Save the model to database.
        
        Args:
            session: SQLAlchemy session
            
        Raises:
            ValueError: If validation fails
        """
        # Validate before saving
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        self.updated_at = datetime.utcnow()
        session.add(self)
        session.flush()
    
    def delete(self, session: Session, hard_delete: bool = False) -> None:
        """
        Delete the record.
        
        Args:
            session: SQLAlchemy session
            hard_delete: Whether to permanently delete (default: soft delete)
        """
        if hard_delete:
            session.delete(self)
        else:
            self.soft_delete()
        
        session.flush()
    
    def to_dict(self, include_deleted: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Args:
            include_deleted: Whether to include deleted record data
            
        Returns:
            Dict[str, Any]: Model data
        """
        if self.is_deleted and not include_deleted:
            return {}
        
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            # Handle different data types
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        
        return result
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id='{self.id}')>"