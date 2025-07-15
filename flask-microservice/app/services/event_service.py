"""
Event service module for event-driven architecture and message publishing.

This module provides the EventService class that handles publishing and consuming
events in a microservice architecture. It supports various message brokers and
implements event sourcing patterns for audit trails and system integration.

Author: AI Assistant
Date: 2024
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
import redis
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of event types for the microservice."""
    
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DEACTIVATED = "user.deactivated"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PASSWORD_CHANGED = "user.password_changed"
    LOGIN_FAILED = "user.login_failed"
    
    # Role and permission events
    ROLE_CREATED = "role.created"
    ROLE_UPDATED = "role.updated"
    ROLE_DELETED = "role.deleted"
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"
    
    # Workspace events
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_DELETED = "workspace.deleted"
    WORKSPACE_MEMBER_ADDED = "workspace.member_added"
    WORKSPACE_MEMBER_REMOVED = "workspace.member_removed"
    WORKSPACE_ROLE_CHANGED = "workspace.role_changed"
    
    # Invitation events
    INVITATION_CREATED = "invitation.created"
    INVITATION_USED = "invitation.used"
    INVITATION_EXPIRED = "invitation.expired"
    
    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_INFO = "system.info"


@dataclass
class Event:
    """
    Data class representing a system event.
    
    This class encapsulates all the information about an event that occurs
    in the system, providing a standardized format for event data.
    
    Attributes:
        event_id (str): Unique identifier for the event
        event_type (EventType): Type of event that occurred
        entity_id (str): ID of the entity the event relates to
        entity_type (str): Type of entity (user, workspace, etc.)
        timestamp (datetime): When the event occurred
        data (Dict[str, Any]): Additional event-specific data
        source_service (str): Service that published the event
        correlation_id (str): Optional correlation ID for request tracing
        version (str): Event schema version
    """
    
    event_id: str
    event_type: EventType
    entity_id: str
    entity_type: str
    timestamp: datetime
    data: Dict[str, Any]
    source_service: str = "user-management-service"
    correlation_id: Optional[str] = None
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Event data as dictionary
        """
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    def to_json(self) -> str:
        """
        Convert event to JSON string.
        
        Returns:
            str: Event data as JSON string
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """
        Create event from dictionary.
        
        Args:
            data: Event data dictionary
            
        Returns:
            Event: Event instance
        """
        data['event_type'] = EventType(data['event_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """
        Create event from JSON string.
        
        Args:
            json_str: Event data as JSON string
            
        Returns:
            Event: Event instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class EventPublisher:
    """
    Base class for event publishers.
    
    This abstract class defines the interface for publishing events
    to different message brokers or event stores.
    """
    
    def publish(self, event: Event) -> bool:
        """
        Publish an event.
        
        Args:
            event: Event to publish
            
        Returns:
            bool: True if event was published successfully
        """
        raise NotImplementedError("Subclasses must implement publish method")
    
    def publish_batch(self, events: List[Event]) -> bool:
        """
        Publish multiple events in a batch.
        
        Args:
            events: List of events to publish
            
        Returns:
            bool: True if all events were published successfully
        """
        for event in events:
            if not self.publish(event):
                return False
        return True


class RedisEventPublisher(EventPublisher):
    """
    Redis-based event publisher implementation.
    
    This publisher uses Redis streams or pub/sub to publish events
    to subscribers and other microservices.
    """
    
    def __init__(self, redis_url: str, stream_name: str = "events"):
        """
        Initialize Redis event publisher.
        
        Args:
            redis_url: Redis connection URL
            stream_name: Name of the Redis stream for events
        """
        self.redis_client = redis.from_url(redis_url)
        self.stream_name = stream_name
    
    def publish(self, event: Event) -> bool:
        """
        Publish event to Redis stream.
        
        Args:
            event: Event to publish
            
        Returns:
            bool: True if event was published successfully
        """
        try:
            # Publish to Redis stream
            self.redis_client.xadd(
                self.stream_name,
                event.to_dict(),
                maxlen=10000  # Keep only recent events
            )
            
            # Also publish to pub/sub for real-time subscribers
            channel_name = f"events:{event.event_type.value}"
            self.redis_client.publish(channel_name, event.to_json())
            
            logger.info(f"Published event {event.event_id} of type {event.event_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False
    
    def get_events(self, start_id: str = "0", count: int = 100) -> List[Event]:
        """
        Retrieve events from Redis stream.
        
        Args:
            start_id: Starting event ID (Redis stream ID)
            count: Maximum number of events to retrieve
            
        Returns:
            List[Event]: List of events
        """
        try:
            events = []
            stream_events = self.redis_client.xrange(
                self.stream_name, 
                min=start_id, 
                count=count
            )
            
            for stream_id, fields in stream_events:
                try:
                    # Convert Redis fields to Event
                    event_data = {k.decode(): v.decode() for k, v in fields.items()}
                    
                    # Parse JSON fields
                    if 'data' in event_data:
                        event_data['data'] = json.loads(event_data['data'])
                    
                    event = Event.from_dict(event_data)
                    events.append(event)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse event {stream_id}: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
            return []


class InMemoryEventPublisher(EventPublisher):
    """
    In-memory event publisher for testing and development.
    
    This publisher stores events in memory and provides methods
    to retrieve them for testing purposes.
    """
    
    def __init__(self):
        """Initialize in-memory event publisher."""
        self.events: List[Event] = []
        self.subscribers: Dict[EventType, List[Callable]] = {}
    
    def publish(self, event: Event) -> bool:
        """
        Publish event to memory storage.
        
        Args:
            event: Event to publish
            
        Returns:
            bool: True if event was published successfully
        """
        try:
            self.events.append(event)
            
            # Notify subscribers
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.warning(f"Subscriber callback failed: {e}")
            
            logger.info(f"Published event {event.event_id} of type {event.event_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of events to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def get_events(self, event_type: Optional[EventType] = None, 
                  entity_id: Optional[str] = None) -> List[Event]:
        """
        Retrieve events from memory storage.
        
        Args:
            event_type: Optional event type filter
            entity_id: Optional entity ID filter
            
        Returns:
            List[Event]: Filtered list of events
        """
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if entity_id:
            events = [e for e in events if e.entity_id == entity_id]
        
        return events
    
    def clear_events(self) -> None:
        """Clear all stored events."""
        self.events.clear()


class EventService:
    """
    Main event service class for managing events in the microservice.
    
    This service provides a high-level interface for publishing events,
    managing event publishers, and handling event-related operations.
    It supports multiple publishers and provides event correlation.
    """
    
    def __init__(self, publishers: Optional[List[EventPublisher]] = None, 
                 correlation_id: Optional[str] = None):
        """
        Initialize event service.
        
        Args:
            publishers: List of event publishers to use
            correlation_id: Default correlation ID for events
        """
        self.publishers = publishers or [InMemoryEventPublisher()]
        self.correlation_id = correlation_id
        self.event_store: List[Event] = []
    
    def publish_event(self, event_type: EventType, entity_id: str, 
                     entity_type: str, data: Dict[str, Any],
                     correlation_id: Optional[str] = None) -> bool:
        """
        Publish an event to all configured publishers.
        
        This method creates an Event instance and publishes it to all
        configured publishers. It also stores the event locally for
        audit trails and debugging purposes.
        
        Args:
            event_type: Type of event to publish
            entity_id: ID of the entity the event relates to
            entity_type: Type of entity (user, workspace, etc.)
            data: Additional event-specific data
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            bool: True if event was published to at least one publisher
            
        Example:
            >>> event_service.publish_event(
            ...     event_type=EventType.USER_CREATED,
            ...     entity_id="user-123",
            ...     entity_type="user",
            ...     data={"email": "user@example.com"}
            ... )
        """
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            timestamp=datetime.utcnow(),
            data=data,
            correlation_id=correlation_id or self.correlation_id
        )
        
        # Store event locally
        self.event_store.append(event)
        
        # Publish to all publishers
        success_count = 0
        for publisher in self.publishers:
            try:
                if publisher.publish(event):
                    success_count += 1
            except Exception as e:
                logger.error(f"Publisher {publisher.__class__.__name__} failed: {e}")
        
        return success_count > 0
    
    def publish_user_event(self, event_type: EventType, user_id: str, 
                          data: Dict[str, Any]) -> bool:
        """
        Convenience method to publish user-related events.
        
        Args:
            event_type: Type of user event
            user_id: User ID
            data: Event data
            
        Returns:
            bool: True if event was published
        """
        return self.publish_event(event_type, user_id, "user", data)
    
    def publish_workspace_event(self, event_type: EventType, workspace_id: str, 
                               data: Dict[str, Any]) -> bool:
        """
        Convenience method to publish workspace-related events.
        
        Args:
            event_type: Type of workspace event
            workspace_id: Workspace ID
            data: Event data
            
        Returns:
            bool: True if event was published
        """
        return self.publish_event(event_type, workspace_id, "workspace", data)
    
    def publish_system_event(self, event_type: EventType, message: str, 
                            details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Convenience method to publish system-related events.
        
        Args:
            event_type: Type of system event
            message: Event message
            details: Optional additional details
            
        Returns:
            bool: True if event was published
        """
        data = {"message": message}
        if details:
            data.update(details)
        
        return self.publish_event(event_type, "system", "system", data)
    
    def get_events_for_entity(self, entity_id: str, 
                             event_types: Optional[List[EventType]] = None) -> List[Event]:
        """
        Get all events for a specific entity.
        
        Args:
            entity_id: Entity ID to filter by
            event_types: Optional list of event types to filter by
            
        Returns:
            List[Event]: Events for the entity
        """
        events = [e for e in self.event_store if e.entity_id == entity_id]
        
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        
        return sorted(events, key=lambda e: e.timestamp)
    
    def get_recent_events(self, count: int = 50, 
                         event_types: Optional[List[EventType]] = None) -> List[Event]:
        """
        Get recent events.
        
        Args:
            count: Number of recent events to return
            event_types: Optional list of event types to filter by
            
        Returns:
            List[Event]: Recent events
        """
        events = self.event_store
        
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        
        # Sort by timestamp descending and take the most recent
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:count]
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set correlation ID for future events.
        
        Args:
            correlation_id: Correlation ID to use
        """
        self.correlation_id = correlation_id
    
    def add_publisher(self, publisher: EventPublisher) -> None:
        """
        Add an event publisher.
        
        Args:
            publisher: Event publisher to add
        """
        self.publishers.append(publisher)
    
    def remove_publisher(self, publisher: EventPublisher) -> None:
        """
        Remove an event publisher.
        
        Args:
            publisher: Event publisher to remove
        """
        if publisher in self.publishers:
            self.publishers.remove(publisher)