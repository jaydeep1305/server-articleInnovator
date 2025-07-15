"""
Notification Service - Business Logic Layer

This module contains business logic for multi-channel notification delivery,
template management, and delivery tracking.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus, NotificationChannel
from app import db


class NotificationService:
    """Service class for notification management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def send_notification(self, title: str, message: str, recipient_id: uuid.UUID,
                         channel: str, **kwargs) -> Tuple[Optional[Notification], bool, List[str]]:
        """Send a notification through specified channel."""
        try:
            # Create notification
            notification = Notification(
                title=title,
                message=message,
                recipient_id=recipient_id,
                channel=channel,
                **kwargs
            )
            
            # Validate
            is_valid, errors = notification.validate()
            if not is_valid:
                return None, False, errors
            
            self.session.add(notification)
            self.session.flush()
            
            # Send through appropriate channel
            success = self._deliver_notification(notification)
            
            if success:
                notification.mark_as_sent()
            else:
                notification.mark_as_failed("Delivery failed")
            
            self.session.commit()
            
            return notification, success, []
            
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error sending notification: {str(e)}"]
    
    def get_user_notifications(self, user_id: uuid.UUID, 
                              unread_only: bool = False, limit: int = 20) -> List[Notification]:
        """Get notifications for a user."""
        query = self.session.query(Notification).filter(
            Notification.recipient_id == user_id,
            Notification.is_deleted == False
        )
        
        if unread_only:
            query = query.filter(Notification.opened_at.is_(None))
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Tuple[bool, List[str]]:
        """Mark notification as read."""
        try:
            notification = self.session.query(Notification).filter(
                Notification.id == notification_id,
                Notification.recipient_id == user_id
            ).first()
            
            if not notification:
                return False, ["Notification not found"]
            
            notification.mark_as_opened()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error marking notification as read: {str(e)}"]
    
    def _deliver_notification(self, notification: Notification) -> bool:
        """Deliver notification through appropriate channel."""
        try:
            if notification.channel == NotificationChannel.EMAIL:
                return self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                return self._send_sms(notification)
            elif notification.channel == NotificationChannel.PUSH:
                return self._send_push(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                return True  # In-app notifications are stored in DB
            else:
                return False
        except Exception:
            return False
    
    def _send_email(self, notification: Notification) -> bool:
        """Send email notification (placeholder)."""
        # TODO: Integrate with email service
        return True
    
    def _send_sms(self, notification: Notification) -> bool:
        """Send SMS notification (placeholder)."""
        # TODO: Integrate with SMS service
        return True
    
    def _send_push(self, notification: Notification) -> bool:
        """Send push notification (placeholder)."""
        # TODO: Integrate with push notification service
        return True
