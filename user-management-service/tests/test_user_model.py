"""
Unit tests for User model.

This module contains comprehensive tests for the User model including
validation, security features, password handling, and business logic.
Tests cover edge cases and ensure data integrity with cognitive test patterns.

Author: AI Assistant
Date: 2024
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import User, Role, Permission
from config import TestingConfig


class TestUserModel:
    """Test class for User model with comprehensive coverage."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test environment before each test method."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Test data
        self.valid_user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        yield
        
        # Cleanup after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_creation_with_valid_data(self):
        """Test creating a user with valid data."""
        user = User(**self.valid_user_data)
        
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('SecurePass123!')
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_admin is False
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_creation_with_minimal_data(self):
        """Test creating a user with only required fields."""
        minimal_data = {
            'email': 'minimal@example.com',
            'username': 'minimal',
            'password': 'Password123!'
        }
        
        user = User(**minimal_data)
        
        assert user.email == 'minimal@example.com'
        assert user.username == 'minimal'
        assert user.first_name is None
        assert user.last_name is None
        assert user.check_password('Password123!')
    
    def test_email_normalization(self):
        """Test that email addresses are normalized to lowercase."""
        data = self.valid_user_data.copy()
        data['email'] = 'TEST@EXAMPLE.COM'
        
        user = User(**data)
        assert user.email == 'test@example.com'
    
    def test_username_normalization(self):
        """Test that usernames are normalized to lowercase."""
        data = self.valid_user_data.copy()
        data['username'] = 'TestUser'
        
        user = User(**data)
        assert user.username == 'testuser'
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        user = User(**self.valid_user_data)
        
        # Password should be hashed, not stored in plain text
        assert user.password_hash != 'SecurePass123!'
        assert user.password_hash.startswith('$2b$')  # bcrypt hash format
        assert len(user.password_hash) > 50
    
    def test_password_verification(self):
        """Test password verification functionality."""
        user = User(**self.valid_user_data)
        
        # Correct password should verify
        assert user.check_password('SecurePass123!') is True
        
        # Incorrect password should not verify
        assert user.check_password('wrongpassword') is False
        assert user.check_password('') is False
        assert user.check_password(None) is False
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Test various invalid passwords
        invalid_passwords = [
            'weak',  # Too short
            'password',  # No uppercase, numbers, or special chars
            'PASSWORD',  # No lowercase, numbers, or special chars
            'Password',  # No numbers or special chars
            'Password123',  # No special chars
            'Password!',  # No numbers
            '12345678!',  # No letters
        ]
        
        for invalid_password in invalid_passwords:
            data = self.valid_user_data.copy()
            data['password'] = invalid_password
            
            with pytest.raises(ValueError, match="Password must be at least"):
                User(**data)
    
    def test_email_validation(self):
        """Test email validation with various invalid formats."""
        invalid_emails = [
            'invalid',
            'invalid@',
            '@invalid.com',
            'invalid@.com',
            'invalid@com.',
            'invalid..email@example.com',
            'a' * 60 + '@example.com',  # Local part too long
            'test@' + 'a' * 250 + '.com',  # Domain too long
            '',
            None
        ]
        
        for invalid_email in invalid_emails:
            data = self.valid_user_data.copy()
            data['email'] = invalid_email
            
            with pytest.raises(ValueError, match="validation failed"):
                User(**data)
    
    def test_username_validation(self):
        """Test username validation with various invalid formats."""
        invalid_usernames = [
            'a',  # Too short
            'ab',  # Too short
            'a' * 51,  # Too long
            'user-name',  # Invalid character (hyphen)
            'user name',  # Invalid character (space)
            'user@name',  # Invalid character (@)
            '_username',  # Cannot start with underscore
            '123username',  # Must start with letter
            '',
            None
        ]
        
        for invalid_username in invalid_usernames:
            data = self.valid_user_data.copy()
            data['username'] = invalid_username
            
            with pytest.raises(ValueError, match="validation failed"):
                User(**data)
    
    def test_age_calculation(self):
        """Test age calculation from birth date."""
        user = User(**self.valid_user_data)
        
        # Test with specific birth date
        user.birth_date = date(1990, 1, 1)
        age = user.age
        expected_age = date.today().year - 1990
        
        # Adjust for birthday not yet occurred this year
        if date.today() < date(date.today().year, 1, 1):
            expected_age -= 1
        
        assert age == expected_age
        
        # Test with no birth date
        user.birth_date = None
        assert user.age is None
    
    def test_full_name_property(self):
        """Test full_name property with various name combinations."""
        user = User(**self.valid_user_data)
        
        # Both first and last name
        assert user.full_name == 'Test User'
        
        # Only first name
        user.last_name = None
        assert user.full_name == 'Test'
        
        # Only last name
        user.first_name = None
        user.last_name = 'User'
        assert user.full_name == 'User'
        
        # No names, should fall back to username
        user.first_name = None
        user.last_name = None
        assert user.full_name == 'testuser'
    
    def test_birth_date_validation(self):
        """Test birth date validation."""
        user = User(**self.valid_user_data)
        
        # Future date should be invalid
        future_date = date.today() + timedelta(days=1)
        user.birth_date = future_date
        
        is_valid, errors = user.validate()
        assert not is_valid
        assert any('future' in error.lower() for error in errors)
        
        # Age below 13 should be invalid (COPPA compliance)
        recent_date = date.today() - timedelta(days=365 * 10)  # 10 years old
        user.birth_date = recent_date
        
        is_valid, errors = user.validate()
        assert not is_valid
        assert any('13 years' in error for error in errors)
    
    def test_account_lockout_functionality(self):
        """Test account lockout after failed login attempts."""
        user = User(**self.valid_user_data)
        
        # Initially account should not be locked
        assert not user.is_account_locked()
        
        # Simulate failed login attempts
        for i in range(4):
            user.increment_failed_login()
            assert not user.is_account_locked()  # Should not be locked yet
        
        # Fifth attempt should lock the account
        user.increment_failed_login()
        assert user.is_account_locked()
        assert user.account_locked_until is not None
        assert user.account_locked_until > datetime.utcnow()
    
    def test_failed_login_reset(self):
        """Test resetting failed login attempts."""
        user = User(**self.valid_user_data)
        
        # Simulate some failed attempts
        user.increment_failed_login()
        user.increment_failed_login()
        assert user.failed_login_attempts == "2"
        
        # Reset should clear attempts and update last login
        user.reset_failed_login()
        assert user.failed_login_attempts == "0"
        assert user.account_locked_until is None
        assert user.last_login_at is not None
    
    def test_email_verification(self):
        """Test email verification functionality."""
        user = User(**self.valid_user_data)
        
        # Initially not verified
        assert not user.is_verified
        
        # Verify email
        user.verify_email()
        assert user.is_verified
        assert user.updated_at is not None
    
    def test_soft_delete_functionality(self):
        """Test soft delete functionality."""
        user = User(**self.valid_user_data)
        
        # Initially active
        assert user.is_active is True
        
        # Soft delete
        user.soft_delete()
        assert user.is_active is False
        assert user.updated_at is not None
        
        # Restore
        user.restore()
        assert user.is_active is True
    
    def test_to_dict_method(self):
        """Test conversion to dictionary."""
        user = User(**self.valid_user_data)
        user_dict = user.to_dict()
        
        # Should include basic fields
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['username'] == 'testuser'
        assert user_dict['first_name'] == 'Test'
        assert user_dict['last_name'] == 'User'
        assert user_dict['full_name'] == 'Test User'
        assert user_dict['is_active'] is True
        
        # Should exclude sensitive fields by default
        assert 'password_hash' not in user_dict
        assert 'failed_login_attempts' not in user_dict
        
        # Should include sensitive fields when requested
        sensitive_dict = user.to_dict(include_sensitive=True)
        assert 'password_hash' in sensitive_dict
        assert 'failed_login_attempts' in sensitive_dict
    
    def test_user_string_representations(self):
        """Test string representation methods."""
        user = User(**self.valid_user_data)
        
        # __repr__ should include email and username
        repr_str = repr(user)
        assert 'test@example.com' in repr_str
        assert 'testuser' in repr_str
        
        # __str__ should return the user ID
        str_repr = str(user)
        assert str(user.id) == str_repr
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        user = User(**self.valid_user_data)
        
        # Valid phone numbers
        valid_phones = [
            '+1234567890',
            '+12345678901',
            '1234567890',
            '+44 123 456 7890',
            '+1 (555) 123-4567'
        ]
        
        for phone in valid_phones:
            user.phone_number = phone
            is_valid, errors = user.validate()
            assert is_valid, f"Phone {phone} should be valid"
        
        # Invalid phone numbers
        invalid_phones = [
            '123',  # Too short
            'abc123456789',  # Contains letters
            '+',  # Just plus sign
            '++1234567890',  # Multiple plus signs
            '0123456789'  # Starts with 0
        ]
        
        for phone in invalid_phones:
            user.phone_number = phone
            is_valid, errors = user.validate()
            assert not is_valid, f"Phone {phone} should be invalid"
    
    def test_bio_length_validation(self):
        """Test bio length validation."""
        user = User(**self.valid_user_data)
        
        # Valid bio (under 1000 characters)
        user.bio = 'A' * 999
        is_valid, errors = user.validate()
        assert is_valid
        
        # Invalid bio (over 1000 characters)
        user.bio = 'A' * 1001
        is_valid, errors = user.validate()
        assert not is_valid
        assert any('1000 characters' in error for error in errors)
    
    def test_model_relationships_with_roles(self):
        """Test user-role relationships."""
        # Create user and role
        user = User(**self.valid_user_data)
        role = Role(name='test_role', display_name='Test Role')
        
        # Add role to user
        user.roles.append(role)
        
        assert len(user.roles) == 1
        assert role in user.roles
        assert user.has_role('test_role')
        assert not user.has_role('nonexistent_role')
    
    @pytest.mark.integration
    def test_database_constraints(self):
        """Test database-level constraints."""
        db.session.add(User(**self.valid_user_data))
        db.session.commit()
        
        # Attempt to create user with same email
        duplicate_email_data = self.valid_user_data.copy()
        duplicate_email_data['username'] = 'different'
        
        with pytest.raises(IntegrityError):
            db.session.add(User(**duplicate_email_data))
            db.session.commit()
        
        db.session.rollback()
        
        # Attempt to create user with same username
        duplicate_username_data = self.valid_user_data.copy()
        duplicate_username_data['email'] = 'different@example.com'
        duplicate_username_data['username'] = 'testuser'
        
        with pytest.raises(IntegrityError):
            db.session.add(User(**duplicate_username_data))
            db.session.commit()
    
    def test_update_from_dict_method(self):
        """Test updating user from dictionary."""
        user = User(**self.valid_user_data)
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+1234567890'
        }
        
        user.update_from_dict(update_data)
        
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'
        assert user.phone_number == '+1234567890'
        assert user.updated_at is not None
        
        # Should not update protected fields
        protected_update = {
            'id': 'should-not-change',
            'created_at': datetime.utcnow()
        }
        
        original_id = user.id
        original_created_at = user.created_at
        
        user.update_from_dict(protected_update)
        
        assert user.id == original_id
        assert user.created_at == original_created_at