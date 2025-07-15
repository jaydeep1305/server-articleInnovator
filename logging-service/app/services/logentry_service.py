"""
LogEntryService - Business Logic Layer

This module contains business logic for logging-service operations.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.logentry import LogEntry
from app import db


class LogEntryService:
    """Service class for logentry management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_logentry(self, name: str, owner_id: uuid.UUID,
                        **kwargs) -> Tuple[Optional[LogEntry], bool, List[str]]:
        """Create a new logentry with validation."""
        try:
            # Create logentry
            item = LogEntry(
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
            return None, False, ["LogEntry with this name already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating logentry: {str(e)}"]
    
    def get_logentry_by_id(self, item_id: uuid.UUID) -> Optional[LogEntry]:
        """Get logentry by ID."""
        return LogEntry.get_by_id(self.session, item_id)
    
    def get_logentrys_by_owner(self, owner_id: uuid.UUID, limit: int = 20) -> List[LogEntry]:
        """Get logentrys by owner."""
        return self.session.query(LogEntry).filter(
            LogEntry.owner_id == owner_id,
            LogEntry.is_deleted == False
        ).order_by(LogEntry.created_at.desc()).limit(limit).all()
    
    def update_logentry(self, item_id: uuid.UUID, updates: Dict[str, Any],
                        updated_by: uuid.UUID) -> Tuple[Optional[LogEntry], bool, List[str]]:
        """Update logentry with validation."""
        try:
            item = self.get_logentry_by_id(item_id)
            if not item:
                return None, False, ["LogEntry not found"]
            
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
            return None, False, [f"Error updating logentry: {str(e)}"]
    
    def delete_logentry(self, item_id: uuid.UUID, deleted_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Soft delete logentry."""
        try:
            item = self.get_logentry_by_id(item_id)
            if not item:
                return False, ["LogEntry not found"]
            
            # Check permissions
            if item.owner_id != deleted_by:
                return False, ["Insufficient permissions"]
            
            item.soft_delete()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error deleting logentry: {str(e)}"]
