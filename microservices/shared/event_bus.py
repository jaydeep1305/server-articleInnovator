"""
Shared Event Bus for Microservices Communication via RabbitMQ

This module provides event publishing and consuming capabilities for all microservices
in the event-driven architecture using RabbitMQ as the message broker.

Author: AI Assistant
Date: 2024
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import pika
import threading
from functools import wraps

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for the microservices architecture."""
    
    # User Management Events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    # Workspace Events
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_DELETED = "workspace.deleted"
    WORKSPACE_USER_ADDED = "workspace.user_added"
    WORKSPACE_USER_REMOVED = "workspace.user_removed"
    
    # Article Events
    ARTICLE_CREATED = "article.created"
    ARTICLE_UPDATED = "article.updated"
    ARTICLE_PUBLISHED = "article.published"
    ARTICLE_DELETED = "article.deleted"
    ARTICLE_GENERATION_REQUESTED = "article.generation_requested"
    ARTICLE_GENERATION_COMPLETED = "article.generation_completed"
    
    # Domain Events
    DOMAIN_CREATED = "domain.created"
    DOMAIN_UPDATED = "domain.updated"
    DOMAIN_DELETED = "domain.deleted"
    DOMAIN_VERIFIED = "domain.verified"
    
    # AI Configuration Events
    AI_MODEL_UPDATED = "ai.model_updated"
    PROMPT_CREATED = "prompt.created"
    PROMPT_UPDATED = "prompt.updated"
    
    # Image Generation Events
    IMAGE_GENERATION_REQUESTED = "image.generation_requested"
    IMAGE_GENERATION_COMPLETED = "image.generation_completed"
    IMAGE_GENERATION_FAILED = "image.generation_failed"
    
    # Monitoring Events
    COMPETITOR_ANALYSIS_COMPLETED = "monitoring.competitor_analysis_completed"
    MONITORING_ALERT = "monitoring.alert"
    
    # Notification Events
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_SENT = "notification.sent"
    EMAIL_SENT = "email.sent"
    
    # System Events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SERVICE_HEALTH_CHECK = "service.health_check"


