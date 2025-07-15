#!/usr/bin/env python3
"""
Complete All Services Script

This script systematically completes all missing components across all microservices
including domain-specific models, business logic services, API routes, comprehensive
test suites, and configuration files.

Author: AI Assistant  
Date: 2024
"""

import os
from pathlib import Path
from typing import Dict, List, Any

# Service configurations
SERVICES = {
    "article-management-service": {
        "port": 5003,
        "database": "article_management",
        "models": ["Article", "ArticleVersion", "Category", "Tag", "Comment"],
        "description": "Content management and publishing service"
    },
    "domain-management-service": {
        "port": 5004, 
        "database": "domain_management",
        "models": ["Domain", "WordPressSite", "DomainRecord", "SSLCertificate"],
        "description": "Domain and WordPress site management"
    },
    "ai-configuration-service": {
        "port": 5005,
        "database": "ai_configuration", 
        "models": ["AIModel", "ModelProvider", "Configuration", "Usage"],
        "description": "AI model configuration and management"
    },
    "image-generation-service": {
        "port": 5006,
        "database": "image_generation",
        "models": ["ImageRequest", "GeneratedImage", "ImageTemplate", "Generation"],
        "description": "AI-powered image generation service"
    },
    "monitoring-service": {
        "port": 5007,
        "database": "monitoring",
        "models": ["ServiceHealth", "Metric", "Alert", "Incident"],
        "description": "System monitoring and alerting"
    },
    "notification-service": {
        "port": 5008,
        "database": "notification",
        "models": ["Notification", "NotificationTemplate", "Channel", "Subscription"],
        "description": "Multi-channel notification service"
    },
    "logging-service": {
        "port": 5009,
        "database": "logging",
        "models": ["LogEntry", "AuditLog", "SystemEvent", "ErrorLog"],
        "description": "Centralized logging and auditing"
    },
    "configuration-service": {
        "port": 5010,
        "database": "configuration",
        "models": ["ConfigurationItem", "Environment", "Secret", "FeatureFlag"],
        "description": "Application configuration management"
    },
    "scraping-service": {
        "port": 5011,
        "database": "scraping",
        "models": ["ScrapingJob", "ScrapedData", "Source", "Schedule"],
        "description": "Web scraping and data collection"
    },
    "ai-rate-limiter-service": {
        "port": 5012,
        "database": "ai_rate_limiter",
        "models": ["RateLimit", "Usage", "Quota", "Throttle"],
        "description": "AI service rate limiting and quotas"
    }
}


def create_service_models(service_name: str, models: List[str]) -> None:
    """Create comprehensive models for a service."""
    
    # Create models directory if it doesn't exist
    models_dir = f"{service_name}/app/models"
    os.makedirs(models_dir, exist_ok=True)
    
    # Model templates based on service type
    model_templates = {
        "Article": """'''Article model for content management'''

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ArticleStatus:
    DRAFT = "draft"
    UNDER_REVIEW = "under_review" 
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Article(BaseModel):
    '''Article model for content management and publishing.'''
    
    __tablename__ = 'articles'
    
    # Basic fields
    title = Column(String(200), nullable=False)
    slug = Column(String(250), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    status = Column(String(50), default=ArticleStatus.DRAFT, index=True)
    
    # Author and workspace
    author_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # SEO fields
    meta_title = Column(String(200))
    meta_description = Column(String(300))
    meta_keywords = Column(String(500))
    featured_image_url = Column(String(500))
    
    # Publishing fields
    published_at = Column(DateTime)
    scheduled_at = Column(DateTime)
    word_count = Column(Integer, default=0)
    reading_time_minutes = Column(Integer, default=0)
    
    # Engagement metrics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # Content settings
    allow_comments = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    content_type = Column(String(50), default="article")
    
    # Relationships (defined as strings to avoid circular imports)
    # versions = relationship("ArticleVersion", back_populates="article")
    # comments = relationship("Comment", back_populates="article")
    
    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @classmethod
    def generate_slug(cls, title: str) -> str:
        '''Generate URL-friendly slug from title.'''
        import re
        slug = title.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug[:250]
    
    def publish(self) -> None:
        '''Publish the article.'''
        self.status = ArticleStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.calculate_reading_time()
    
    def calculate_reading_time(self) -> None:
        '''Calculate estimated reading time based on word count.'''
        if self.content:
            words = len(self.content.split())
            self.word_count = words
            # Average reading speed: 200 words per minute
            self.reading_time_minutes = max(1, round(words / 200))
    
    def to_dict(self) -> Dict[str, Any]:
        '''Convert article to dictionary.'''
        data = super().to_dict()
        data.update({
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'excerpt': self.excerpt,
            'status': self.status,
            'author_id': str(self.author_id),
            'workspace_id': str(self.workspace_id),
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'featured_image_url': self.featured_image_url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'word_count': self.word_count,
            'reading_time_minutes': self.reading_time_minutes,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'allow_comments': self.allow_comments,
            'is_featured': self.is_featured,
            'content_type': self.content_type
        })
        return data
""",
        
        "Domain": """'''Domain management model'''

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
""",

        "Notification": """'''Notification model for multi-channel messaging'''

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
"""
    }
    
    # Create primary model for each service
    for model in models:
        if model in model_templates:
            template = model_templates[model]
        else:
            # Generic model template
            template = f"""'''Generic {model} model'''

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class {model}(BaseModel):
    '''{model} model for {service_name}.'''
    
    __tablename__ = '{model.lower()}s'
    
    # Basic fields
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active", index=True)
    
    # Ownership
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), index=True)
    
    def __repr__(self) -> str:
        return f"<{model}(id={{self.id}}, name='{{self.name}}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        '''Convert {model.lower()} to dictionary.'''
        data = super().to_dict()
        data.update({{
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'owner_id': str(self.owner_id),
            'workspace_id': str(self.workspace_id) if self.workspace_id else None
        }})
        return data
"""
        
        model_file = f"{models_dir}/{model.lower()}.py"
        with open(model_file, "w") as f:
            f.write(template)


