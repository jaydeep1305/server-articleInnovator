'''Generic Metric model'''

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class Metric(BaseModel):
    '''Metric model for monitoring-service.'''
    
    __tablename__ = 'metrics'
    
    # Basic fields
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active", index=True)
    
    # Ownership
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), index=True)
    
    def __repr__(self) -> str:
        return f"<Metric(id={self.id}, name='{self.name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        '''Convert metric to dictionary.'''
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'owner_id': str(self.owner_id),
            'workspace_id': str(self.workspace_id) if self.workspace_id else None
        })
        return data
