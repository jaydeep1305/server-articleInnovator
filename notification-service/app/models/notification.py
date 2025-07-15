'''Notification model for multi-channel messaging'''

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.models.base import BaseModel


class NotificationStatus:
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class NotificationChannel:
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class Notification(BaseModel):
    '''Notification model for managing multi-channel notifications.'''
    
    __tablename__ = 'notifications'
    
    # Basic fields
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default=NotificationStatus.PENDING, index=True)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Recipient info
    recipient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    recipient_email = Column(String(255))
    recipient_phone = Column(String(20))
    
    # Channel and delivery
    channel = Column(String(50), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True))
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    
    # Content and metadata
    data = Column(JSON)  # Template variables and additional data
    tags = Column(JSON)  # Categories/tags for filtering
    
    # Tracking
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    delivery_attempts = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Context
    source_service = Column(String(100))
    source_event = Column(String(100))
    workspace_id = Column(UUID(as_uuid=True), index=True)
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    def mark_as_sent(self) -> None:
        '''Mark notification as sent.'''
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()
    
    def mark_as_failed(self, error: str) -> None:
        '''Mark notification as failed.'''
        self.status = NotificationStatus.FAILED
        self.error_message = error
        self.delivery_attempts += 1
    
    def mark_as_opened(self) -> None:
        '''Mark notification as opened by recipient.'''
        if not self.opened_at:
            self.opened_at = datetime.utcnow()
    
    def mark_as_clicked(self) -> None:
        '''Mark notification as clicked by recipient.'''
        if not self.clicked_at:
            self.clicked_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        '''Convert notification to dictionary.'''
        data = super().to_dict()
        data.update({
            'title': self.title,
            'message': self.message,
            'status': self.status,
            'priority': self.priority,
            'recipient_id': str(self.recipient_id),
            'recipient_email': self.recipient_email,
            'channel': self.channel,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'delivery_attempts': self.delivery_attempts,
            'data': self.data,
            'tags': self.tags,
            'source_service': self.source_service,
            'workspace_id': str(self.workspace_id) if self.workspace_id else None
        })
        return data
