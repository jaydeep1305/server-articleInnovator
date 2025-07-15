"""
Base service module containing common business logic functionality.

This module defines the base service class that provides common
CRUD operations and pagination for all service classes.

Classes:
    BaseService: Abstract base class with common service operations
"""

from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Query
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy import SQLAlchemy

from app.models.base import BaseModel

# Type variable for model classes
ModelType = TypeVar('ModelType', bound=BaseModel)


class PaginationResult:
    """
    Container class for pagination results.
    
    Attributes:
        items: List of items for the current page
        total: Total number of items
        page: Current page number
        per_page: Items per page
        pages: Total number of pages
        has_next: Whether there is a next page
        has_prev: Whether there is a previous page
    """
    
    def __init__(self, items: List[Any], total: int, page: int, per_page: int):
        """
        Initialize pagination result.
        
        Args:
            items: List of items for the current page
            total: Total number of items
            page: Current page number
            per_page: Items per page
        """
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = (total - 1) // per_page + 1 if total > 0 else 0
        self.has_next = page < self.pages
        self.has_prev = page > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert pagination result to dictionary.
        
        Returns:
            Dictionary representation of pagination info
        """
        return {
            'items': [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items],
            'pagination': {
                'total': self.total,
                'page': self.page,
                'per_page': self.per_page,
                'pages': self.pages,
                'has_next': self.has_next,
                'has_prev': self.has_prev
            }
        }


class BaseService(Generic[ModelType]):
    """
    Base service class providing common CRUD operations.
    
    This class implements common business logic operations that are
    inherited by all service classes in the application.
    
    Attributes:
        model: The model class this service operates on
        db: SQLAlchemy database instance
    
    Methods:
        create: Create a new instance
        get_by_id: Get instance by ID
        get_all: Get all instances with optional filtering
        update: Update an existing instance
        delete: Delete an instance
        exists: Check if instance exists
        paginate: Get paginated results
    """
    
    def __init__(self, model: Type[ModelType], db: SQLAlchemy):
        """
        Initialize the base service.
        
        Args:
            model: The model class this service operates on
            db: SQLAlchemy database instance
        """
        self.model = model
        self.db = db
    
    def create(self, **kwargs) -> ModelType:
        """
        Create a new instance of the model.
        
        Args:
            **kwargs: Attributes for the new instance
            
        Returns:
            The created model instance
            
        Raises:
            ValueError: If validation fails
            SQLAlchemyError: If database operation fails
            
        Example:
            user = user_service.create(username='john', email='john@example.com')
        """
        try:
            instance = self.model(**kwargs)
            instance.save()
            return instance
        except ValueError as e:
            raise e
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise e
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get a model instance by its ID.
        
        Args:
            id: The ID of the instance to retrieve
            
        Returns:
            The model instance if found, None otherwise
            
        Example:
            user = user_service.get_by_id(1)
        """
        return self.db.session.get(self.model, id)
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None, 
                order_by: Optional[str] = None) -> List[ModelType]:
        """
        Get all instances with optional filtering and ordering.
        
        Args:
            filters: Dictionary of field-value pairs to filter by
            order_by: Field name to order by (prefix with '-' for descending)
            
        Returns:
            List of model instances
            
        Example:
            users = user_service.get_all(filters={'is_active': True}, order_by='-created_at')
        """
        query = self.db.session.query(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(getattr(self.model, field).desc())
            else:
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))
        
        return query.all()
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Update an existing model instance.
        
        Args:
            id: The ID of the instance to update
            **kwargs: Attributes to update
            
        Returns:
            The updated model instance if found, None otherwise
            
        Raises:
            ValueError: If validation fails
            SQLAlchemyError: If database operation fails
            
        Example:
            user = user_service.update(1, username='new_username')
        """
        instance = self.get_by_id(id)
        if not instance:
            return None
        
        try:
            instance.update(**kwargs)
            return instance
        except ValueError as e:
            raise e
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise e
    
    def delete(self, id: int) -> bool:
        """
        Delete a model instance by ID.
        
        Args:
            id: The ID of the instance to delete
            
        Returns:
            True if deletion was successful, False if instance not found
            
        Raises:
            SQLAlchemyError: If database operation fails
            
        Example:
            success = user_service.delete(1)
        """
        instance = self.get_by_id(id)
        if not instance:
            return False
        
        try:
            instance.delete()
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise e
    
    def exists(self, **kwargs) -> bool:
        """
        Check if an instance exists with the given criteria.
        
        Args:
            **kwargs: Field-value pairs to check
            
        Returns:
            True if an instance exists, False otherwise
            
        Example:
            exists = user_service.exists(username='john_doe')
        """
        query = self.db.session.query(self.model)
        
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        
        return query.first() is not None
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count instances with optional filtering.
        
        Args:
            filters: Dictionary of field-value pairs to filter by
            
        Returns:
            Number of instances matching the criteria
            
        Example:
            active_users = user_service.count(filters={'is_active': True})
        """
        query = self.db.session.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.count()
    
    def paginate(self, page: int = 1, per_page: int = 20, 
                 filters: Optional[Dict[str, Any]] = None,
                 order_by: Optional[str] = None) -> PaginationResult:
        """
        Get paginated results with optional filtering and ordering.
        
        Args:
            page: Page number (starting from 1)
            per_page: Number of items per page
            filters: Dictionary of field-value pairs to filter by
            order_by: Field name to order by (prefix with '-' for descending)
            
        Returns:
            PaginationResult containing items and pagination info
            
        Example:
            result = user_service.paginate(page=1, per_page=10, 
                                         filters={'is_active': True})
        """
        query = self.db.session.query(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(getattr(self.model, field).desc())
            else:
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))
        
        # Calculate pagination
        total = query.count()
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        return PaginationResult(items, total, page, per_page)
    
    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, 
                      **kwargs) -> tuple[ModelType, bool]:
        """
        Get an existing instance or create a new one.
        
        Args:
            defaults: Default values for creation if instance doesn't exist
            **kwargs: Field-value pairs to search for existing instance
            
        Returns:
            Tuple of (instance, created) where created is True if new instance
            
        Example:
            user, created = user_service.get_or_create(
                username='john', defaults={'email': 'john@example.com'}
            )
        """
        query = self.db.session.query(self.model)
        
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        
        instance = query.first()
        
        if instance:
            return instance, False
        else:
            # Merge kwargs and defaults for creation
            create_data = {**kwargs}
            if defaults:
                create_data.update(defaults)
            
            instance = self.create(**create_data)
            return instance, True
    
    def bulk_create(self, instances_data: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple instances in bulk.
        
        Args:
            instances_data: List of dictionaries containing instance data
            
        Returns:
            List of created model instances
            
        Raises:
            SQLAlchemyError: If database operation fails
            
        Example:
            users = user_service.bulk_create([
                {'username': 'user1', 'email': 'user1@example.com'},
                {'username': 'user2', 'email': 'user2@example.com'}
            ])
        """
        instances = []
        
        try:
            for data in instances_data:
                instance = self.model(**data)
                instances.append(instance)
                self.db.session.add(instance)
            
            self.db.session.commit()
            return instances
        except Exception as e:
            self.db.session.rollback()
            raise e