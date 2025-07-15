"""
Test cases for ScrapingJobService

Comprehensive test coverage for scrapingjob management operations.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.scrapingjob_service import ScrapingJobService
from app.models.scrapingjob import ScrapingJob


class TestScrapingJobService:
    """Test cases for ScrapingJobService."""
    
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
        """ScrapingJobService instance with mocked session."""
        return ScrapingJobService(session=mock_session)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user UUID."""
        return uuid.uuid4()
    
    def test_create_scrapingjob_success(self, service, sample_user_id):
        """Test successful scrapingjob creation."""
        # Mock scrapingjob creation
        mock_item = Mock()
        mock_item.validate.return_value = (True, [])
        mock_item.to_dict.return_value = {'id': str(uuid.uuid4()), 'name': 'Test ScrapingJob'}
        
        with patch('app.services.scrapingjob_service.ScrapingJob', return_value=mock_item):
            item, success, errors = service.create_scrapingjob(
                name='Test ScrapingJob',
                owner_id=sample_user_id
            )
        
        assert success is True
        assert errors == []
        assert item == mock_item
        service.session.add.assert_called_once()
        service.session.commit.assert_called_once()
    
    def test_create_scrapingjob_validation_error(self, service, sample_user_id):
        """Test scrapingjob creation with validation errors."""
        mock_item = Mock()
        mock_item.validate.return_value = (False, ["Name is required"])
        
        with patch('app.services.scrapingjob_service.ScrapingJob', return_value=mock_item):
            item, success, errors = service.create_scrapingjob(
                name='',
                owner_id=sample_user_id
            )
        
        assert success is False
        assert "Name is required" in errors
        assert item is None
    
    def test_get_scrapingjob_by_id_success(self, service):
        """Test successful scrapingjob retrieval."""
        item_id = uuid.uuid4()
        mock_item = Mock()
        
        with patch.object(ScrapingJob, 'get_by_id', return_value=mock_item):
            result = service.get_scrapingjob_by_id(item_id)
        
        assert result == mock_item
        ScrapingJob.get_by_id.assert_called_once_with(service.session, item_id)
    
    def test_get_scrapingjob_by_id_not_found(self, service):
        """Test scrapingjob retrieval when not found."""
        item_id = uuid.uuid4()
        
        with patch.object(ScrapingJob, 'get_by_id', return_value=None):
            result = service.get_scrapingjob_by_id(item_id)
        
        assert result is None
    
    def test_update_scrapingjob_success(self, service, sample_user_id):
        """Test successful scrapingjob update."""
        item_id = uuid.uuid4()
        updates = {'name': 'Updated Name'}
        
        mock_item = Mock()
        mock_item.owner_id = sample_user_id
        mock_item.validate.return_value = (True, [])
        mock_item.to_dict.return_value = {'id': str(item_id), 'name': 'Updated Name'}
        
        service.get_scrapingjob_by_id = Mock(return_value=mock_item)
        
        item, success, errors = service.update_scrapingjob(
            item_id=item_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is True
        assert errors == []
        assert item == mock_item
        service.session.commit.assert_called_once()
    
    def test_update_scrapingjob_insufficient_permissions(self, service, sample_user_id):
        """Test scrapingjob update with insufficient permissions."""
        item_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        updates = {'name': 'Updated Name'}
        
        mock_item = Mock()
        mock_item.owner_id = other_user_id  # Different owner
        
        service.get_scrapingjob_by_id = Mock(return_value=mock_item)
        
        item, success, errors = service.update_scrapingjob(
            item_id=item_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is False
        assert "Insufficient permissions" in errors[0]
        assert item is None
    
    def test_delete_scrapingjob_success(self, service, sample_user_id):
        """Test successful scrapingjob deletion."""
        item_id = uuid.uuid4()
        
        mock_item = Mock()
        mock_item.owner_id = sample_user_id
        mock_item.soft_delete = Mock()
        
        service.get_scrapingjob_by_id = Mock(return_value=mock_item)
        
        success, errors = service.delete_scrapingjob(item_id, sample_user_id)
        
        assert success is True
        assert errors == []
        mock_item.soft_delete.assert_called_once()
        service.session.commit.assert_called_once()
    
    def test_get_scrapingjobs_by_owner(self, service, sample_user_id):
        """Test getting scrapingjobs by owner."""
        mock_items = [Mock(), Mock()]
        
        service.session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_items
        
        result = service.get_scrapingjobs_by_owner(sample_user_id)
        
        assert len(result) == 2
        assert result == mock_items