@dataclass
class Event:
    """Event data class for microservices communication."""
    
    event_id: str
    event_type: EventType
    service: str
    entity_id: str
    entity_type: str
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        data['event_type'] = EventType(data['event_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class EventBus:
    """
    RabbitMQ-based event bus for microservices communication.
    
    This class handles event publishing and consuming using RabbitMQ
    with proper error handling, retries, and dead letter queues.
    """
    
    def __init__(self, rabbitmq_url: str, service_name: str):
        """
        Initialize the event bus.
        
        Args:
            rabbitmq_url: RabbitMQ connection URL
            service_name: Name of the service using this event bus
        """
        self.rabbitmq_url = rabbitmq_url
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.consuming = False
        self._setup_connection()
        self._declare_exchanges_and_queues()
    
    def _setup_connection(self) -> None:
        """Setup RabbitMQ connection and channel."""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            logger.info(f"Connected to RabbitMQ for service {self.service_name}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def _declare_exchanges_and_queues(self) -> None:
        """Declare exchanges and queues for the service."""
        try:
            # Main events exchange
            self.channel.exchange_declare(
                exchange='events',
                exchange_type='topic',
                durable=True
            )
            
            # Dead letter exchange
            self.channel.exchange_declare(
                exchange='events.dlx',
                exchange_type='direct',
                durable=True
            )
            
            # Service-specific queue
            queue_name = f"{self.service_name}.events"
            self.channel.queue_declare(
                queue=queue_name,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': 'events.dlx',
                    'x-dead-letter-routing-key': f"{self.service_name}.dlq"
                }
            )
            
            # Dead letter queue
            dlq_name = f"{self.service_name}.dlq"
            self.channel.queue_declare(queue=dlq_name, durable=True)
            self.channel.queue_bind(
                exchange='events.dlx',
                queue=dlq_name,
                routing_key=f"{self.service_name}.dlq"
            )
            
            logger.info(f"Declared exchanges and queues for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to declare exchanges and queues: {e}")
            raise
    
    def publish_event(self, event_type: EventType, entity_id: str, 
                     entity_type: str, data: Dict[str, Any],
                     correlation_id: Optional[str] = None,
                     user_id: Optional[str] = None) -> bool:
        """
        Publish an event to the event bus.
        
        Args:
            event_type: Type of event
            entity_id: ID of the entity
            entity_type: Type of entity
            data: Event data
            correlation_id: Optional correlation ID
            user_id: Optional user ID
            
        Returns:
            bool: True if event was published successfully
        """
        try:
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                service=self.service_name,
                entity_id=entity_id,
                entity_type=entity_type,
                timestamp=datetime.utcnow(),
                data=data,
                correlation_id=correlation_id,
                user_id=user_id
            )
            
            # Publish to events exchange with routing key
            routing_key = f"{event_type.value}.{entity_type}"
            
            self.channel.basic_publish(
                exchange='events',
                routing_key=routing_key,
                body=event.to_json(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    correlation_id=correlation_id,
                    message_id=event.event_id,
                    timestamp=int(event.timestamp.timestamp())
                )
            )
            
            logger.info(f"Published event {event.event_id}: {event_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type.value}: {e}")
            return False
    
    def subscribe_to_event(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        
        # Bind queue to exchange with routing key pattern
        queue_name = f"{self.service_name}.events"
        routing_key = f"{event_type.value}.*"
        
        self.channel.queue_bind(
            exchange='events',
            queue=queue_name,
            routing_key=routing_key
        )
        
        logger.info(f"Subscribed to event type: {event_type.value}")
    
    def subscribe_to_all_events(self, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to all events.
        
        Args:
            handler: Function to handle all events
        """
        # Bind queue to receive all events
        queue_name = f"{self.service_name}.events"
        self.channel.queue_bind(
            exchange='events',
            queue=queue_name,
            routing_key='*.*'
        )
        
        # Store handler for all event types
        for event_type in EventType:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)
        
        logger.info("Subscribed to all events")
    
    def _process_message(self, channel, method, properties, body) -> None:
        """Process received message."""
        try:
            # Parse event
            event_data = json.loads(body.decode('utf-8'))
            event = Event.from_dict(event_data)
            
            # Find and execute handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Event handler failed for {event.event_type.value}: {e}")
                        # Don't acknowledge the message if handler fails
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                        return
            
            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"Processed event {event.event_id}: {event.event_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            # Reject message and send to DLQ
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self) -> None:
        """Start consuming events."""
        if self.consuming:
            return
        
        try:
            queue_name = f"{self.service_name}.events"
            self.channel.basic_qos(prefetch_count=10)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self._process_message
            )
            
            self.consuming = True
            logger.info(f"Started consuming events for {self.service_name}")
            self.channel.start_consuming()
            
        except Exception as e:
            logger.error(f"Failed to start consuming: {e}")
            self.consuming = False
    
    def stop_consuming(self) -> None:
        """Stop consuming events."""
        if self.consuming:
            self.channel.stop_consuming()
            self.consuming = False
            logger.info(f"Stopped consuming events for {self.service_name}")
    
    def close(self) -> None:
        """Close connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info(f"Closed RabbitMQ connection for {self.service_name}")


def event_handler(event_type: EventType):
    """
    Decorator for event handlers.
    
    Args:
        event_type: Event type to handle
    """
    def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
        @wraps(func)
        def wrapper(event: Event) -> None:
            if event.event_type == event_type:
                return func(event)
            else:
                logger.warning(f"Event type mismatch: expected {event_type.value}, got {event.event_type.value}")
        
        wrapper._event_type = event_type
        return wrapper
    
    return decorator


class EventConsumer:
    """
    Event consumer that runs in a separate thread.
    
    This class allows services to consume events without blocking
    the main application thread.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize event consumer.
        
        Args:
            event_bus: Event bus instance
        """
        self.event_bus = event_bus
        self.consumer_thread = None
        self.running = False
    
    def start(self) -> None:
        """Start event consumer in a separate thread."""
        if self.running:
            return
        
        self.running = True
        self.consumer_thread = threading.Thread(
            target=self.event_bus.start_consuming,
            daemon=True
        )
        self.consumer_thread.start()
        logger.info("Started event consumer thread")
    
    def stop(self) -> None:
        """Stop event consumer."""
        if self.running:
            self.running = False
            self.event_bus.stop_consuming()
            if self.consumer_thread:
                self.consumer_thread.join(timeout=5)
            logger.info("Stopped event consumer thread")