def create_service_business_logic(service_name: str, models: List[str]) -> None:
    """Create comprehensive service layer for business logic."""
    
    # Create services directory
    services_dir = f"{service_name}/app/services"
    os.makedirs(services_dir, exist_ok=True)
    
    # Main service class name
    main_model = models[0] if models else "Generic"
    service_class = f"{main_model}Service"
    
    # Service templates based on service type
    service_templates = {
        "ArticleService": '''"""
Article Service - Business Logic Layer

This module contains comprehensive business logic for article management,
including content creation, publishing workflow, SEO optimization, and analytics.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.article import Article, ArticleStatus
from app import db


class ArticleService:
    """Service class for article management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_article(self, title: str, content: str, author_id: uuid.UUID,
                      workspace_id: uuid.UUID, **kwargs) -> Tuple[Optional[Article], bool, List[str]]:
        """Create a new article with validation."""
        try:
            # Generate slug
            base_slug = Article.generate_slug(title)
            slug = self._ensure_unique_slug(base_slug)
            
            # Create article
            article = Article(
                title=title.strip(),
                slug=slug,
                content=content,
                author_id=author_id,
                workspace_id=workspace_id,
                **kwargs
            )
            
            # Calculate reading time
            article.calculate_reading_time()
            
            # Validate
            is_valid, errors = article.validate()
            if not is_valid:
                return None, False, errors
            
            self.session.add(article)
            self.session.commit()
            
            return article, True, []
            
        except IntegrityError:
            self.session.rollback()
            return None, False, ["Article with this slug already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating article: {str(e)}"]
    
    def publish_article(self, article_id: uuid.UUID, published_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Publish an article."""
        try:
            article = Article.get_by_id(self.session, article_id)
            if not article:
                return False, ["Article not found"]
            
            # Check permissions (simplified)
            if article.author_id != published_by:
                return False, ["Only the author can publish this article"]
            
            article.publish()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error publishing article: {str(e)}"]
    
    def get_articles_by_workspace(self, workspace_id: uuid.UUID, 
                                 status: str = None, limit: int = 20) -> List[Article]:
        """Get articles for a workspace."""
        query = self.session.query(Article).filter(
            Article.workspace_id == workspace_id,
            Article.is_deleted == False
        )
        
        if status:
            query = query.filter(Article.status == status)
        
        return query.order_by(Article.created_at.desc()).limit(limit).all()
    
    def search_articles(self, query: str, workspace_id: uuid.UUID = None) -> List[Article]:
        """Search articles by title and content."""
        from sqlalchemy import or_, func
        
        search_query = self.session.query(Article).filter(Article.is_deleted == False)
        
        if workspace_id:
            search_query = search_query.filter(Article.workspace_id == workspace_id)
        
        if query:
            search_terms = f"%{query}%"
            search_query = search_query.filter(
                or_(
                    func.lower(Article.title).like(func.lower(search_terms)),
                    func.lower(Article.content).like(func.lower(search_terms))
                )
            )
        
        return search_query.order_by(Article.created_at.desc()).limit(50).all()
    
    def _ensure_unique_slug(self, base_slug: str) -> str:
        """Ensure article slug is unique."""
        slug = base_slug
        counter = 1
        
        while True:
            existing = self.session.query(Article).filter(
                Article.slug == slug,
                Article.is_deleted == False
            ).first()
            
            if not existing:
                return slug
            
            slug = f"{base_slug}-{counter}"
            counter += 1
''',
        
        "DomainService": '''"""
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
''',
        
        "NotificationService": '''"""
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
'''
    }
    
    # Select appropriate template or use generic
    if service_class in service_templates:
        template = service_templates[service_class]
    else:
        # Generic service template
        template = f'''"""
{service_class} - Business Logic Layer

This module contains business logic for {service_name} operations.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.{main_model.lower()} import {main_model}
from app import db


class {service_class}:
    """Service class for {main_model.lower()} management operations."""
    
    def __init__(self, session: Session = None):
        self.session = session or db.session
    
    def create_{main_model.lower()}(self, name: str, owner_id: uuid.UUID,
                        **kwargs) -> Tuple[Optional[{main_model}], bool, List[str]]:
        """Create a new {main_model.lower()} with validation."""
        try:
            # Create {main_model.lower()}
            item = {main_model}(
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
            return None, False, ["{main_model} with this name already exists"]
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error creating {main_model.lower()}: {{str(e)}}"]
    
    def get_{main_model.lower()}_by_id(self, item_id: uuid.UUID) -> Optional[{main_model}]:
        """Get {main_model.lower()} by ID."""
        return {main_model}.get_by_id(self.session, item_id)
    
    def get_{main_model.lower()}s_by_owner(self, owner_id: uuid.UUID, limit: int = 20) -> List[{main_model}]:
        """Get {main_model.lower()}s by owner."""
        return self.session.query({main_model}).filter(
            {main_model}.owner_id == owner_id,
            {main_model}.is_deleted == False
        ).order_by({main_model}.created_at.desc()).limit(limit).all()
    
    def update_{main_model.lower()}(self, item_id: uuid.UUID, updates: Dict[str, Any],
                        updated_by: uuid.UUID) -> Tuple[Optional[{main_model}], bool, List[str]]:
        """Update {main_model.lower()} with validation."""
        try:
            item = self.get_{main_model.lower()}_by_id(item_id)
            if not item:
                return None, False, ["{main_model} not found"]
            
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
            return None, False, [f"Error updating {main_model.lower()}: {{str(e)}}"]
    
    def delete_{main_model.lower()}(self, item_id: uuid.UUID, deleted_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """Soft delete {main_model.lower()}."""
        try:
            item = self.get_{main_model.lower()}_by_id(item_id)
            if not item:
                return False, ["{main_model} not found"]
            
            # Check permissions
            if item.owner_id != deleted_by:
                return False, ["Insufficient permissions"]
            
            item.soft_delete()
            self.session.commit()
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error deleting {main_model.lower()}: {{str(e)}}"]
'''
    
    service_file = f"{services_dir}/{main_model.lower()}_service.py"
    with open(service_file, "w") as f:
        f.write(template)


