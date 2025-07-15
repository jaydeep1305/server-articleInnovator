"""
ScrapingJobService - Business Logic Layer

This module contains business logic for scraping-service operations.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.scrapingjob import ScrapingJob
from app import db


class ScrapingJobService:
    """Service class for scrapingjob management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_scrapingjob(self, name: str, owner_id: uuid.UUID,
                        **kwargs) -> Tuple[Optional[ScrapingJob], bool, List[str]]:
        """Create a new scrapingjob with validation."""
        try:
            # Create scrapingjob
            item = ScrapingJob(
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
            return None, False, ["ScrapingJob with this name already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating scrapingjob: {str(e)}"]
    
    def get_scrapingjob_by_id(self, item_id: uuid.UUID) -> Optional[ScrapingJob]:
        """Get scrapingjob by ID."""
        return ScrapingJob.get_by_id(self.session, item_id)
    
    def get_scrapingjobs_by_owner(self, owner_id: uuid.UUID, limit: int = 20) -> List[ScrapingJob]:
        """Get scrapingjobs by owner."""
        return self.session.query(ScrapingJob).filter(
            ScrapingJob.owner_id == owner_id,
            ScrapingJob.is_deleted == False
        ).order_by(ScrapingJob.created_at.desc()).limit(limit).all()
    
    def update_scrapingjob(self, item_id: uuid.UUID, updates: Dict[str, Any],
                        updated_by: uuid.UUID) -> Tuple[Optional[ScrapingJob], bool, List[str]]:
        """Update scrapingjob with validation."""
        try:
            item = self.get_scrapingjob_by_id(item_id)
            if not item:
                return None, False, ["ScrapingJob not found"]
            
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
            return None, False, [f"Error updating scrapingjob: {str(e)}"]
    
    def delete_scrapingjob(self, item_id: uuid.UUID, deleted_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Soft delete scrapingjob."""
        try:
            item = self.get_scrapingjob_by_id(item_id)
            if not item:
                return False, ["ScrapingJob not found"]
            
            # Check permissions
            if item.owner_id != deleted_by:
                return False, ["Insufficient permissions"]
            
            item.soft_delete()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error deleting scrapingjob: {str(e)}"]
