"""
ImageRequestService - Business Logic Layer

This module contains business logic for image-generation-service operations.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.imagerequest import ImageRequest
from app import db


class ImageRequestService:
    """Service class for imagerequest management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_imagerequest(self, name: str, owner_id: uuid.UUID,
                        **kwargs) -> Tuple[Optional[ImageRequest], bool, List[str]]:
        """Create a new imagerequest with validation."""
        try:
            # Create imagerequest
            item = ImageRequest(
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
            return None, False, ["ImageRequest with this name already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating imagerequest: {str(e)}"]
    
    def get_imagerequest_by_id(self, item_id: uuid.UUID) -> Optional[ImageRequest]:
        """Get imagerequest by ID."""
        return ImageRequest.get_by_id(self.session, item_id)
    
    def get_imagerequests_by_owner(self, owner_id: uuid.UUID, limit: int = 20) -> List[ImageRequest]:
        """Get imagerequests by owner."""
        return self.session.query(ImageRequest).filter(
            ImageRequest.owner_id == owner_id,
            ImageRequest.is_deleted == False
        ).order_by(ImageRequest.created_at.desc()).limit(limit).all()
    
    def update_imagerequest(self, item_id: uuid.UUID, updates: Dict[str, Any],
                        updated_by: uuid.UUID) -> Tuple[Optional[ImageRequest], bool, List[str]]:
        """Update imagerequest with validation."""
        try:
            item = self.get_imagerequest_by_id(item_id)
            if not item:
                return None, False, ["ImageRequest not found"]
            
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
            return None, False, [f"Error updating imagerequest: {str(e)}"]
    
    def delete_imagerequest(self, item_id: uuid.UUID, deleted_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Soft delete imagerequest."""
        try:
            item = self.get_imagerequest_by_id(item_id)
            if not item:
                return False, ["ImageRequest not found"]
            
            # Check permissions
            if item.owner_id != deleted_by:
                return False, ["Insufficient permissions"]
            
            item.soft_delete()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error deleting imagerequest: {str(e)}"]