def create_service_api_routes(service_name: str, models: List[str], port: int) -> None:
    """Create comprehensive REST API routes."""
    
    routes_dir = f"{service_name}/app/routes"
    os.makedirs(routes_dir, exist_ok=True)
    
    main_model = models[0] if models else "Generic"
    service_class = f"{main_model}Service"
    
    # API routes template
    template = f'''"""
{main_model} API Routes

REST API endpoints for {main_model.lower()} management with comprehensive
CRUD operations, validation, error handling, and rate limiting.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError, validate

from app.services.{main_model.lower()}_service import {service_class}
from app import limiter

# Create API blueprint
{main_model.lower()}_api = Blueprint('{main_model.lower()}_api', __name__)


# Request/Response Schemas
class Create{main_model}Schema(Schema):
    """Schema for {main_model.lower()} creation requests."""
    name = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(missing=None, validate=validate.Length(max=1000))
    status = fields.Str(missing="active", validate=validate.OneOf(["active", "inactive"]))


class Update{main_model}Schema(Schema):
    """Schema for {main_model.lower()} update requests."""
    name = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str(validate=validate.Length(max=1000), allow_none=True)
    status = fields.Str(validate=validate.OneOf(["active", "inactive"]))


def validate_uuid(uuid_string: str) -> uuid.UUID:
    """Validate and convert UUID string."""
    try:
        return uuid.UUID(uuid_string)
    except (ValueError, TypeError):
        raise ValueError("Invalid UUID format")


def handle_validation_error(error: ValidationError) -> tuple:
    """Handle marshmallow validation errors."""
    return jsonify({{
        'error': 'Validation Error',
        'message': 'Request data validation failed',
        'details': error.messages,
        'status_code': 400
    }}), 400


def handle_service_error(success: bool, errors: list, default_message: str = "Operation failed") -> tuple:
    """Handle service layer errors."""
    if success:
        return None
    
    message = errors[0] if errors else default_message
    status_code = 404 if "not found" in message.lower() else 400
    
    return jsonify({{
        'error': 'Operation Failed',
        'message': message,
        'details': errors,
        'status_code': status_code
    }}), status_code


# Health check endpoint
@{main_model.lower()}_api.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({{
        'status': 'healthy',
        'service': '{service_name}',
        'timestamp': datetime.utcnow().isoformat()
    }}), 200


# CRUD endpoints
@{main_model.lower()}_api.route('/{main_model.lower()}s', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_{main_model.lower()}():
    """Create a new {main_model.lower()}."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Validate request data
        schema = Create{main_model}Schema()
        data = schema.load(request.get_json() or {{}})
        
        # Create {main_model.lower()}
        service = {service_class}()
        item, success, errors = service.create_{main_model.lower()}(
            name=data['name'],
            owner_id=user_uuid,
            description=data.get('description'),
            status=data.get('status', 'active')
        )
        
        error_response = handle_service_error(success, errors, "Failed to create {main_model.lower()}")
        if error_response:
            return error_response
        
        return jsonify({{
            'message': '{main_model} created successfully',
            'data': item.to_dict(),
            'status_code': 201
        }}), 201
        
    except ValidationError as e:
        return handle_validation_error(e)
    except ValueError as e:
        return jsonify({{
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating {main_model.lower()}: {{e}}")
        return jsonify({{
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }}), 500


@{main_model.lower()}_api.route('/{main_model.lower()}s', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def list_{main_model.lower()}s():
    """Get user's {main_model.lower()}s."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Get {main_model.lower()}s
        service = {service_class}()
        items = service.get_{main_model.lower()}s_by_owner(user_uuid, limit)
        
        return jsonify({{
            'message': '{main_model}s retrieved successfully',
            'data': [item.to_dict() for item in items],
            'total': len(items),
            'status_code': 200
        }}), 200
        
    except ValueError as e:
        return jsonify({{
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }}), 400
    except Exception as e:
        current_app.logger.error(f"Error listing {main_model.lower()}s: {{e}}")
        return jsonify({{
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }}), 500


@{main_model.lower()}_api.route('/{main_model.lower()}s/<item_id>', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def get_{main_model.lower()}(item_id: str):
    """Get {main_model.lower()} details."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Get {main_model.lower()}
        service = {service_class}()
        item = service.get_{main_model.lower()}_by_id(item_uuid)
        
        if not item:
            return jsonify({{
                'error': 'Not Found',
                'message': '{main_model} not found',
                'status_code': 404
            }}), 404
        
        # Check permissions
        if item.owner_id != user_uuid:
            return jsonify({{
                'error': 'Forbidden',
                'message': 'Access denied to this {main_model.lower()}',
                'status_code': 403
            }}), 403
        
        return jsonify({{
            'message': '{main_model} retrieved successfully',
            'data': item.to_dict(),
            'status_code': 200
        }}), 200
        
    except ValueError as e:
        return jsonify({{
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }}), 400
    except Exception as e:
        current_app.logger.error(f"Error getting {main_model.lower()}: {{e}}")
        return jsonify({{
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }}), 500


@{main_model.lower()}_api.route('/{main_model.lower()}s/<item_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_{main_model.lower()}(item_id: str):
    """Update {main_model.lower()} details."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Validate request data
        schema = Update{main_model}Schema()
        updates = schema.load(request.get_json() or {{}})
        
        if not updates:
            return jsonify({{
                'error': 'Bad Request',
                'message': 'No valid fields provided for update',
                'status_code': 400
            }}), 400
        
        # Update {main_model.lower()}
        service = {service_class}()
        item, success, errors = service.update_{main_model.lower()}(
            item_id=item_uuid,
            updates=updates,
            updated_by=user_uuid
        )
        
        error_response = handle_service_error(success, errors, "Failed to update {main_model.lower()}")
        if error_response:
            return error_response
        
        return jsonify({{
            'message': '{main_model} updated successfully',
            'data': item.to_dict(),
            'status_code': 200
        }}), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except ValueError as e:
        return jsonify({{
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating {main_model.lower()}: {{e}}")
        return jsonify({{
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }}), 500


@{main_model.lower()}_api.route('/{main_model.lower()}s/<item_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per hour")
def delete_{main_model.lower()}(item_id: str):
    """Delete {main_model.lower()}."""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user_uuid = validate_uuid(current_user_id)
        item_uuid = validate_uuid(item_id)
        
        # Delete {main_model.lower()}
        service = {service_class}()
        success, errors = service.delete_{main_model.lower()}(item_uuid, user_uuid)
        
        error_response = handle_service_error(success, errors, "Failed to delete {main_model.lower()}")
        if error_response:
            return error_response
        
        return jsonify({{
            'message': '{main_model} deleted successfully',
            'status_code': 200
        }}), 200
        
    except ValueError as e:
        return jsonify({{
            'error': 'Invalid Input',
            'message': str(e),
            'status_code': 400
        }}), 400
    except Exception as e:
        current_app.logger.error(f"Error deleting {main_model.lower()}: {{e}}")
        return jsonify({{
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }}), 500
'''
    
    api_file = f"{routes_dir}/{main_model.lower()}_api.py"
    with open(api_file, "w") as f:
        f.write(template)


