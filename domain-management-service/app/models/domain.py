'''Domain management model'''

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class DomainStatus:
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class Domain(BaseModel):
    '''Domain model for managing domains and DNS records.'''
    
    __tablename__ = 'domains'
    
    # Basic fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), default=DomainStatus.PENDING, index=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Domain info
    registrar = Column(String(100))
    registration_date = Column(DateTime)
    expiration_date = Column(DateTime)
    auto_renew = Column(Boolean, default=True)
    
    # DNS settings
    nameservers = Column(Text)  # JSON array of nameservers
    dns_provider = Column(String(100))
    
    # SSL/TLS
    ssl_enabled = Column(Boolean, default=False)
    ssl_provider = Column(String(100))
    ssl_expiration = Column(DateTime)
    
    # WordPress integration
    wordpress_site_id = Column(UUID(as_uuid=True))
    is_primary_domain = Column(Boolean, default=False)
    
    def __repr__(self) -> str:
        return f"<Domain(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def is_expired(self) -> bool:
        '''Check if domain has expired.'''
        if self.expiration_date:
            return datetime.utcnow() > self.expiration_date
        return False
    
    def days_until_expiry(self) -> Optional[int]:
        '''Get days until domain expires.'''
        if self.expiration_date:
            delta = self.expiration_date - datetime.utcnow()
            return delta.days
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        '''Convert domain to dictionary.'''
        data = super().to_dict()
        data.update({
            'name': self.name,
            'status': self.status,
            'owner_id': str(self.owner_id),
            'workspace_id': str(self.workspace_id),
            'registrar': self.registrar,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'auto_renew': self.auto_renew,
            'ssl_enabled': self.ssl_enabled,
            'ssl_provider': self.ssl_provider,
            'ssl_expiration': self.ssl_expiration.isoformat() if self.ssl_expiration else None,
            'is_expired': self.is_expired(),
            'days_until_expiry': self.days_until_expiry()
        })
        return data
