"""
Domain Service - Business Logic Layer

This module contains business logic for domain management,
including DNS configuration, SSL management, and WordPress integration.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.domain import Domain, DomainStatus
from app import db


class DomainService:
    """Service class for domain management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def register_domain(self, name: str, owner_id: uuid.UUID, 
                       workspace_id: uuid.UUID, **kwargs) -> Tuple[Optional[Domain], bool, List[str]]:
        """Register a new domain."""
        try:
            # Check if domain already exists
            existing = self.session.query(Domain).filter(
                Domain.name == name.lower(),
                Domain.is_deleted == False
            ).first()
            
            if existing:
                return None, False, ["Domain already registered"]
            
            # Create domain
            domain = Domain(
                name=name.lower().strip(),
                owner_id=owner_id,
                workspace_id=workspace_id,
                status=DomainStatus.PENDING,
                **kwargs
            )
            
            # Validate
            is_valid, errors = domain.validate()
            if not is_valid:
                return None, False, errors
            
            self.session.add(domain)
            self.session.commit()
            
            return domain, True, []
            
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error registering domain: {str(e)}"]
    
    def check_domain_expiry(self, workspace_id: uuid.UUID = None) -> List[Domain]:
        """Check for domains expiring soon."""
        expiry_threshold = datetime.utcnow() + timedelta(days=30)
        
        query = self.session.query(Domain).filter(
            Domain.expiration_date <= expiry_threshold,
            Domain.status == DomainStatus.ACTIVE,
            Domain.is_deleted == False
        )
        
        if workspace_id:
            query = query.filter(Domain.workspace_id == workspace_id)
        
        return query.all()
    
    def update_ssl_status(self, domain_id: uuid.UUID, enabled: bool, 
                         provider: str = None, expiration: datetime = None) -> Tuple[bool, List[str]]:
        """Update SSL status for domain."""
        try:
            domain = Domain.get_by_id(self.session, domain_id)
            if not domain:
                return False, ["Domain not found"]
            
            domain.ssl_enabled = enabled
            if provider:
                domain.ssl_provider = provider
            if expiration:
                domain.ssl_expiration = expiration
            
            self.session.commit()
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error updating SSL status: {str(e)}"]
