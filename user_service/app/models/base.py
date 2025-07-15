"""
Base Model for User Management Microservice.

This module provides the base model class with common functionality
such as timestamps, serialization, and validation methods.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr
from app import db


class BaseModel(db.Model):
    """
    Abstract base model class providing common functionality.
    
    This class includes:
    - Primary key auto-generation
    - Created and updated timestamps
    - Common validation methods
    - Serialization methods
    
    All domain models should inherit from this class to ensure
    consistent behavior across the application.
    """
    
    __abstract__ = True
    
    @declared_attr
    def id(cls) -> Column:
        """Primary key column with auto-increment."""
        return Column(Integer, primary_key=True, autoincrement=True)
    
    @declared_attr
    def created_at(cls) -> Column:
        """Timestamp for record creation."""
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls) -> Column:
        """Timestamp for last record update."""
        return Column(
            DateTime, 
            default=datetime.utcnow, 
            onupdate=datetime.utcnow, 
            nullable=False
        )
    
    def save(self) -> 'BaseModel':
        """
        Save the current instance to the database.
        
        Returns:
            The saved instance
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self) -> bool:
        """
        Delete the current instance from the database.
        
        Returns:
            True if deletion was successful
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update(self, **kwargs) -> 'BaseModel':
        """
        Update the current instance with provided keyword arguments.
        
        Args:
            **kwargs: Field-value pairs to update
            
        Returns:
            The updated instance
            
        Raises:
            AttributeError: If trying to update non-existent attribute
            SQLAlchemyError: If database operation fails
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{key}'")
            
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise e
    
    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary representation.
        
        Args:
            exclude_fields: List of field names to exclude from output
            
        Returns:
            Dictionary representation of the model
            
        Example:
            >>> user = User(username='john_doe', email='john@example.com')
            >>> user_dict = user.to_dict(exclude_fields=['password_hash'])
        """
        exclude_fields = exclude_fields or []
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                # Handle datetime serialization
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        Create model instance from dictionary data.
        
        Args:
            data: Dictionary containing field-value pairs
            
        Returns:
            New model instance
            
        Raises:
            ValueError: If required fields are missing or invalid
            
        Example:
            >>> user_data = {'username': 'john_doe', 'email': 'john@example.com'}
            >>> user = User.from_dict(user_data)
        """
        # Filter data to only include valid model attributes
        valid_fields = {column.name for column in cls.__table__.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    def validate(self) -> bool:
        """
        Validate the current model instance.
        
        This method should be overridden in child classes to implement
        specific validation logic.
        
        Returns:
            True if validation passes
            
        Raises:
            ValueError: If validation fails
        """
        return True
    
    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', 'None')})>"