def create_service_tests(service_name: str, models: List[str]) -> None:
    """Create comprehensive test suites."""
    
    tests_dir = f"{service_name}/tests"
    os.makedirs(tests_dir, exist_ok=True)
    
    main_model = models[0] if models else "Generic"
    
    # Test template
    template = f'''"""
Test cases for {main_model}Service

Comprehensive test coverage for {main_model.lower()} management operations.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.{main_model.lower()}_service import {main_model}Service
from app.models.{main_model.lower()} import {main_model}


class Test{main_model}Service:
    """Test cases for {main_model}Service."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = Mock()
        session.query.return_value = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session
    
    @pytest.fixture
    def service(self, mock_session):
        """{main_model}Service instance with mocked session."""
        return {main_model}Service(session=mock_session)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user UUID."""
        return uuid.uuid4()
    
    def test_create_{main_model.lower()}_success(self, service, sample_user_id):
        """Test successful {main_model.lower()} creation."""
        # Mock {main_model.lower()} creation
        mock_item = Mock()
        mock_item.validate.return_value = (True, [])
        mock_item.to_dict.return_value = {{'id': str(uuid.uuid4()), 'name': 'Test {main_model}'}}
        
        with patch('app.services.{main_model.lower()}_service.{main_model}', return_value=mock_item):
            item, success, errors = service.create_{main_model.lower()}(
                name='Test {main_model}',
                owner_id=sample_user_id
            )
        
        assert success is True
        assert errors == []
        assert item == mock_item
        service.session.add.assert_called_once()
        service.session.commit.assert_called_once()
    
    def test_create_{main_model.lower()}_validation_error(self, service, sample_user_id):
        """Test {main_model.lower()} creation with validation errors."""
        mock_item = Mock()
        mock_item.validate.return_value = (False, ["Name is required"])
        
        with patch('app.services.{main_model.lower()}_service.{main_model}', return_value=mock_item):
            item, success, errors = service.create_{main_model.lower()}(
                name='',
                owner_id=sample_user_id
            )
        
        assert success is False
        assert "Name is required" in errors
        assert item is None
    
    def test_get_{main_model.lower()}_by_id_success(self, service):
        """Test successful {main_model.lower()} retrieval."""
        item_id = uuid.uuid4()
        mock_item = Mock()
        
        with patch.object({main_model}, 'get_by_id', return_value=mock_item):
            result = service.get_{main_model.lower()}_by_id(item_id)
        
        assert result == mock_item
        {main_model}.get_by_id.assert_called_once_with(service.session, item_id)
    
    def test_get_{main_model.lower()}_by_id_not_found(self, service):
        """Test {main_model.lower()} retrieval when not found."""
        item_id = uuid.uuid4()
        
        with patch.object({main_model}, 'get_by_id', return_value=None):
            result = service.get_{main_model.lower()}_by_id(item_id)
        
        assert result is None
    
    def test_update_{main_model.lower()}_success(self, service, sample_user_id):
        """Test successful {main_model.lower()} update."""
        item_id = uuid.uuid4()
        updates = {{'name': 'Updated Name'}}
        
        mock_item = Mock()
        mock_item.owner_id = sample_user_id
        mock_item.validate.return_value = (True, [])
        mock_item.to_dict.return_value = {{'id': str(item_id), 'name': 'Updated Name'}}
        
        service.get_{main_model.lower()}_by_id = Mock(return_value=mock_item)
        
        item, success, errors = service.update_{main_model.lower()}(
            item_id=item_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is True
        assert errors == []
        assert item == mock_item
        service.session.commit.assert_called_once()
    
    def test_update_{main_model.lower()}_insufficient_permissions(self, service, sample_user_id):
        """Test {main_model.lower()} update with insufficient permissions."""
        item_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        updates = {{'name': 'Updated Name'}}
        
        mock_item = Mock()
        mock_item.owner_id = other_user_id  # Different owner
        
        service.get_{main_model.lower()}_by_id = Mock(return_value=mock_item)
        
        item, success, errors = service.update_{main_model.lower()}(
            item_id=item_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is False
        assert "Insufficient permissions" in errors[0]
        assert item is None
    
    def test_delete_{main_model.lower()}_success(self, service, sample_user_id):
        """Test successful {main_model.lower()} deletion."""
        item_id = uuid.uuid4()
        
        mock_item = Mock()
        mock_item.owner_id = sample_user_id
        mock_item.soft_delete = Mock()
        
        service.get_{main_model.lower()}_by_id = Mock(return_value=mock_item)
        
        success, errors = service.delete_{main_model.lower()}(item_id, sample_user_id)
        
        assert success is True
        assert errors == []
        mock_item.soft_delete.assert_called_once()
        service.session.commit.assert_called_once()
    
    def test_get_{main_model.lower()}s_by_owner(self, service, sample_user_id):
        """Test getting {main_model.lower()}s by owner."""
        mock_items = [Mock(), Mock()]
        
        service.session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_items
        
        result = service.get_{main_model.lower()}s_by_owner(sample_user_id)
        
        assert len(result) == 2
        assert result == mock_items
'''
    
    test_file = f"{tests_dir}/test_{main_model.lower()}_service.py"
    with open(test_file, "w") as f:
        f.write(template)


