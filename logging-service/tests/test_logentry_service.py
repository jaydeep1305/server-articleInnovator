"""
Test cases for LogEntryService

Comprehensive test coverage for logentry management operations.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.logentry_service import LogEntryService
from app.models.logentry import LogEntry


class TestLogEntryService:
    """Test cases for LogEntryService."""
    
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
        """LogEntryService instance with mocked session."""
        return LogEntryService(session=mock_session)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user UUID."""
        return uuid.uuid4()
    
    def test_create_logentry_success(self, service, sample_user_id):
        """Test successful logentry creation."""
        # Mock logentry creation
        mock_item = Mock()
        mock_item.validate.return_value = (True, [])
        mock_item.to_dict.return_value = {'id': str(uuid.uuid4()), 'name': 'Test LogEntry'}
        
        with patch('app.services.logentry_service.LogEntry', return_value=mock_item):
            item, success, errors = service.create_logentry(
                name='Test LogEntry',
                owner_id=sample_user_id
            )
        
        assert success is True
        assert errors == []
        assert item == mock_item
        service.session.add.assert_called_once()
        service.session.commit.assert_called_once()
    
    def test_create_logentry_validation_error(self, service, sample_user_id):
        """Test logentry creation with validation errors."""
        mock_item = Mock()
        mock_item.validate.return_value = (False, ["Name is required"])
        
        with patch('app.services.logentry_service.LogEntry', return_value=mock_item):
            item, success, errors = service.create_logentry(
                name='',
                owner_id=sample_user_id
            )
        
        assert success is False
        assert "Name is required" in errors
        assert item is None
    
    def test_get_logentry_by_id_success(self, service):
        """Test successful logentry retrieval."""
        item_id = uuid.uuid4()
        mock_item = Mock()
        
        with patch.object(LogEntry, 'get_by_id', return_value=mock_item):
            result = service.get_logentry_by_id(item_id)
        
        assert result == mock_item
        LogEntry.get_by_id.assert_called_once_with(service.session, item_id)
    
    def test_get_logentry_by_id_not_found(self, service):
        """Test logentry retrieval when not found."""
        item_id = uuid.uuid4()
        
        with patch.object(LogEntry, 'get_by_id', return_value=None):
            result = service.get_logentry_by_id(item_id)
        
        assert result is None
    
    def test_update_logentry_success(self, service, sample_user_id):
        """Test successful logentry update."""
        item_id = uuid.uuid4()
        updates = {'name': 'Updated Name'}
        
        mock_item = Mock()
        mock_item.owner_id = sample_user_id
        mock_item.validate.return_value = (True, [])
        mock_item.to_dict.return_value = {'id': str(item_id), 'name': 'Updated Name'}
        
        service.get_logentry_by_id = Mock(return_value=mock_item)
        
        item, success, errors = service.update_logentry(
            item_id=item_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is True
        assert errors == []
        assert item == mock_item
        service.session.commit.assert_called_once()
    
    def test_update_logentry_insufficient_permissions(self, service, sample_user_id):
        """Test logentry update with insufficient permissions."""
        item_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        updates = {'name': 'Updated Name'}
        
        mock_item = Mock()
        mock_item.owner_id = other_user_id  # Different owner
        
        service.get_logentry_by_id = Mock(return_value=mock_item)
        
        item, success, errors = service.update_logentry(
            item_id=item_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is False
        assert "Insufficient permissions" in errors[0]
        assert item is None
    
    def test_delete_logentry_success(self, service, sample_user_id):
        """Test successful logentry deletion."""
        item_id = uuid.uuid4()
        
        mock_item = Mock()
        mock_item.owner_id = sample_user_id
        mock_item.soft_delete = Mock()
        
        service.get_logentry_by_id = Mock(return_value=mock_item)
        
        success, errors = service.delete_logentry(item_id, sample_user_id)
        
        assert success is True
        assert errors == []
        mock_item.soft_delete.assert_called_once()
        service.session.commit.assert_called_once()
    
    def test_get_logentrys_by_owner(self, service, sample_user_id):
        """Test getting logentrys by owner."""
        mock_items = [Mock(), Mock()]
        
        service.session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_items
        
        result = service.get_logentrys_by_owner(sample_user_id)
        
        assert len(result) == 2
        assert result == mock_items
