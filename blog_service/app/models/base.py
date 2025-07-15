"""
Base model module containing common database functionality.

This module defines the base model class that provides common
attributes and methods for all database models.

Classes:
    BaseModel: Abstract base class with common database attributes
"""

from datetime import datetime
from typing import Dict, Any, Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# SQLAlchemy instance (will be initialized in the application factory)
db = SQLAlchemy()


class BaseModel(DeclarativeBase):
    """
    Abstract base model class providing common functionality.
    
    This class defines common attributes and methods that are
    inherited by all database models in the application.
    
    Attributes:
        id: Primary key for the model
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    
    Methods:
        save: Save the current instance to the database
        delete: Delete the current instance from the database
        to_dict: Convert the instance to a dictionary
        update: Update the instance with provided data
    """
    
    # Common attributes for all models
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated"
    )
    
    def save(self) -> 'BaseModel':
        """
        Save the current instance to the database.
        
        Returns:
            The saved instance
            
        Raises:
            SQLAlchemyError: If there's an error during database operation
            
        Example:
            user = User(username='john_doe')
            user.save()
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
            SQLAlchemyError: If there's an error during database operation
            
        Example:
            user.delete()
        """
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update(self, **kwargs: Any) -> 'BaseModel':
        """
        Update the instance with provided keyword arguments.
        
        Args:
            **kwargs: Attributes to update
            
        Returns:
            The updated instance
            
        Raises:
            SQLAlchemyError: If there's an error during database operation
            
        Example:
            user.update(username='new_username', email='new@email.com')
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise e
    
    def to_dict(self, exclude: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Convert the instance to a dictionary representation.
        
        Args:
            exclude: List of attributes to exclude from the dictionary
            
        Returns:
            Dictionary representation of the instance
            
        Example:
            user_dict = user.to_dict(exclude=['password_hash'])
        """
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Handle datetime serialization
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
        
        return result
    
    def __repr__(self) -> str:
        """
        String representation of the instance.
        
        Returns:
            String representation including class name and id
        """
        return f"<{self.__class__.__name__}(id={self.id})>"