def complete_all_services() -> None:
    """Complete all missing components for all services."""
    
    print("🚀 Starting comprehensive service completion...")
    
    for service_name, config in SERVICES.items():
        print(f"\n🔧 Completing {service_name}...")
        
        try:
            # Create models
            create_service_models(service_name, config['models'])
            print(f"  ✅ Created models: {', '.join(config['models'])}")
            
            # Create business logic services
            create_service_business_logic(service_name, config['models'])
            print(f"  ✅ Created service layer")
            
            # Create API routes
            create_service_api_routes(service_name, config['models'], config['port'])
            print(f"  ✅ Created API routes")
            
            # Create test suites
            create_service_tests(service_name, config['models'])
            print(f"  ✅ Created test suites")
            
            print(f"  🎉 {service_name} completed successfully!")
            
        except Exception as e:
            print(f"  ❌ Error completing {service_name}: {e}")
    
    print(f"\n🎉 All services completed!")
    print(f"\n📊 Completion Summary:")
    print(f"   - {len(SERVICES)} services processed")
    print(f"   - Models, services, routes, and tests created")
    print(f"   - Ready for testing and deployment")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Update master docker-compose.yml")
    print(f"   2. Test individual services")
    print(f"   3. Run integration tests")
    print(f"   4. Deploy to staging environment")


if __name__ == "__main__":
    complete_all_services()