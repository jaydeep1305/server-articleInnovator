"""
Unit tests for UserService.

This module contains comprehensive tests for the UserService class
including user registration, authentication, and profile management.

Test Classes:
    TestUserService: Tests for UserService functionality
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.models.base import db
from app.models import User
from app.services import UserService


class TestUserService:
    """
    Test class for UserService functionality.
    
    This class tests all aspects of user management including
    registration, authentication, profile updates, and validation.
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """
        Set up test environment before each test method.
        
        Creates a test Flask application with in-memory database
        and initializes the UserService for testing.
        """
        # Create test application
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Initialize service
        self.user_service = UserService(db)
        
        # Test data
        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def teardown_method(self):
        """
        Clean up test environment after each test method.
        
        Removes database tables and application context.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_register_user_success(self):
        """
        Test successful user registration.
        
        Verifies that a new user can be registered with valid data
        and that the user is properly saved to the database.
        """
        # Act: Register a new user
        user = self.user_service.register(**self.valid_user_data)
        
        # Assert: User should be created successfully
        assert user is not None
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.is_active is True
        assert user.is_verified is False
        
        # Verify password is hashed
        assert user.password_hash != 'TestPass123'
        assert user.check_password('TestPass123') is True
    
    def test_register_duplicate_username(self):
        """
        Test registration with duplicate username.
        
        Verifies that registering a user with an existing username
        raises a ValueError.
        """
        # Arrange: Create a user first
        self.user_service.register(**self.valid_user_data)
        
        # Act & Assert: Try to register with same username
        with pytest.raises(ValueError, match="Username 'testuser' already exists"):
            duplicate_data = self.valid_user_data.copy()
            duplicate_data['email'] = 'different@example.com'
            self.user_service.register(**duplicate_data)
    
    def test_register_duplicate_email(self):
        """
        Test registration with duplicate email.
        
        Verifies that registering a user with an existing email
        raises a ValueError.
        """
        # Arrange: Create a user first
        self.user_service.register(**self.valid_user_data)
        
        # Act & Assert: Try to register with same email
        with pytest.raises(ValueError, match="Email 'test@example.com' already exists"):
            duplicate_data = self.valid_user_data.copy()
            duplicate_data['username'] = 'differentuser'
            self.user_service.register(**duplicate_data)
    
    def test_register_invalid_email(self):
        """
        Test registration with invalid email format.
        
        Verifies that invalid email formats are rejected during registration.
        """
        # Arrange: Invalid email data
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        # Act & Assert: Registration should fail
        with pytest.raises(ValueError, match="Invalid email format"):
            self.user_service.register(**invalid_data)
    
    def test_register_weak_password(self):
        """
        Test registration with weak password.
        
        Verifies that weak passwords are rejected during registration.
        """
        # Arrange: Weak password data
        weak_password_data = self.valid_user_data.copy()
        weak_password_data['password'] = 'weak'
        
        # Act & Assert: Registration should fail
        with pytest.raises(ValueError):
            self.user_service.register(**weak_password_data)
    
    def test_authenticate_valid_credentials(self):
        """
        Test authentication with valid credentials.
        
        Verifies that a user can authenticate with correct username/email
        and password.
        """
        # Arrange: Create a user
        created_user = self.user_service.register(**self.valid_user_data)
        
        # Act: Authenticate with username
        user_by_username = self.user_service.authenticate('testuser', 'TestPass123')
        
        # Act: Authenticate with email
        user_by_email = self.user_service.authenticate('test@example.com', 'TestPass123')
        
        # Assert: Both authentication methods should work
        assert user_by_username is not None
        assert user_by_username.id == created_user.id
        assert user_by_email is not None
        assert user_by_email.id == created_user.id
    
    def test_authenticate_invalid_credentials(self):
        """
        Test authentication with invalid credentials.
        
        Verifies that authentication fails with incorrect passwords
        or non-existent users.
        """
        # Arrange: Create a user
        self.user_service.register(**self.valid_user_data)
        
        # Act & Assert: Wrong password
        user_wrong_password = self.user_service.authenticate('testuser', 'WrongPassword')
        assert user_wrong_password is None
        
        # Act & Assert: Non-existent user
        user_not_found = self.user_service.authenticate('nonexistent', 'TestPass123')
        assert user_not_found is None
    
    def test_authenticate_inactive_user(self):
        """
        Test authentication with inactive user.
        
        Verifies that inactive users cannot authenticate even with
        correct credentials.
        """
        # Arrange: Create and deactivate a user
        user = self.user_service.register(**self.valid_user_data)
        self.user_service.deactivate_user(user.id)
        
        # Act: Try to authenticate
        authenticated_user = self.user_service.authenticate('testuser', 'TestPass123')
        
        # Assert: Authentication should fail
        assert authenticated_user is None
    
    def test_get_by_username(self):
        """
        Test retrieving user by username.
        
        Verifies that users can be retrieved by username
        with case-insensitive matching.
        """
        # Arrange: Create a user
        created_user = self.user_service.register(**self.valid_user_data)
        
        # Act: Get user by username (different cases)
        user_lower = self.user_service.get_by_username('testuser')
        user_upper = self.user_service.get_by_username('TESTUSER')
        user_mixed = self.user_service.get_by_username('TestUser')
        
        # Assert: All should return the same user
        assert user_lower is not None
        assert user_lower.id == created_user.id
        assert user_upper is not None
        assert user_upper.id == created_user.id
        assert user_mixed is not None
        assert user_mixed.id == created_user.id
    
    def test_get_by_email(self):
        """
        Test retrieving user by email.
        
        Verifies that users can be retrieved by email
        with case-insensitive matching.
        """
        # Arrange: Create a user
        created_user = self.user_service.register(**self.valid_user_data)
        
        # Act: Get user by email (different cases)
        user_lower = self.user_service.get_by_email('test@example.com')
        user_upper = self.user_service.get_by_email('TEST@EXAMPLE.COM')
        user_mixed = self.user_service.get_by_email('Test@Example.Com')
        
        # Assert: All should return the same user
        assert user_lower is not None
        assert user_lower.id == created_user.id
        assert user_upper is not None
        assert user_upper.id == created_user.id
        assert user_mixed is not None
        assert user_mixed.id == created_user.id
    
    def test_activate_user(self):
        """
        Test user account activation.
        
        Verifies that inactive users can be activated and
        their status is updated correctly.
        """
        # Arrange: Create and deactivate a user
        user = self.user_service.register(**self.valid_user_data)
        self.user_service.deactivate_user(user.id)
        
        # Act: Activate the user
        activated_user = self.user_service.activate_user(user.id)
        
        # Assert: User should be active
        assert activated_user is not None
        assert activated_user.is_active is True
    
    def test_deactivate_user(self):
        """
        Test user account deactivation.
        
        Verifies that active users can be deactivated and
        their status is updated correctly.
        """
        # Arrange: Create a user
        user = self.user_service.register(**self.valid_user_data)
        
        # Act: Deactivate the user
        deactivated_user = self.user_service.deactivate_user(user.id)
        
        # Assert: User should be inactive
        assert deactivated_user is not None
        assert deactivated_user.is_active is False
    
    def test_verify_email(self):
        """
        Test email verification.
        
        Verifies that user email can be marked as verified
        and status is updated correctly.
        """
        # Arrange: Create a user
        user = self.user_service.register(**self.valid_user_data)
        assert user.is_verified is False
        
        # Act: Verify email
        verified_user = self.user_service.verify_email(user.id)
        
        # Assert: User email should be verified
        assert verified_user is not None
        assert verified_user.is_verified is True
    
    def test_update_password_success(self):
        """
        Test successful password update.
        
        Verifies that users can update their password with
        correct current password verification.
        """
        # Arrange: Create a user
        user = self.user_service.register(**self.valid_user_data)
        
        # Act: Update password
        success = self.user_service.update_password(
            user.id, 'TestPass123', 'NewPass456'
        )
        
        # Assert: Password should be updated
        assert success is True
        
        # Verify new password works
        updated_user = self.user_service.get_by_id(user.id)
        assert updated_user.check_password('NewPass456') is True
        assert updated_user.check_password('TestPass123') is False
    
    def test_update_password_wrong_current(self):
        """
        Test password update with wrong current password.
        
        Verifies that password update fails when the current
        password is incorrect.
        """
        # Arrange: Create a user
        user = self.user_service.register(**self.valid_user_data)
        
        # Act & Assert: Update with wrong current password
        with pytest.raises(ValueError, match="Current password is incorrect"):
            self.user_service.update_password(
                user.id, 'WrongPassword', 'NewPass456'
            )
    
    def test_search_users(self):
        """
        Test user search functionality.
        
        Verifies that users can be searched by username, email,
        first name, and last name.
        """
        # Arrange: Create multiple users
        users_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 
             'password': 'Pass123', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 
             'password': 'Pass123', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'bob_johnson', 'email': 'bob@example.com', 
             'password': 'Pass123', 'first_name': 'Bob', 'last_name': 'Johnson'}
        ]
        
        for user_data in users_data:
            self.user_service.register(**user_data)
        
        # Act: Search by different criteria
        search_john = self.user_service.search_users('john')
        search_jane_email = self.user_service.search_users('jane@')
        search_smith = self.user_service.search_users('smith')
        
        # Assert: Search results should be correct
        assert len(search_john) >= 1  # Should find John and Johnson
        assert len(search_jane_email) == 1
        assert search_jane_email[0].username == 'jane_smith'
        assert len(search_smith) == 1
        assert search_smith[0].last_name == 'Smith'
    
    def test_get_user_statistics(self):
        """
        Test user statistics retrieval.
        
        Verifies that user statistics are calculated correctly
        including article and comment counts.
        """
        # Arrange: Create a user
        user = self.user_service.register(**self.valid_user_data)
        
        # Act: Get statistics
        stats = self.user_service.get_user_statistics(user.id)
        
        # Assert: Statistics should be returned
        assert isinstance(stats, dict)
        assert 'total_articles' in stats
        assert 'total_comments' in stats
        assert 'total_article_views' in stats
        assert stats['total_articles'] == 0  # New user has no articles
        assert stats['total_comments'] == 0   # New user has no comments
    
    def test_paginate_users(self):
        """
        Test user pagination functionality.
        
        Verifies that users can be paginated correctly with
        proper page information.
        """
        # Arrange: Create multiple users
        for i in range(5):
            user_data = self.valid_user_data.copy()
            user_data['username'] = f'user{i}'
            user_data['email'] = f'user{i}@example.com'
            self.user_service.register(**user_data)
        
        # Act: Get paginated users
        result = self.user_service.paginate_users(page=1, per_page=3)
        
        # Assert: Pagination should work correctly
        assert result.total == 5
        assert len(result.items) == 3
        assert result.page == 1
        assert result.per_page == 3
        assert result.pages == 2
        assert result.has_next is True
        assert result.has_prev is False
    
    @patch('app.models.base.db.session.commit')
    def test_register_database_error(self, mock_commit):
        """
        Test registration with database error.
        
        Verifies that database errors during registration
        are handled properly.
        """
        # Arrange: Mock database error
        mock_commit.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert: Registration should raise SQLAlchemyError
        with pytest.raises(SQLAlchemyError):
            self.user_service.register(**self.valid_user_data)
    
    def test_user_not_found_operations(self):
        """
        Test operations on non-existent users.
        
        Verifies that operations on non-existent users
        return appropriate None values.
        """
        # Act: Try operations on non-existent user
        user = self.user_service.get_by_id(999)
        activated = self.user_service.activate_user(999)
        deactivated = self.user_service.deactivate_user(999)
        verified = self.user_service.verify_email(999)
        
        # Assert: All should return None
        assert user is None
        assert activated is None
        assert deactivated is None
        assert verified is None
    
    def test_user_validation_edge_cases(self):
        """
        Test user validation with edge cases.
        
        Verifies that edge cases in user data validation
        are handled correctly.
        """
        # Test minimum username length
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            data = self.valid_user_data.copy()
            data['username'] = 'ab'
            self.user_service.register(**data)
        
        # Test maximum username length
        with pytest.raises(ValueError, match="Username must be less than 80 characters"):
            data = self.valid_user_data.copy()
            data['username'] = 'a' * 81
            self.user_service.register(**data)
        
        # Test invalid username characters
        with pytest.raises(ValueError, match="Username can only contain"):
            data = self.valid_user_data.copy()
            data['username'] = 'user@name'
            self.user_service.register(**data)