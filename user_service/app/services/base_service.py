"""
Base Service for User Management Microservice.

This module provides the base service class with common CRUD operations
and utility methods that can be inherited by specific service classes.
"""

from typing import Type, List, Optional, Dict, Any, Union
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Query
from flask import current_app

from app import db
from app.models.base import BaseModel


class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass


class ValidationError(ServiceError):
    """Exception raised for validation errors."""
    pass


class NotFoundError(ServiceError):
    """Exception raised when a resource is not found."""
    pass


class DuplicateError(ServiceError):
    """Exception raised for duplicate resource errors."""
    pass


class BaseService:
    """
    Base service class providing common CRUD operations and utilities.
    
    This class encapsulates common database operations and error handling
    patterns that are used across all service classes in the application.
    
    Attributes:
        model: The SQLAlchemy model class this service operates on
    """
    
    def __init__(self, model: Type[BaseModel]):
        """
        Initialize the base service with a model class.
        
        Args:
            model: SQLAlchemy model class to operate on
        """
        self.model = model
    
    def create(self, data: Dict[str, Any]) -> BaseModel:
        """
        Create a new instance of the model.
        
        Args:
            data: Dictionary containing field values for the new instance
            
        Returns:
            Created model instance
            
        Raises:
            ValidationError: If data validation fails
            DuplicateError: If a unique constraint is violated
            ServiceError: For other database errors
            
        Example:
            >>> user_service = UserService()
            >>> user_data = {'username': 'john', 'email': 'john@example.com'}
            >>> user = user_service.create(user_data)
        """
        try:
            # Create instance from data
            instance = self.model.from_dict(data)
            
            # Validate the instance
            instance.validate()
            
            # Save to database
            instance.save()
            
            current_app.logger.info(
                f"Created {self.model.__name__} with ID: {instance.id}"
            )
            
            return instance
            
        except ValueError as e:
            raise ValidationError(f"Validation error: {str(e)}")
        except IntegrityError as e:
            db.session.rollback()
            raise DuplicateError(f"Resource already exists: {str(e.orig)}")
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Database error: {str(e)}")
    
    def get_by_id(self, instance_id: int) -> Optional[BaseModel]:
        """
        Retrieve an instance by its ID.
        
        Args:
            instance_id: ID of the instance to retrieve
            
        Returns:
            Model instance if found, None otherwise
            
        Example:
            >>> user = user_service.get_by_id(123)
        """
        try:
            return self.model.query.get(instance_id)
        except SQLAlchemyError as e:
            raise ServiceError(f"Database error: {str(e)}")
    
    def get_by_id_or_404(self, instance_id: int) -> BaseModel:
        """
        Retrieve an instance by ID or raise NotFoundError.
        
        Args:
            instance_id: ID of the instance to retrieve
            
        Returns:
            Model instance
            
        Raises:
            NotFoundError: If instance is not found
            
        Example:
            >>> user = user_service.get_by_id_or_404(123)
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            raise NotFoundError(f"{self.model.__name__} with ID {instance_id} not found")
        return instance
    
    def get_all(self, page: int = 1, per_page: int = 20, 
                filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve all instances with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            filters: Dictionary of field-value pairs for filtering
            
        Returns:
            Dictionary containing items, pagination info, and metadata
            
        Example:
            >>> result = user_service.get_all(page=1, per_page=10, 
            ...                               filters={'is_active': True})
            >>> users = result['items']
            >>> total = result['total']
        """
        try:
            query = self.model.query
            
            # Apply filters if provided
            if filters:
                query = self._apply_filters(query, filters)
            
            # Execute paginated query
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return {
                'items': pagination.items,
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
            
        except SQLAlchemyError as e:
            raise ServiceError(f"Database error: {str(e)}")
    
    def update(self, instance_id: int, data: Dict[str, Any]) -> BaseModel:
        """
        Update an existing instance.
        
        Args:
            instance_id: ID of the instance to update
            data: Dictionary containing field values to update
            
        Returns:
            Updated model instance
            
        Raises:
            NotFoundError: If instance is not found
            ValidationError: If data validation fails
            ServiceError: For database errors
            
        Example:
            >>> updated_user = user_service.update(123, {'first_name': 'John'})
        """
        try:
            instance = self.get_by_id_or_404(instance_id)
            
            # Update instance with new data
            instance.update(**data)
            
            # Validate updated instance
            instance.validate()
            
            current_app.logger.info(
                f"Updated {self.model.__name__} with ID: {instance_id}"
            )
            
            return instance
            
        except ValueError as e:
            raise ValidationError(f"Validation error: {str(e)}")
        except IntegrityError as e:
            db.session.rollback()
            raise DuplicateError(f"Update would create duplicate: {str(e.orig)}")
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Database error: {str(e)}")
    
    def delete(self, instance_id: int) -> bool:
        """
        Delete an instance by ID.
        
        Args:
            instance_id: ID of the instance to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            NotFoundError: If instance is not found
            ServiceError: For database errors
            
        Example:
            >>> success = user_service.delete(123)
        """
        try:
            instance = self.get_by_id_or_404(instance_id)
            
            instance.delete()
            
            current_app.logger.info(
                f"Deleted {self.model.__name__} with ID: {instance_id}"
            )
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Database error: {str(e)}")
    
    def exists(self, **filters) -> bool:
        """
        Check if an instance exists with the given filters.
        
        Args:
            **filters: Field-value pairs to filter by
            
        Returns:
            True if at least one instance exists, False otherwise
            
        Example:
            >>> exists = user_service.exists(email='john@example.com')
        """
        try:
            query = self.model.query
            query = self._apply_filters(query, filters)
            return query.first() is not None
        except SQLAlchemyError as e:
            raise ServiceError(f"Database error: {str(e)}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count instances with optional filtering.
        
        Args:
            filters: Dictionary of field-value pairs for filtering
            
        Returns:
            Number of instances matching the criteria
            
        Example:
            >>> active_users = user_service.count({'is_active': True})
        """
        try:
            query = self.model.query
            
            if filters:
                query = self._apply_filters(query, filters)
            
            return query.count()
            
        except SQLAlchemyError as e:
            raise ServiceError(f"Database error: {str(e)}")
    
    def find_by(self, **filters) -> List[BaseModel]:
        """
        Find instances by field values.
        
        Args:
            **filters: Field-value pairs to filter by
            
        Returns:
            List of matching instances
            
        Example:
            >>> active_users = user_service.find_by(is_active=True)
        """
        try:
            query = self.model.query
            query = self._apply_filters(query, filters)
            return query.all()
        except SQLAlchemyError as e:
            raise ServiceError(f"Database error: {str(e)}")
    
    def find_one_by(self, **filters) -> Optional[BaseModel]:
        """
        Find a single instance by field values.
        
        Args:
            **filters: Field-value pairs to filter by
            
        Returns:
            First matching instance or None
            
        Example:
            >>> user = user_service.find_one_by(email='john@example.com')
        """
        try:
            query = self.model.query
            query = self._apply_filters(query, filters)
            return query.first()
        except SQLAlchemyError as e:
            raise ServiceError(f"Database error: {str(e)}")
    
    def _apply_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        """
        Apply filters to a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            filters: Dictionary of field-value pairs
            
        Returns:
            Filtered query object
        """
        for field, value in filters.items():
            if hasattr(self.model, field):
                # Handle different filter types
                if isinstance(value, list):
                    # IN clause for lists
                    query = query.filter(getattr(self.model, field).in_(value))
                elif isinstance(value, dict) and 'like' in value:
                    # LIKE clause for pattern matching
                    query = query.filter(
                        getattr(self.model, field).like(f"%{value['like']}%")
                    )
                else:
                    # Exact match
                    query = query.filter(getattr(self.model, field) == value)
        
        return query
    
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[BaseModel]:
        """
        Create multiple instances in a single transaction.
        
        Args:
            data_list: List of dictionaries containing field values
            
        Returns:
            List of created instances
            
        Raises:
            ValidationError: If any validation fails
            ServiceError: For database errors
            
        Example:
            >>> users_data = [
            ...     {'username': 'user1', 'email': 'user1@example.com'},
            ...     {'username': 'user2', 'email': 'user2@example.com'}
            ... ]
            >>> users = user_service.bulk_create(users_data)
        """
        try:
            instances = []
            
            for data in data_list:
                instance = self.model.from_dict(data)
                instance.validate()
                instances.append(instance)
            
            # Add all instances to session
            db.session.add_all(instances)
            db.session.commit()
            
            current_app.logger.info(
                f"Bulk created {len(instances)} {self.model.__name__} instances"
            )
            
            return instances
            
        except ValueError as e:
            db.session.rollback()
            raise ValidationError(f"Validation error: {str(e)}")
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Database error: {str(e)}")
    
    def soft_delete(self, instance_id: int) -> BaseModel:
        """
        Soft delete an instance by marking it as inactive.
        
        This method assumes the model has an 'is_active' field.
        
        Args:
            instance_id: ID of the instance to soft delete
            
        Returns:
            Updated instance
            
        Raises:
            NotFoundError: If instance is not found
            ServiceError: If model doesn't support soft delete
        """
        if not hasattr(self.model, 'is_active'):
            raise ServiceError(f"{self.model.__name__} does not support soft delete")
        
        return self.update(instance_id, {'is_active': False})