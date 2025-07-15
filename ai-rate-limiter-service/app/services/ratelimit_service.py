"""
RateLimitService - Business Logic Layer

This module contains business logic for ai-rate-limiter-service operations.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.ratelimit import RateLimit
from app import db


class RateLimitService:
    """Service class for ratelimit management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_ratelimit(self, name: str, owner_id: uuid.UUID,
                        **kwargs) -> Tuple[Optional[RateLimit], bool, List[str]]:
        """Create a new ratelimit with validation."""
        try:
            # Create ratelimit
            item = RateLimit(
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
            return None, False, ["RateLimit with this name already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating ratelimit: {str(e)}"]
    
    def get_ratelimit_by_id(self, item_id: uuid.UUID) -> Optional[RateLimit]:
        """Get ratelimit by ID."""
        return RateLimit.get_by_id(self.session, item_id)
    
    def get_ratelimits_by_owner(self, owner_id: uuid.UUID, limit: int = 20) -> List[RateLimit]:
        """Get ratelimits by owner."""
        return self.session.query(RateLimit).filter(
            RateLimit.owner_id == owner_id,
            RateLimit.is_deleted == False
        ).order_by(RateLimit.created_at.desc()).limit(limit).all()
    
    def update_ratelimit(self, item_id: uuid.UUID, updates: Dict[str, Any],
                        updated_by: uuid.UUID) -> Tuple[Optional[RateLimit], bool, List[str]]:
        """Update ratelimit with validation."""
        try:
            item = self.get_ratelimit_by_id(item_id)
            if not item:
                return None, False, ["RateLimit not found"]
            
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
            return None, False, [f"Error updating ratelimit: {str(e)}"]
    
    def delete_ratelimit(self, item_id: uuid.UUID, deleted_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Soft delete ratelimit."""
        try:
            item = self.get_ratelimit_by_id(item_id)
            if not item:
                return False, ["RateLimit not found"]
            
            # Check permissions
            if item.owner_id != deleted_by:
                return False, ["Insufficient permissions"]
            
            item.soft_delete()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error deleting ratelimit: {str(e)}"]
