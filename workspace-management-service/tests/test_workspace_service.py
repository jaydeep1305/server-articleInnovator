"""
Test cases for WorkspaceService

This module contains comprehensive test cases for workspace management
business logic, covering all service methods, edge cases, and error conditions.

Author: AI Assistant
Date: 2024
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.workspace_service import WorkspaceService
from app.models.workspace import Workspace, WorkspaceRole, WorkspaceStatus


class TestWorkspaceService:
    """Test cases for WorkspaceService class."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = Mock()
        session.query.return_value = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.flush = Mock()
        return session
    
    @pytest.fixture
    def workspace_service(self, mock_session):
        """WorkspaceService instance with mocked session."""
        return WorkspaceService(session=mock_session)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user UUID for testing."""
        return uuid.uuid4()
    
    @pytest.fixture
    def sample_workspace_data(self):
        """Sample workspace data for testing."""
        return {
            'name': 'Test Workspace',
            'description': 'A test workspace for unit testing',
            'visibility': 'private',
            'max_members': 10,
            'storage_quota_gb': 5
        }
    
    # Test workspace creation
    def test_create_workspace_success(self, workspace_service, sample_user_id, sample_workspace_data):
        """Test successful workspace creation."""
        # Mock dependencies
        workspace_service.get_user_workspaces = Mock(return_value=[])
        workspace_service._ensure_unique_slug = Mock(return_value='test-workspace')
        
        # Mock workspace creation
        mock_workspace = Mock()
        mock_workspace.validate.return_value = (True, [])
        mock_workspace.to_dict.return_value = {'id': str(uuid.uuid4()), 'name': 'Test Workspace'}
        mock_workspace.add_member = Mock(return_value=True)
        
        with patch('app.services.workspace_service.Workspace', return_value=mock_workspace):
            workspace, success, errors = workspace_service.create_workspace(
                name=sample_workspace_data['name'],
                owner_id=sample_user_id,
                description=sample_workspace_data['description']
            )
        
        assert success is True
        assert errors == []
        assert workspace == mock_workspace
        workspace_service.session.add.assert_called_once()
        workspace_service.session.commit.assert_called_once()
    
    def test_create_workspace_exceeds_limit(self, workspace_service, sample_user_id, sample_workspace_data):
        """Test workspace creation when user exceeds limit."""
        # Mock user having maximum workspaces
        existing_workspaces = [Mock() for _ in range(10)]
        workspace_service.get_user_workspaces = Mock(return_value=existing_workspaces)
        
        workspace, success, errors = workspace_service.create_workspace(
            name=sample_workspace_data['name'],
            owner_id=sample_user_id,
            max_workspaces=10
        )
        
        assert success is False
        assert "maximum workspace limit" in errors[0]
        assert workspace is None
    
    def test_create_workspace_duplicate_name(self, workspace_service, sample_user_id, sample_workspace_data):
        """Test workspace creation with duplicate name."""
        # Mock no existing workspaces for limit check
        workspace_service.get_user_workspaces = Mock(return_value=[])
        
        # Mock existing workspace with same name
        mock_existing = Mock()
        workspace_service.session.query.return_value.filter.return_value.first.return_value = mock_existing
        
        workspace, success, errors = workspace_service.create_workspace(
            name=sample_workspace_data['name'],
            owner_id=sample_user_id
        )
        
        assert success is False
        assert "already exists" in errors[0]
        assert workspace is None
    
    def test_create_workspace_validation_error(self, workspace_service, sample_user_id):
        """Test workspace creation with validation errors."""
        workspace_service.get_user_workspaces = Mock(return_value=[])
        workspace_service.session.query.return_value.filter.return_value.first.return_value = None
        workspace_service._ensure_unique_slug = Mock(return_value='test-workspace')
        
        # Mock workspace with validation errors
        mock_workspace = Mock()
        mock_workspace.validate.return_value = (False, ["Name is required"])
        
        with patch('app.services.workspace_service.Workspace', return_value=mock_workspace):
            workspace, success, errors = workspace_service.create_workspace(
                name="",
                owner_id=sample_user_id
            )
        
        assert success is False
        assert "Name is required" in errors
        assert workspace is None
    
    # Test workspace retrieval
    def test_get_workspace_by_id_success(self, workspace_service):
        """Test successful workspace retrieval by ID."""
        workspace_id = uuid.uuid4()
        mock_workspace = Mock()
        
        with patch.object(Workspace, 'get_by_id', return_value=mock_workspace):
            result = workspace_service.get_workspace_by_id(workspace_id)
        
        assert result == mock_workspace
        Workspace.get_by_id.assert_called_once_with(workspace_service.session, workspace_id)
    
    def test_get_workspace_by_id_not_found(self, workspace_service):
        """Test workspace retrieval when not found."""
        workspace_id = uuid.uuid4()
        
        with patch.object(Workspace, 'get_by_id', return_value=None):
            result = workspace_service.get_workspace_by_id(workspace_id)
        
        assert result is None
    
    def test_get_workspace_by_slug_success(self, workspace_service):
        """Test successful workspace retrieval by slug."""
        slug = "test-workspace"
        mock_workspace = Mock()
        
        with patch.object(Workspace, 'find_by_slug', return_value=mock_workspace):
            result = workspace_service.get_workspace_by_slug(slug)
        
        assert result == mock_workspace
        Workspace.find_by_slug.assert_called_once_with(workspace_service.session, slug)
    
    # Test workspace updates
    def test_update_workspace_success(self, workspace_service, sample_user_id):
        """Test successful workspace update."""
        workspace_id = uuid.uuid4()
        updates = {'name': 'Updated Name', 'description': 'Updated description'}
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = WorkspaceRole.OWNER
        mock_workspace.validate.return_value = (True, [])
        mock_workspace.to_dict.return_value = {'id': str(workspace_id), 'name': 'Updated Name'}
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        workspace, success, errors = workspace_service.update_workspace(
            workspace_id=workspace_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is True
        assert errors == []
        assert workspace == mock_workspace
        workspace_service.session.commit.assert_called_once()
    
    def test_update_workspace_insufficient_permissions(self, workspace_service, sample_user_id):
        """Test workspace update with insufficient permissions."""
        workspace_id = uuid.uuid4()
        updates = {'name': 'Updated Name'}
        
        # Mock workspace with insufficient permissions
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = WorkspaceRole.MEMBER
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        workspace, success, errors = workspace_service.update_workspace(
            workspace_id=workspace_id,
            updates=updates,
            updated_by=sample_user_id
        )
        
        assert success is False
        assert "Insufficient permissions" in errors[0]
        assert workspace is None
    
    # Test member management
    def test_add_workspace_member_success(self, workspace_service, sample_user_id):
        """Test successful member addition."""
        workspace_id = uuid.uuid4()
        new_member_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = WorkspaceRole.OWNER
        mock_workspace.add_member.return_value = True
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.add_workspace_member(
            workspace_id=workspace_id,
            user_id=new_member_id,
            role=WorkspaceRole.MEMBER,
            invited_by=sample_user_id
        )
        
        assert success is True
        assert errors == []
        workspace_service.session.commit.assert_called_once()
    
    def test_add_workspace_member_insufficient_permissions(self, workspace_service, sample_user_id):
        """Test member addition with insufficient permissions."""
        workspace_id = uuid.uuid4()
        new_member_id = uuid.uuid4()
        
        # Mock workspace with insufficient permissions
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = WorkspaceRole.MEMBER
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.add_workspace_member(
            workspace_id=workspace_id,
            user_id=new_member_id,
            invited_by=sample_user_id
        )
        
        assert success is False
        assert "Insufficient permissions" in errors[0]
    
    def test_remove_workspace_member_success(self, workspace_service, sample_user_id):
        """Test successful member removal."""
        workspace_id = uuid.uuid4()
        member_to_remove = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.get_member_role.side_effect = [WorkspaceRole.OWNER, WorkspaceRole.MEMBER]
        mock_workspace.owner_id = sample_user_id
        mock_workspace.remove_member.return_value = True
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.remove_workspace_member(
            workspace_id=workspace_id,
            user_id=member_to_remove,
            removed_by=sample_user_id
        )
        
        assert success is True
        assert errors == []
        workspace_service.session.commit.assert_called_once()
    
    def test_remove_workspace_member_cannot_remove_owner(self, workspace_service, sample_user_id):
        """Test that workspace owner cannot remove themselves."""
        workspace_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.owner_id = sample_user_id
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.remove_workspace_member(
            workspace_id=workspace_id,
            user_id=sample_user_id,  # Owner trying to remove themselves
            removed_by=sample_user_id
        )
        
        assert success is False
        assert "cannot remove themselves" in errors[0]
    
    def test_update_member_role_success(self, workspace_service, sample_user_id):
        """Test successful member role update."""
        workspace_id = uuid.uuid4()
        member_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = WorkspaceRole.OWNER
        mock_workspace.owner_id = sample_user_id
        mock_workspace.update_member_role.return_value = True
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.update_member_role(
            workspace_id=workspace_id,
            user_id=member_id,
            new_role=WorkspaceRole.ADMIN,
            updated_by=sample_user_id
        )
        
        assert success is True
        assert errors == []
        workspace_service.session.commit.assert_called_once()
    
    def test_update_member_role_cannot_change_owner(self, workspace_service, sample_user_id):
        """Test that owner role cannot be changed."""
        workspace_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = WorkspaceRole.OWNER
        mock_workspace.owner_id = sample_user_id
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.update_member_role(
            workspace_id=workspace_id,
            user_id=sample_user_id,  # Trying to change owner role
            new_role=WorkspaceRole.ADMIN,
            updated_by=sample_user_id
        )
        
        assert success is False
        assert "Cannot change workspace owner role" in errors[0]
    
    # Test workspace archive/restore
    def test_archive_workspace_success(self, workspace_service, sample_user_id):
        """Test successful workspace archiving."""
        workspace_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.owner_id = sample_user_id
        mock_workspace.archive = Mock()
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.archive_workspace(workspace_id, sample_user_id)
        
        assert success is True
        assert errors == []
        mock_workspace.archive.assert_called_once()
        workspace_service.session.commit.assert_called_once()
    
    def test_archive_workspace_not_owner(self, workspace_service, sample_user_id):
        """Test workspace archiving by non-owner."""
        workspace_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.owner_id = other_user_id  # Different owner
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.archive_workspace(workspace_id, sample_user_id)
        
        assert success is False
        assert "Only workspace owner" in errors[0]
    
    def test_restore_workspace_success(self, workspace_service, sample_user_id):
        """Test successful workspace restoration."""
        workspace_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.owner_id = sample_user_id
        mock_workspace.restore = Mock()
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        success, errors = workspace_service.restore_workspace(workspace_id, sample_user_id)
        
        assert success is True
        assert errors == []
        mock_workspace.restore.assert_called_once()
        workspace_service.session.commit.assert_called_once()
    
    # Test permissions
    def test_check_workspace_permissions_success(self, workspace_service, sample_user_id):
        """Test successful permission check."""
        workspace_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = WorkspaceRole.ADMIN
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        result = workspace_service.check_workspace_permissions(
            workspace_id=workspace_id,
            user_id=sample_user_id,
            required_role=WorkspaceRole.MEMBER
        )
        
        assert result is True
    
    def test_check_workspace_permissions_insufficient(self, workspace_service, sample_user_id):
        """Test permission check with insufficient role."""
        workspace_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = WorkspaceRole.GUEST
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        result = workspace_service.check_workspace_permissions(
            workspace_id=workspace_id,
            user_id=sample_user_id,
            required_role=WorkspaceRole.ADMIN
        )
        
        assert result is False
    
    def test_check_workspace_permissions_not_member(self, workspace_service, sample_user_id):
        """Test permission check for non-member."""
        workspace_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.get_member_role.return_value = None  # Not a member
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        result = workspace_service.check_workspace_permissions(
            workspace_id=workspace_id,
            user_id=sample_user_id,
            required_role=WorkspaceRole.MEMBER
        )
        
        assert result is False
    
    # Test search functionality
    def test_search_workspaces_success(self, workspace_service, sample_user_id):
        """Test successful workspace search."""
        query = "test"
        mock_workspaces = [Mock(), Mock()]
        
        workspace_service.get_user_workspaces = Mock(return_value=mock_workspaces)
        workspace_service.session.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = mock_workspaces
        
        result = workspace_service.search_workspaces(
            query=query,
            user_id=sample_user_id,
            limit=20
        )
        
        assert len(result) == 2
    
    def test_search_workspaces_no_user_workspaces(self, workspace_service, sample_user_id):
        """Test workspace search when user has no workspaces."""
        query = "test"
        
        workspace_service.get_user_workspaces = Mock(return_value=[])
        
        result = workspace_service.search_workspaces(
            query=query,
            user_id=sample_user_id,
            limit=20
        )
        
        assert result == []
    
    # Test utility methods
    def test_ensure_unique_slug_no_collision(self, workspace_service):
        """Test slug generation with no collision."""
        base_slug = "test-workspace"
        workspace_service.session.query.return_value.filter.return_value.first.return_value = None
        
        result = workspace_service._ensure_unique_slug(base_slug)
        
        assert result == base_slug
    
    def test_ensure_unique_slug_with_collision(self, workspace_service):
        """Test slug generation with collision."""
        base_slug = "test-workspace"
        
        # Mock collision on first attempt, then success
        workspace_service.session.query.return_value.filter.return_value.first.side_effect = [
            Mock(),  # Collision
            None     # Success
        ]
        
        result = workspace_service._ensure_unique_slug(base_slug)
        
        assert result == "test-workspace-1"
    
    # Test storage management
    def test_update_workspace_storage_success(self, workspace_service):
        """Test successful storage update."""
        workspace_id = uuid.uuid4()
        
        # Mock workspace
        mock_workspace = Mock()
        mock_workspace.update_storage_usage = Mock()
        
        workspace_service.get_workspace_by_id = Mock(return_value=mock_workspace)
        
        result = workspace_service.update_workspace_storage(workspace_id, 100)
        
        assert result is True
        mock_workspace.update_storage_usage.assert_called_once_with(workspace_service.session, 100)
        workspace_service.session.commit.assert_called_once()
    
    def test_update_workspace_storage_not_found(self, workspace_service):
        """Test storage update for non-existent workspace."""
        workspace_id = uuid.uuid4()
        
        workspace_service.get_workspace_by_id = Mock(return_value=None)
        
        result = workspace_service.update_workspace_storage(workspace_id, 100)
        
        assert result is False
    
    # Test error handling
    def test_create_workspace_database_error(self, workspace_service, sample_user_id, sample_workspace_data):
        """Test workspace creation with database error."""
        from sqlalchemy.exc import IntegrityError
        
        workspace_service.get_user_workspaces = Mock(return_value=[])
        workspace_service.session.query.return_value.filter.return_value.first.return_value = None
        workspace_service._ensure_unique_slug = Mock(return_value='test-workspace')
        
        # Mock workspace that causes database error
        mock_workspace = Mock()
        mock_workspace.validate.return_value = (True, [])
        workspace_service.session.add.side_effect = IntegrityError("", "", "")
        
        with patch('app.services.workspace_service.Workspace', return_value=mock_workspace):
            workspace, success, errors = workspace_service.create_workspace(
                name=sample_workspace_data['name'],
                owner_id=sample_user_id
            )
        
        assert success is False
        assert "constraint violation" in errors[0]
        workspace_service.session.rollback.assert_called_once()
    
    def test_get_user_workspaces_integration(self, workspace_service, sample_user_id):
        """Test getting user workspaces with integration behavior."""
        # Mock owned workspaces
        owned_workspaces = [Mock()]
        
        # Mock member workspaces query
        mock_subquery = Mock()
        workspace_service.session.query.return_value.filter.return_value.subquery.return_value = mock_subquery
        workspace_service.session.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        
        with patch.object(Workspace, 'find_by_owner', return_value=owned_workspaces):
            result = workspace_service.get_user_workspaces(sample_user_id)
        
        assert len(result) == 1
        assert result[0] in owned_workspaces