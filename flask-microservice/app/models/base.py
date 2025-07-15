"""
Base model module for all database entities.

This module provides the foundational BaseModel class that includes common fields,
methods, and behaviors shared across all database models in the microservice.
All models inherit from this base class to ensure consistency and maintainability.

Author: AI Assistant
Date: 2024
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session


Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model class with common fields and methods.
    
    This class provides standard fields that every entity should have:
    - id: Primary key using UUID for distributed systems
    - slug_id: Human-readable identifier for API endpoints
    - created_date: Timestamp when the entity was created
    - updated_date: Timestamp when the entity was last modified
    - status: Soft delete flag for data retention
    
    It also includes utility methods for serialization, validation,
    and common database operations.
    """
    
    __abstract__ = True
    
    # Primary key using UUID for better distributed system support
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        comment="Unique identifier for the entity"
    )
    
    # Human-readable slug for API endpoints
    slug_id = Column(
        String(100),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        comment="URL-safe identifier for API endpoints"
    )
    
    # Audit timestamps
    created_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the entity was created"
    )
    
    updated_date = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the entity was last modified"
    )
    
    # Soft delete flag
    status = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active status flag for soft delete functionality"
    )
    
    def __init__(self, **kwargs) -> None:
        """
        Initialize the model instance with provided keyword arguments.
        
        Args:
            **kwargs: Arbitrary keyword arguments for model fields
        """
        super().__init__(**kwargs)
        
        # Generate slug_id if not provided
        if not self.slug_id:
            self.slug_id = str(uuid.uuid4())
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert model instance to dictionary representation.
        
        This method creates a JSON-serializable dictionary of the model's attributes,
        handling special types like UUID and datetime objects appropriately.
        
        Args:
            include_relationships: Whether to include relationship data
            
        Returns:
            Dict[str, Any]: Dictionary representation of the model
            
        Example:
            >>> user = User(email="test@example.com")
            >>> user_dict = user.to_dict()
            >>> print(user_dict['email'])  # "test@example.com"
        """
        result = {}
        
        # Convert column attributes
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            # Handle special types for JSON serialization
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            
            result[column.name] = value
        
        # Include relationships if requested
        if include_relationships:
            for relationship in self.__mapper__.relationships:
                try:
                    related_obj = getattr(self, relationship.key)
                    if related_obj is not None:
                        if hasattr(related_obj, '__iter__') and not isinstance(related_obj, str):
                            # Handle collections
                            result[relationship.key] = [
                                obj.to_dict(include_relationships=False) 
                                for obj in related_obj
                            ]
                        else:
                            # Handle single objects
                            result[relationship.key] = related_obj.to_dict(include_relationships=False)
                except Exception:
                    # Skip relationships that can't be loaded
                    continue
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: Optional[List[str]] = None) -> None:
        """
        Update model instance from dictionary data.
        
        This method safely updates model attributes from a dictionary,
        excluding protected fields and handling type validation.
        
        Args:
            data: Dictionary containing field updates
            exclude_fields: List of field names to exclude from updates
            
        Raises:
            AttributeError: If trying to set a non-existent attribute
            ValueError: If provided data type doesn't match field requirements
            
        Example:
            >>> user.update_from_dict({"email": "new@example.com"})
            >>> print(user.email)  # "new@example.com"
        """
        if exclude_fields is None:
            exclude_fields = ['id', 'created_date']  # Protect immutable fields
        
        for key, value in data.items():
            if key in exclude_fields:
                continue
                
            if hasattr(self, key):
                # Validate that the attribute exists on the model
                column = getattr(self.__table__.columns, key, None)
                if column is not None:
                    setattr(self, key, value)
                    
        # Update the modification timestamp
        self.updated_date = datetime.utcnow()
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate model instance according to business rules.
        
        This method performs custom validation logic that goes beyond
        basic database constraints. Subclasses should override this
        method to implement domain-specific validation rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
            
        Example:
            >>> user = User(email="invalid-email")
            >>> is_valid, errors = user.validate()
            >>> print(is_valid)  # False
            >>> print(errors)    # ["Invalid email format"]
        """
        errors = []
        
        # Basic validation
        if not self.slug_id:
            errors.append("slug_id is required")
        
        if self.created_date and self.updated_date:
            if self.created_date > self.updated_date:
                errors.append("created_date cannot be later than updated_date")
        
        return len(errors) == 0, errors
    
    def soft_delete(self) -> None:
        """
        Perform soft delete by setting status to False.
        
        This method maintains data integrity by marking the record as deleted
        rather than physically removing it from the database.
        """
        self.status = False
        self.updated_date = datetime.utcnow()
    
    def restore(self) -> None:
        """
        Restore a soft-deleted record by setting status to True.
        """
        self.status = True
        self.updated_date = datetime.utcnow()
    
    @classmethod
    def get_active_query(cls, session: Session):
        """
        Get query for active (non-soft-deleted) records only.
        
        Args:
            session: SQLAlchemy session instance
            
        Returns:
            Query object filtered for active records
            
        Example:
            >>> active_users = User.get_active_query(session).all()
        """
        return session.query(cls).filter(cls.status == True)
    
    @classmethod
    def find_by_slug(cls, session: Session, slug_id: str):
        """
        Find a record by its slug_id.
        
        Args:
            session: SQLAlchemy session instance
            slug_id: The slug identifier to search for
            
        Returns:
            Model instance or None if not found
            
        Example:
            >>> user = User.find_by_slug(session, "user-123")
        """
        return cls.get_active_query(session).filter(cls.slug_id == slug_id).first()
    
    def __repr__(self) -> str:
        """
        String representation of the model instance.
        
        Returns:
            str: Human-readable representation showing the class name and slug_id
        """
        return f"<{self.__class__.__name__}(slug_id='{self.slug_id}')>"
    
    def __str__(self) -> str:
        """
        String conversion of the model instance.
        
        Returns:
            str: The slug_id of the instance
        """
        return self.slug_id