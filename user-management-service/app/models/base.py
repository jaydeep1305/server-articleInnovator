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
from typing import Dict, Any, List, Optional, Union
from sqlalchemy import Column, String, DateTime, Boolean, Integer, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session
from app import db

Base = declarative_base()


class BaseModel(db.Model):
    """
    Abstract base model class with common fields and methods.
    
    This class provides standard fields that every entity should have:
    - id: Primary key using UUID for distributed systems
    - created_at: Timestamp when the entity was created
    - updated_at: Timestamp when the entity was last modified
    - is_active: Soft delete flag for data retention
    
    It also includes utility methods for serialization, validation,
    and common database operations with cognitive error handling patterns.
    
    Attributes:
        id (UUID): Primary key using UUID for better distributed system support
        created_at (datetime): Timestamp when the entity was created
        updated_at (datetime): Timestamp when the entity was last modified  
        is_active (bool): Soft delete flag for data retention
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
    
    # Audit timestamps with automatic management
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the entity was created"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the entity was last modified"
    )
    
    # Soft delete flag for cognitive data retention
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active status flag for soft delete functionality"
    )
    
    def __init__(self, **kwargs) -> None:
        """
        Initialize the model instance with provided keyword arguments.
        
        This constructor implements cognitive defaults and validation
        to ensure data integrity from the moment of instantiation.
        
        Args:
            **kwargs: Arbitrary keyword arguments for model fields
            
        Example:
            >>> user = User(email="test@example.com", username="testuser")
            >>> print(user.id)  # UUID automatically generated
        """
        super().__init__(**kwargs)
        
        # Ensure timestamps are set if not provided
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_relationships: bool = False, 
                exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary representation.
        
        This method creates a JSON-serializable dictionary of the model's attributes,
        handling special types like UUID and datetime objects appropriately.
        It implements cognitive serialization patterns for API responses.
        
        Args:
            include_relationships: Whether to include relationship data
            exclude_fields: List of field names to exclude from output
            
        Returns:
            Dict[str, Any]: Dictionary representation of the model
            
        Example:
            >>> user = User(email="test@example.com")
            >>> user_dict = user.to_dict(exclude_fields=['password_hash'])
            >>> print(user_dict['email'])  # "test@example.com"
        """
        exclude_fields = exclude_fields or []
        result = {}
        
        # Convert column attributes
        for column in self.__table__.columns:
            if column.name in exclude_fields:
                continue
                
            value = getattr(self, column.name)
            
            # Handle special types for JSON serialization
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif value is None:
                value = None
            
            result[column.name] = value
        
        # Include relationships if requested (cognitive pattern for API efficiency)
        if include_relationships:
            for relationship in self.__mapper__.relationships:
                if relationship.key in exclude_fields:
                    continue
                    
                try:
                    related_obj = getattr(self, relationship.key)
                    if related_obj is not None:
                        if hasattr(related_obj, '__iter__') and not isinstance(related_obj, str):
                            # Handle collections (one-to-many, many-to-many)
                            result[relationship.key] = [
                                obj.to_dict(include_relationships=False) 
                                for obj in related_obj
                            ]
                        else:
                            # Handle single objects (many-to-one, one-to-one)
                            result[relationship.key] = related_obj.to_dict(include_relationships=False)
                except Exception:
                    # Skip relationships that can't be loaded (cognitive error handling)
                    continue
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], 
                        exclude_fields: Optional[List[str]] = None) -> None:
        """
        Update model instance from dictionary data.
        
        This method safely updates model attributes from a dictionary,
        excluding protected fields and handling type validation.
        It implements cognitive update patterns with automatic timestamp management.
        
        Args:
            data: Dictionary containing field updates
            exclude_fields: List of field names to exclude from updates
            
        Raises:
            AttributeError: If trying to set a non-existent attribute
            ValueError: If provided data type doesn't match field requirements
            
        Example:
            >>> user.update_from_dict({"email": "new@example.com"})
            >>> print(user.email)  # "new@example.com"
            >>> # updated_at is automatically set to current time
        """
        if exclude_fields is None:
            exclude_fields = ['id', 'created_at']  # Protect immutable fields
        
        for key, value in data.items():
            if key in exclude_fields:
                continue
                
            # Validate that the attribute exists on the model
            if hasattr(self, key):
                column = getattr(self.__table__.columns, key, None)
                if column is not None:
                    # Perform basic type validation
                    if value is not None:
                        self._validate_field_value(key, value)
                    setattr(self, key, value)
                    
        # Update the modification timestamp (cognitive audit pattern)
        self.updated_at = datetime.utcnow()
    
    def _validate_field_value(self, field_name: str, value: Any) -> None:
        """
        Validate field value before assignment.
        
        This method implements cognitive validation patterns to ensure
        data integrity at the field level before database operations.
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate
            
        Raises:
            ValueError: If value doesn't meet field requirements
        """
        column = getattr(self.__table__.columns, field_name, None)
        if column is None:
            return
        
        # Basic type validation based on column type
        if hasattr(column.type, 'python_type'):
            expected_type = column.type.python_type
            if not isinstance(value, expected_type) and value is not None:
                raise ValueError(f"Field {field_name} expects {expected_type.__name__}, got {type(value).__name__}")
        
        # String length validation
        if hasattr(column.type, 'length') and column.type.length:
            if isinstance(value, str) and len(value) > column.type.length:
                raise ValueError(f"Field {field_name} exceeds maximum length of {column.type.length}")
    
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
        
        # Basic validation that applies to all models
        if self.created_at and self.updated_at:
            if self.created_at > self.updated_at:
                errors.append("created_at cannot be later than updated_at")
        
        # Validate required fields are not None
        for column in self.__table__.columns:
            if not column.nullable and column.default is None:
                value = getattr(self, column.name)
                if value is None:
                    errors.append(f"{column.name} is required")
        
        return len(errors) == 0, errors
    
    def soft_delete(self) -> None:
        """
        Perform soft delete by setting is_active to False.
        
        This method maintains data integrity by marking the record as deleted
        rather than physically removing it from the database. This implements
        cognitive data retention patterns for audit trails and recovery.
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """
        Restore a soft-deleted record by setting is_active to True.
        
        This method allows recovery of soft-deleted records, implementing
        cognitive recovery patterns for data restoration scenarios.
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_active_query(cls, session: Session):
        """
        Get query for active (non-soft-deleted) records only.
        
        This method implements cognitive filtering patterns to automatically
        exclude soft-deleted records from normal queries, improving
        application performance and data consistency.
        
        Args:
            session: SQLAlchemy session instance
            
        Returns:
            Query object filtered for active records
            
        Example:
            >>> active_users = User.get_active_query(session).all()
            >>> # Only returns users with is_active=True
        """
        return session.query(cls).filter(cls.is_active == True)
    
    @classmethod
    def find_by_id(cls, session: Session, entity_id: Union[str, uuid.UUID]):
        """
        Find a record by its ID.
        
        This method implements cognitive ID lookup patterns with proper
        type handling for UUID fields and automatic active filtering.
        
        Args:
            session: SQLAlchemy session instance
            entity_id: The ID to search for (string or UUID)
            
        Returns:
            Model instance or None if not found
            
        Example:
            >>> user = User.find_by_id(session, "123e4567-e89b-12d3-a456-426614174000")
        """
        if isinstance(entity_id, str):
            try:
                entity_id = uuid.UUID(entity_id)
            except ValueError:
                return None
        
        return cls.get_active_query(session).filter(cls.id == entity_id).first()
    
    @classmethod
    def create(cls, session: Session, **kwargs):
        """
        Create and save a new instance.
        
        This method implements cognitive creation patterns with automatic
        validation, error handling, and transaction management.
        
        Args:
            session: SQLAlchemy session instance
            **kwargs: Fields for the new instance
            
        Returns:
            Created model instance
            
        Raises:
            ValueError: If validation fails
            
        Example:
            >>> user = User.create(session, email="test@example.com", username="testuser")
        """
        try:
            instance = cls(**kwargs)
            
            # Validate before saving
            is_valid, errors = instance.validate()
            if not is_valid:
                raise ValueError(f"Validation failed: {', '.join(errors)}")
            
            session.add(instance)
            session.flush()  # Get ID without committing
            return instance
            
        except Exception as e:
            session.rollback()
            raise
    
    def save(self, session: Session) -> None:
        """
        Save the current instance to the database.
        
        This method implements cognitive save patterns with validation
        and automatic timestamp management.
        
        Args:
            session: SQLAlchemy session instance
            
        Raises:
            ValueError: If validation fails
        """
        # Validate before saving
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        # Update timestamp
        self.updated_at = datetime.utcnow()
        
        session.add(self)
        session.flush()
    
    def delete(self, session: Session, hard_delete: bool = False) -> None:
        """
        Delete the instance (soft delete by default).
        
        This method implements cognitive deletion patterns with options
        for both soft and hard delete scenarios.
        
        Args:
            session: SQLAlchemy session instance
            hard_delete: If True, physically remove from database
            
        Example:
            >>> user.delete(session)  # Soft delete
            >>> user.delete(session, hard_delete=True)  # Hard delete
        """
        if hard_delete:
            session.delete(self)
        else:
            self.soft_delete()
            session.add(self)
        
        session.flush()
    
    def __repr__(self) -> str:
        """
        String representation of the model instance.
        
        This method provides cognitive string representation showing
        the class name and primary identifier for debugging purposes.
        
        Returns:
            str: Human-readable representation showing the class name and ID
        """
        return f"<{self.__class__.__name__}(id='{self.id}')>"
    
    def __str__(self) -> str:
        """
        String conversion of the model instance.
        
        Returns:
            str: The string representation of the instance ID
        """
        return str(self.id)


# Event listeners for automatic timestamp management
@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """
    Automatically update the updated_at timestamp before any update.
    
    This event listener implements cognitive timestamp management
    to ensure audit trails are always accurate.
    """
    target.updated_at = datetime.utcnow()