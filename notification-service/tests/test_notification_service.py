"""
Test cases for NotificationService

Comprehensive test coverage for notification management operations.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.notification_service import NotificationService
from app.models.notification import Notification


class TestNotificationService:
    """Test cases for NotificationService."""
    
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
        """NotificationService instance with mocked session."""
        return NotificationService(session=mock_session)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user UUID."""
        return uuid.uuid4()
    
    def test_create_notification_success(self, service, sample_user_id):
        """Test successful notification creation."""
        # Mock notification creation
        mock_item = Mock()
        mock_item.validate.return_value = (True, [])
        mock_item.to_dict.return_value = {'id': str(uuid.uuid4()), 'name': 'Test Notification'}
        
        with patch('app.services.notification_service.Notification', return_value=mock_item):
            item, success, errors = service.create_notification(
                name='Test Notification',
                owner_id=sample_user_id
            )
        
        assert success is True
        assert errors == []
        assert item == mock_item
        service.session.add.assert_called_once()
        service.session.commit.assert_called_once()
    
    def test_create_notification_validation_error(self, service, sample_user_id):
        """Test notification creation with validation errors."""
        mock_item = Mock()
        mock_item.validate.return_value = (False, ["Name is required"])
        
        with patch('app.services.notification_service.Notification', return_value=mock_item):
            item, success, errors = service.create_notification(
                name='',
                owner_id=sample_user_id
            )
        
        assert success is False
        assert "Name is required" in errors
        assert item is None
    
    def test_get_notification_by_id_success(self, service):
        """Test successful notification retrieval."""
        item_id = uuid.uuid4()
        mock_item = Mock()
        
        with patch.object(Notification, 'get_by_id', return_value=mock_item):
            result = service.get_notification_by_id(item_id)
        
        assert result == mock_item
        Notification.get_by_id.assert_called_once_with(service.session, item_id)
    
    def test_get_notification_by_id_not_found(self, service):
        """Test notification retrieval when not found."""
        item_id = uuid.uuid4()
        
        with patch.object(Notification, 'get_by_id', return_value=None):
            result = service.get_notification_by_id(item_id)
        
        assert result is None
    
    def test_update_notification_success(self, service, sample_user_id):
        """Test successful notification update."""
        item_id = uuid.uuid4()
        updates = {'name': 'Updated Name'}
        
        mock_item = Mock()
        mock_item.owner_id = sample_user_id
        mock_item.validate.return_value = (True, [])
        mock_item.to_dict.return_value = {'id': str(item_id), 'name': 'Updated Name'}
        
        service.get_notification_by_id = Mock(return_value=mock_item)
        
        item, success, errors = service.update_notification(
            item_id=item_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is True
        assert errors == []
        assert item == mock_item
        service.session.commit.assert_called_once()
    
    def test_update_notification_insufficient_permissions(self, service, sample_user_id):
        """Test notification update with insufficient permissions."""
        item_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        updates = {'name': 'Updated Name'}
        
        mock_item = Mock()
        mock_item.owner_id = other_user_id  # Different owner
        
        service.get_notification_by_id = Mock(return_value=mock_item)
        
        item, success, errors = service.update_notification(
            item_id=item_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is False
        assert "Insufficient permissions" in errors[0]
        assert item is None
    
    def test_delete_notification_success(self, service, sample_user_id):
        """Test successful notification deletion."""
        item_id = uuid.uuid4()
        
        mock_item = Mock()
        mock_item.owner_id = sample_user_id
        mock_item.soft_delete = Mock()
        
        service.get_notification_by_id = Mock(return_value=mock_item)
        
        success, errors = service.delete_notification(item_id, sample_user_id)
        
        assert success is True
        assert errors == []
        mock_item.soft_delete.assert_called_once()
        service.session.commit.assert_called_once()
    
    def test_get_notifications_by_owner(self, service, sample_user_id):
        """Test getting notifications by owner."""
        mock_items = [Mock(), Mock()]
        
        service.session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_items
        
        result = service.get_notifications_by_owner(sample_user_id)
        
        assert len(result) == 2
        assert result == mock_items
