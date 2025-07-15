"""
Profile Model for User Management Microservice.

This module defines the Profile model that extends user information
with additional personal and professional details.
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Date, Integer, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship, validates
import enum

from app import db
from .base import BaseModel


class GenderEnum(enum.Enum):
    """Enumeration for gender options with inclusive choices."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    OTHER = "other"


class Profile(BaseModel):
    """
    Profile model extending User with detailed personal and professional information.
    
    This model provides a comprehensive user profile system including:
    - Personal information (bio, phone, address)
    - Professional details (company, job title, website)
    - Social media links
    - Avatar and customization options
    - Privacy and preference settings
    
    Attributes:
        user_id: Foreign key to User model (one-to-one relationship)
        bio: User's biographical information (max 1000 characters)
        phone_number: Contact phone number with validation
        date_of_birth: User's birth date for age calculation
        gender: Gender identification (enum with inclusive options)
        address_line_1: Primary address line
        address_line_2: Secondary address line (optional)
        city: City name
        state_province: State or province name
        postal_code: ZIP/postal code
        country: Country name
        company: Current company/employer
        job_title: Current job position
        website_url: Personal or professional website
        linkedin_url: LinkedIn profile URL
        twitter_handle: Twitter username (without @)
        github_username: GitHub username
        avatar_url: Profile picture URL
        timezone: User's timezone preference
        language_preference: Preferred language code (ISO 639-1)
        is_profile_public: Privacy setting for profile visibility
        newsletter_subscribed: Newsletter subscription preference
    
    Relationships:
        user: One-to-one relationship back to User model
    """
    
    __tablename__ = 'profiles'
    
    # Foreign key relationship to User
    user_id = Column(
        Integer, 
        ForeignKey('users.id'), 
        unique=True, 
        nullable=False,
        doc="Foreign key to User model (one-to-one relationship)"
    )
    
    # Personal Information
    bio = Column(
        Text(1000), 
        nullable=True,
        doc="User's biographical information (max 1000 characters)"
    )
    
    phone_number = Column(
        String(20), 
        nullable=True,
        doc="Contact phone number with international format validation"
    )
    
    date_of_birth = Column(
        Date, 
        nullable=True,
        doc="User's birth date for age calculation and personalization"
    )
    
    gender = Column(
        SQLEnum(GenderEnum), 
        nullable=True,
        doc="Gender identification with inclusive options"
    )
    
    # Address Information
    address_line_1 = Column(
        String(200), 
        nullable=True,
        doc="Primary address line (street address)"
    )
    
    address_line_2 = Column(
        String(200), 
        nullable=True,
        doc="Secondary address line (apartment, unit, etc.)"
    )
    
    city = Column(
        String(100), 
        nullable=True,
        doc="City name"
    )
    
    state_province = Column(
        String(100), 
        nullable=True,
        doc="State or province name"
    )
    
    postal_code = Column(
        String(20), 
        nullable=True,
        doc="ZIP/postal code"
    )
    
    country = Column(
        String(100), 
        nullable=True,
        doc="Country name"
    )
    
    # Professional Information
    company = Column(
        String(200), 
        nullable=True,
        doc="Current company or employer"
    )
    
    job_title = Column(
        String(150), 
        nullable=True,
        doc="Current job position or title"
    )
    
    # Online Presence
    website_url = Column(
        String(500), 
        nullable=True,
        doc="Personal or professional website URL"
    )
    
    linkedin_url = Column(
        String(500), 
        nullable=True,
        doc="LinkedIn profile URL"
    )
    
    twitter_handle = Column(
        String(50), 
        nullable=True,
        doc="Twitter username (without @ symbol)"
    )
    
    github_username = Column(
        String(50), 
        nullable=True,
        doc="GitHub username"
    )
    
    # Avatar and Customization
    avatar_url = Column(
        String(500), 
        nullable=True,
        doc="Profile picture URL"
    )
    
    # Preferences and Settings
    timezone = Column(
        String(50), 
        default='UTC',
        doc="User's timezone preference (e.g., 'America/New_York')"
    )
    
    language_preference = Column(
        String(5), 
        default='en',
        doc="Preferred language code (ISO 639-1 format)"
    )
    
    # Privacy Settings
    is_profile_public = Column(
        Boolean, 
        default=False, 
        nullable=False,
        doc="Privacy setting for profile visibility to other users"
    )
    
    newsletter_subscribed = Column(
        Boolean, 
        default=True, 
        nullable=False,
        doc="Newsletter subscription preference"
    )
    
    # Relationships
    user = relationship(
        "User", 
        back_populates="profile",
        doc="One-to-one relationship back to User model"
    )
    
    @validates('phone_number')
    def validate_phone_number(self, key: str, phone_number: str) -> Optional[str]:
        """
        Validate phone number format.
        
        Accepts international formats including:
        - +1-234-567-8900
        - +44 20 7946 0958
        - (555) 123-4567
        
        Args:
            key: Field name being validated
            phone_number: Phone number to validate
            
        Returns:
            Validated phone number or None if empty
            
        Raises:
            ValueError: If phone number format is invalid
        """
        if not phone_number:
            return None
        
        phone_number = phone_number.strip()
        
        # Basic phone number validation - allows various international formats
        phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,18}$'
        if not re.match(phone_pattern, phone_number):
            raise ValueError(
                "Invalid phone number format. Use international format "
                "(e.g., +1-234-567-8900, +44 20 7946 0958)"
            )
        
        return phone_number
    
    @validates('date_of_birth')
    def validate_date_of_birth(self, key: str, dob: date) -> Optional[date]:
        """
        Validate date of birth to ensure realistic values.
        
        Args:
            key: Field name being validated
            dob: Date of birth to validate
            
        Returns:
            Validated date of birth or None if empty
            
        Raises:
            ValueError: If date is invalid or unrealistic
        """
        if not dob:
            return None
        
        today = date.today()
        
        # Check if date is not in the future
        if dob > today:
            raise ValueError("Date of birth cannot be in the future")
        
        # Check for reasonable age limits (13-120 years old)
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 13:
            raise ValueError("User must be at least 13 years old")
        if age > 120:
            raise ValueError("Invalid date of birth - age cannot exceed 120 years")
        
        return dob
    
    @validates('website_url', 'linkedin_url')
    def validate_url_fields(self, key: str, url: str) -> Optional[str]:
        """
        Validate URL format for website and social media fields.
        
        Args:
            key: Field name being validated
            url: URL to validate
            
        Returns:
            Validated URL or None if empty
            
        Raises:
            ValueError: If URL format is invalid
        """
        if not url:
            return None
        
        url = url.strip()
        
        # Basic URL validation
        url_pattern = r'^https?:\/\/[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url, re.IGNORECASE):
            raise ValueError(f"Invalid URL format for {key}")
        
        # Specific validation for LinkedIn
        if key == 'linkedin_url' and 'linkedin.com' not in url.lower():
            raise ValueError("LinkedIn URL must be from linkedin.com domain")
        
        return url
    
    @validates('twitter_handle')
    def validate_twitter_handle(self, key: str, handle: str) -> Optional[str]:
        """
        Validate Twitter handle format.
        
        Args:
            key: Field name being validated
            handle: Twitter handle to validate (without @)
            
        Returns:
            Validated handle or None if empty
            
        Raises:
            ValueError: If handle format is invalid
        """
        if not handle:
            return None
        
        handle = handle.strip().lstrip('@')  # Remove @ if provided
        
        # Twitter handle validation (1-15 characters, alphanumeric and underscores)
        if not re.match(r'^[a-zA-Z0-9_]{1,15}$', handle):
            raise ValueError(
                "Twitter handle must be 1-15 characters long and contain "
                "only letters, numbers, and underscores"
            )
        
        return handle
    
    @validates('github_username')
    def validate_github_username(self, key: str, username: str) -> Optional[str]:
        """
        Validate GitHub username format.
        
        Args:
            key: Field name being validated
            username: GitHub username to validate
            
        Returns:
            Validated username or None if empty
            
        Raises:
            ValueError: If username format is invalid
        """
        if not username:
            return None
        
        username = username.strip()
        
        # GitHub username validation (alphanumeric and hyphens, max 39 chars)
        if not re.match(r'^[a-zA-Z0-9\-]{1,39}$', username):
            raise ValueError(
                "GitHub username must be 1-39 characters long and contain "
                "only letters, numbers, and hyphens"
            )
        
        # Cannot start or end with hyphen
        if username.startswith('-') or username.endswith('-'):
            raise ValueError("GitHub username cannot start or end with a hyphen")
        
        return username
    
    @validates('bio')
    def validate_bio(self, key: str, bio: str) -> Optional[str]:
        """
        Validate bio content and length.
        
        Args:
            key: Field name being validated
            bio: Bio text to validate
            
        Returns:
            Validated bio or None if empty
            
        Raises:
            ValueError: If bio exceeds character limit
        """
        if not bio:
            return None
        
        bio = bio.strip()
        if len(bio) > 1000:
            raise ValueError("Bio cannot exceed 1000 characters")
        
        return bio
    
    @validates('language_preference')
    def validate_language_preference(self, key: str, lang: str) -> str:
        """
        Validate language preference format (ISO 639-1).
        
        Args:
            key: Field name being validated
            lang: Language code to validate
            
        Returns:
            Validated language code
            
        Raises:
            ValueError: If language code format is invalid
        """
        if not lang:
            return 'en'  # Default to English
        
        lang = lang.strip().lower()
        
        # Basic ISO 639-1 format validation (2 characters)
        if not re.match(r'^[a-z]{2}$', lang):
            raise ValueError("Language preference must be a valid ISO 639-1 code (e.g., 'en', 'es', 'fr')")
        
        return lang
    
    @property
    def age(self) -> Optional[int]:
        """
        Calculate user's age from date of birth.
        
        Returns:
            Age in years or None if date of birth not set
        """
        if not self.date_of_birth:
            return None
        
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def full_address(self) -> Optional[str]:
        """
        Get formatted full address.
        
        Returns:
            Formatted address string or None if no address components
        """
        components = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state_province,
            self.postal_code,
            self.country
        ]
        
        # Filter out None/empty components
        address_parts = [part for part in components if part and part.strip()]
        
        if not address_parts:
            return None
        
        return ', '.join(address_parts)
    
    def get_social_links(self) -> Dict[str, str]:
        """
        Get all social media links in a structured format.
        
        Returns:
            Dictionary containing available social media links
            
        Example:
            >>> profile.get_social_links()
            {
                'website': 'https://johndoe.com',
                'linkedin': 'https://linkedin.com/in/johndoe',
                'twitter': 'https://twitter.com/johndoe',
                'github': 'https://github.com/johndoe'
            }
        """
        links = {}
        
        if self.website_url:
            links['website'] = self.website_url
        
        if self.linkedin_url:
            links['linkedin'] = self.linkedin_url
        
        if self.twitter_handle:
            links['twitter'] = f"https://twitter.com/{self.twitter_handle}"
        
        if self.github_username:
            links['github'] = f"https://github.com/{self.github_username}"
        
        return links
    
    def update_professional_info(self, company: str = None, job_title: str = None) -> None:
        """
        Update professional information in a single transaction.
        
        Args:
            company: New company name
            job_title: New job title
        """
        updates = {}
        if company is not None:
            updates['company'] = company
        if job_title is not None:
            updates['job_title'] = job_title
        
        if updates:
            self.update(**updates)
    
    def update_address(self, address_line_1: str = None, address_line_2: str = None,
                      city: str = None, state_province: str = None,
                      postal_code: str = None, country: str = None) -> None:
        """
        Update address information in a single transaction.
        
        Args:
            address_line_1: Primary address line
            address_line_2: Secondary address line
            city: City name
            state_province: State or province
            postal_code: ZIP/postal code
            country: Country name
        """
        updates = {}
        for field, value in {
            'address_line_1': address_line_1,
            'address_line_2': address_line_2,
            'city': city,
            'state_province': state_province,
            'postal_code': postal_code,
            'country': country
        }.items():
            if value is not None:
                updates[field] = value
        
        if updates:
            self.update(**updates)
    
    def is_profile_complete(self) -> bool:
        """
        Check if profile has minimum required information for completeness.
        
        Returns:
            True if profile is considered complete
        """
        required_fields = [
            self.bio,
            self.phone_number,
            self.city,
            self.country
        ]
        
        return all(field is not None and str(field).strip() for field in required_fields)
    
    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert profile instance to dictionary with computed fields.
        
        Args:
            exclude_fields: List of field names to exclude from output
            
        Returns:
            Dictionary representation including computed fields
        """
        profile_dict = super().to_dict(exclude_fields=exclude_fields)
        
        # Add computed fields
        profile_dict['age'] = self.age
        profile_dict['full_address'] = self.full_address
        profile_dict['social_links'] = self.get_social_links()
        profile_dict['is_complete'] = self.is_profile_complete()
        
        # Format enum values
        if self.gender:
            profile_dict['gender'] = self.gender.value
        
        return profile_dict
    
    def validate(self) -> bool:
        """
        Comprehensive validation of profile instance.
        
        Returns:
            True if all validations pass
            
        Raises:
            ValueError: If any validation fails
        """
        # Validate user_id is set
        if not self.user_id:
            raise ValueError("Profile must be associated with a user")
        
        return True
    
    def __repr__(self) -> str:
        """String representation of the profile."""
        return f"<Profile(id={self.id}, user_id={self.user_id}, complete={self.is_profile_complete()})>"