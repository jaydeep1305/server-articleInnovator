"""
ServiceHealthService - Business Logic Layer

This module contains business logic for monitoring-service operations.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.servicehealth import ServiceHealth
from app import db


class ServiceHealthService:
    """Service class for servicehealth management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_servicehealth(self, name: str, owner_id: uuid.UUID,
                        **kwargs) -> Tuple[Optional[ServiceHealth], bool, List[str]]:
        """Create a new servicehealth with validation."""
        try:
            # Create servicehealth
            item = ServiceHealth(
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
            return None, False, ["ServiceHealth with this name already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating servicehealth: {str(e)}"]
    
    def get_servicehealth_by_id(self, item_id: uuid.UUID) -> Optional[ServiceHealth]:
        """Get servicehealth by ID."""
        return ServiceHealth.get_by_id(self.session, item_id)
    
    def get_servicehealths_by_owner(self, owner_id: uuid.UUID, limit: int = 20) -> List[ServiceHealth]:
        """Get servicehealths by owner."""
        return self.session.query(ServiceHealth).filter(
            ServiceHealth.owner_id == owner_id,
            ServiceHealth.is_deleted == False
        ).order_by(ServiceHealth.created_at.desc()).limit(limit).all()
    
    def update_servicehealth(self, item_id: uuid.UUID, updates: Dict[str, Any],
                        updated_by: uuid.UUID) -> Tuple[Optional[ServiceHealth], bool, List[str]]:
        """Update servicehealth with validation."""
        try:
            item = self.get_servicehealth_by_id(item_id)
            if not item:
                return None, False, ["ServiceHealth not found"]
            
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
            return None, False, [f"Error updating servicehealth: {str(e)}"]
    
    def delete_servicehealth(self, item_id: uuid.UUID, deleted_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Soft delete servicehealth."""
        try:
            item = self.get_servicehealth_by_id(item_id)
            if not item:
                return False, ["ServiceHealth not found"]
            
            # Check permissions
            if item.owner_id != deleted_by:
                return False, ["Insufficient permissions"]
            
            item.soft_delete()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error deleting servicehealth: {str(e)}"]
