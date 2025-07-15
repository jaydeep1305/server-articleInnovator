"""
AIModelService - Business Logic Layer

This module contains business logic for ai-configuration-service operations.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.aimodel import AIModel
from app import db


class AIModelService:
    """Service class for aimodel management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_aimodel(self, name: str, owner_id: uuid.UUID,
                        **kwargs) -> Tuple[Optional[AIModel], bool, List[str]]:
        """Create a new aimodel with validation."""
        try:
            # Create aimodel
            item = AIModel(
                name=name.strip(),
                owner_id=owner_id,
                **kwargs
            )
            
            # Validate
            is_valid, errors = item.validate()
            if not is_valid:
                return None, False, errors
            
            self.session.add(item)
            self.session.commit()
            
            return item, True, []
            
        except IntegrityError:
            self.session.rollback()
            return None, False, ["AIModel with this name already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating aimodel: {str(e)}"]
    
    def get_aimodel_by_id(self, item_id: uuid.UUID) -> Optional[AIModel]:
        """Get aimodel by ID."""
        return AIModel.get_by_id(self.session, item_id)
    
    def get_aimodels_by_owner(self, owner_id: uuid.UUID, limit: int = 20) -> List[AIModel]:
        """Get aimodels by owner."""
        return self.session.query(AIModel).filter(
            AIModel.owner_id == owner_id,
            AIModel.is_deleted == False
        ).order_by(AIModel.created_at.desc()).limit(limit).all()
    
    def update_aimodel(self, item_id: uuid.UUID, updates: Dict[str, Any],
                        updated_by: uuid.UUID) -> Tuple[Optional[AIModel], bool, List[str]]:
        """Update aimodel with validation."""
        try:
            item = self.get_aimodel_by_id(item_id)
            if not item:
                return None, False, ["AIModel not found"]
            
            # Check permissions
            if item.owner_id != updated_by:
                return None, False, ["Insufficient permissions"]
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(item, field) and field not in ['id', 'created_at']:
                    setattr(item, field, value)
            
            item.updated_at = datetime.utcnow()
            
            # Validate
            is_valid, errors = item.validate()
            if not is_valid:
                return None, False, errors
            
            self.session.commit()
            
            return item, True, []
            
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error updating aimodel: {str(e)}"]
    
    def delete_aimodel(self, item_id: uuid.UUID, deleted_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Soft delete aimodel."""
        try:
            item = self.get_aimodel_by_id(item_id)
            if not item:
                return False, ["AIModel not found"]
            
            # Check permissions
            if item.owner_id != deleted_by:
                return False, ["Insufficient permissions"]
            
            item.soft_delete()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error deleting aimodel: {str(e)}"]
