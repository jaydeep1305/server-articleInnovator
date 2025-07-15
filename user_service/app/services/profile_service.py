"""
Profile Service for User Management Microservice.

This module provides profile management functionality including
profile creation, updates, and comprehensive profile operations.
"""

from typing import Optional, Dict, Any, List
from datetime import date
from flask import current_app

from app.models.profile import Profile, GenderEnum
from app.models.user import User
from .base_service import BaseService, ValidationError, NotFoundError, ServiceError


class ProfileService(BaseService):
    """
    Service class for comprehensive profile management operations.
    
    This service handles profile creation, updates, validation,
    and business logic related to user profiles while maintaining
    data integrity and privacy settings.
    
    Features:
    - Profile creation and updates
    - Address and contact information management
    - Professional information handling
    - Social media links management
    - Privacy settings management
    - Profile completion tracking
    """
    
    def __init__(self):
        """Initialize the profile service with the Profile model."""
        super().__init__(Profile)
    
    def create_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Profile:
        """
        Create a new profile for a user.
        
        Args:
            user_id: ID of the user to create profile for
            profile_data: Dictionary containing profile information
            
        Returns:
            Created profile instance
            
        Raises:
            ValidationError: If profile data is invalid or user already has profile
            NotFoundError: If user is not found
            ServiceError: For other creation errors
            
        Example:
            >>> profile_data = {
            ...     'bio': 'Software developer with 5 years experience',
            ...     'phone_number': '+1-555-123-4567',
            ...     'city': 'San Francisco',
            ...     'country': 'USA'
            ... }
            >>> profile = profile_service.create_profile(user_id=123, profile_data=profile_data)
        """
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        # Check if user already has a profile
        if user.profile:
            raise ValidationError(f"User {user_id} already has a profile")
        
        # Add user_id to profile data
        profile_data['user_id'] = user_id
        
        # Set default values if not provided
        if 'timezone' not in profile_data:
            profile_data['timezone'] = 'UTC'
        if 'language_preference' not in profile_data:
            profile_data['language_preference'] = 'en'
        
        profile = self.create(profile_data)
        
        current_app.logger.info(f"Profile created for user ID: {user_id}")
        
        return profile
    
    def get_profile_by_user_id(self, user_id: int) -> Optional[Profile]:
        """
        Get profile by user ID.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Profile instance if found, None otherwise
            
        Example:
            >>> profile = profile_service.get_profile_by_user_id(123)
        """
        return self.find_one_by(user_id=user_id)
    
    def get_profile_by_user_id_or_404(self, user_id: int) -> Profile:
        """
        Get profile by user ID or raise NotFoundError.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Profile instance
            
        Raises:
            NotFoundError: If profile is not found
        """
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            raise NotFoundError(f"Profile for user ID {user_id} not found")
        return profile
    
    def update_personal_info(self, user_id: int, personal_data: Dict[str, Any]) -> Profile:
        """
        Update personal information in a user's profile.
        
        Args:
            user_id: ID of the user
            personal_data: Dictionary containing personal information fields
            
        Returns:
            Updated profile instance
            
        Raises:
            NotFoundError: If profile is not found
            ValidationError: If data is invalid
            
        Example:
            >>> personal_data = {
            ...     'bio': 'Updated bio',
            ...     'phone_number': '+1-555-987-6543',
            ...     'date_of_birth': date(1990, 5, 15)
            ... }
            >>> profile = profile_service.update_personal_info(123, personal_data)
        """
        profile = self.get_profile_by_user_id_or_404(user_id)
        
        # Filter to only personal fields
        allowed_fields = {
            'bio', 'phone_number', 'date_of_birth', 'gender'
        }
        
        filtered_data = {
            k: v for k, v in personal_data.items() 
            if k in allowed_fields
        }
        
        if not filtered_data:
            raise ValidationError("No valid personal information fields provided")
        
        updated_profile = self.update(profile.id, filtered_data)
        
        current_app.logger.info(f"Personal info updated for user ID: {user_id}")
        
        return updated_profile
    
    def update_address(self, user_id: int, address_data: Dict[str, Any]) -> Profile:
        """
        Update address information in a user's profile.
        
        Args:
            user_id: ID of the user
            address_data: Dictionary containing address fields
            
        Returns:
            Updated profile instance
            
        Raises:
            NotFoundError: If profile is not found
            ValidationError: If data is invalid
            
        Example:
            >>> address_data = {
            ...     'address_line_1': '123 Main St',
            ...     'city': 'New York',
            ...     'state_province': 'NY',
            ...     'postal_code': '10001',
            ...     'country': 'USA'
            ... }
            >>> profile = profile_service.update_address(123, address_data)
        """
        profile = self.get_profile_by_user_id_or_404(user_id)
        
        # Filter to only address fields
        allowed_fields = {
            'address_line_1', 'address_line_2', 'city', 
            'state_province', 'postal_code', 'country'
        }
        
        filtered_data = {
            k: v for k, v in address_data.items() 
            if k in allowed_fields
        }
        
        if not filtered_data:
            raise ValidationError("No valid address fields provided")
        
        updated_profile = self.update(profile.id, filtered_data)
        
        current_app.logger.info(f"Address updated for user ID: {user_id}")
        
        return updated_profile
    
    def update_professional_info(self, user_id: int, 
                                professional_data: Dict[str, Any]) -> Profile:
        """
        Update professional information in a user's profile.
        
        Args:
            user_id: ID of the user
            professional_data: Dictionary containing professional fields
            
        Returns:
            Updated profile instance
            
        Raises:
            NotFoundError: If profile is not found
            ValidationError: If data is invalid
            
        Example:
            >>> prof_data = {
            ...     'company': 'Tech Corp',
            ...     'job_title': 'Senior Developer',
            ...     'website_url': 'https://johndoe.dev'
            ... }
            >>> profile = profile_service.update_professional_info(123, prof_data)
        """
        profile = self.get_profile_by_user_id_or_404(user_id)
        
        # Filter to only professional fields
        allowed_fields = {
            'company', 'job_title', 'website_url'
        }
        
        filtered_data = {
            k: v for k, v in professional_data.items() 
            if k in allowed_fields
        }
        
        if not filtered_data:
            raise ValidationError("No valid professional fields provided")
        
        updated_profile = self.update(profile.id, filtered_data)
        
        current_app.logger.info(f"Professional info updated for user ID: {user_id}")
        
        return updated_profile
    
    def update_social_links(self, user_id: int, social_data: Dict[str, Any]) -> Profile:
        """
        Update social media links in a user's profile.
        
        Args:
            user_id: ID of the user
            social_data: Dictionary containing social media fields
            
        Returns:
            Updated profile instance
            
        Raises:
            NotFoundError: If profile is not found
            ValidationError: If data is invalid
            
        Example:
            >>> social_data = {
            ...     'linkedin_url': 'https://linkedin.com/in/johndoe',
            ...     'twitter_handle': 'johndoe',
            ...     'github_username': 'john-doe'
            ... }
            >>> profile = profile_service.update_social_links(123, social_data)
        """
        profile = self.get_profile_by_user_id_or_404(user_id)
        
        # Filter to only social media fields
        allowed_fields = {
            'linkedin_url', 'twitter_handle', 'github_username'
        }
        
        filtered_data = {
            k: v for k, v in social_data.items() 
            if k in allowed_fields
        }
        
        if not filtered_data:
            raise ValidationError("No valid social media fields provided")
        
        updated_profile = self.update(profile.id, filtered_data)
        
        current_app.logger.info(f"Social links updated for user ID: {user_id}")
        
        return updated_profile
    
    def update_preferences(self, user_id: int, preferences_data: Dict[str, Any]) -> Profile:
        """
        Update user preferences and settings.
        
        Args:
            user_id: ID of the user
            preferences_data: Dictionary containing preference fields
            
        Returns:
            Updated profile instance
            
        Raises:
            NotFoundError: If profile is not found
            ValidationError: If data is invalid
            
        Example:
            >>> prefs_data = {
            ...     'timezone': 'America/New_York',
            ...     'language_preference': 'es',
            ...     'is_profile_public': True,
            ...     'newsletter_subscribed': False
            ... }
            >>> profile = profile_service.update_preferences(123, prefs_data)
        """
        profile = self.get_profile_by_user_id_or_404(user_id)
        
        # Filter to only preference fields
        allowed_fields = {
            'timezone', 'language_preference', 'is_profile_public', 
            'newsletter_subscribed', 'avatar_url'
        }
        
        filtered_data = {
            k: v for k, v in preferences_data.items() 
            if k in allowed_fields
        }
        
        if not filtered_data:
            raise ValidationError("No valid preference fields provided")
        
        updated_profile = self.update(profile.id, filtered_data)
        
        current_app.logger.info(f"Preferences updated for user ID: {user_id}")
        
        return updated_profile
    
    def get_profile_completion_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get profile completion status with detailed breakdown.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing completion status and missing fields
            
        Raises:
            NotFoundError: If profile is not found
            
        Example:
            >>> status = profile_service.get_profile_completion_status(123)
            >>> print(f"Profile is {status['completion_percentage']}% complete")
        """
        profile = self.get_profile_by_user_id_or_404(user_id)
        
        # Define required fields for completion
        required_fields = {
            'bio': profile.bio,
            'phone_number': profile.phone_number,
            'city': profile.city,
            'country': profile.country
        }
        
        # Define optional but recommended fields
        recommended_fields = {
            'date_of_birth': profile.date_of_birth,
            'company': profile.company,
            'job_title': profile.job_title,
            'address_line_1': profile.address_line_1
        }
        
        # Calculate completion
        completed_required = sum(
            1 for value in required_fields.values() 
            if value is not None and str(value).strip()
        )
        
        completed_recommended = sum(
            1 for value in recommended_fields.values() 
            if value is not None and str(value).strip()
        )
        
        total_fields = len(required_fields) + len(recommended_fields)
        completed_fields = completed_required + completed_recommended
        
        completion_percentage = round((completed_fields / total_fields) * 100, 1)
        
        # Find missing fields
        missing_required = [
            field for field, value in required_fields.items()
            if value is None or not str(value).strip()
        ]
        
        missing_recommended = [
            field for field, value in recommended_fields.items()
            if value is None or not str(value).strip()
        ]
        
        return {
            'is_complete': profile.is_profile_complete(),
            'completion_percentage': completion_percentage,
            'completed_required': completed_required,
            'total_required': len(required_fields),
            'completed_recommended': completed_recommended,
            'total_recommended': len(recommended_fields),
            'missing_required': missing_required,
            'missing_recommended': missing_recommended
        }
    
    def search_public_profiles(self, query: str, filters: Optional[Dict[str, Any]] = None,
                              page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search public profiles by various criteria.
        
        Args:
            query: Search query string
            filters: Additional filters to apply
            page: Page number for pagination
            per_page: Items per page
            
        Returns:
            Dictionary containing search results and pagination info
            
        Note:
            Only searches profiles marked as public
        """
        from sqlalchemy import or_, and_
        
        # Base query for public profiles only
        search_query = Profile.query.filter(
            Profile.is_profile_public == True
        )
        
        # Add text search across relevant fields
        if query:
            search_query = search_query.filter(
                or_(
                    Profile.bio.ilike(f'%{query}%'),
                    Profile.company.ilike(f'%{query}%'),
                    Profile.job_title.ilike(f'%{query}%'),
                    Profile.city.ilike(f'%{query}%'),
                    Profile.country.ilike(f'%{query}%')
                )
            )
        
        # Apply additional filters
        if filters:
            search_query = self._apply_filters(search_query, filters)
        
        # Execute paginated search
        pagination = search_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'query': query
        }
    
    def get_profiles_by_location(self, city: Optional[str] = None, 
                               country: Optional[str] = None,
                               public_only: bool = True) -> List[Profile]:
        """
        Get profiles by location.
        
        Args:
            city: City name to filter by
            country: Country name to filter by
            public_only: Whether to only return public profiles
            
        Returns:
            List of matching profiles
            
        Example:
            >>> sf_profiles = profile_service.get_profiles_by_location(
            ...     city='San Francisco', 
            ...     country='USA'
            ... )
        """
        filters = {}
        
        if city:
            filters['city'] = city
        if country:
            filters['country'] = country
        if public_only:
            filters['is_profile_public'] = True
        
        return self.find_by(**filters)
    
    def get_profiles_by_company(self, company: str, 
                               public_only: bool = True) -> List[Profile]:
        """
        Get profiles by company name.
        
        Args:
            company: Company name to search for
            public_only: Whether to only return public profiles
            
        Returns:
            List of matching profiles
            
        Example:
            >>> tech_corp_profiles = profile_service.get_profiles_by_company('Tech Corp')
        """
        query = Profile.query.filter(
            Profile.company.ilike(f'%{company}%')
        )
        
        if public_only:
            query = query.filter(Profile.is_profile_public == True)
        
        return query.all()
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """
        Get profile statistics for admin dashboard.
        
        Returns:
            Dictionary containing various profile statistics
        """
        total_profiles = self.count()
        public_profiles = self.count({'is_profile_public': True})
        complete_profiles = Profile.query.filter(
            Profile.bio.isnot(None),
            Profile.phone_number.isnot(None),
            Profile.city.isnot(None),
            Profile.country.isnot(None)
        ).count()
        
        # Newsletter subscribers
        newsletter_subscribers = self.count({'newsletter_subscribed': True})
        
        # Profiles with social links
        profiles_with_social = Profile.query.filter(
            or_(
                Profile.linkedin_url.isnot(None),
                Profile.twitter_handle.isnot(None),
                Profile.github_username.isnot(None)
            )
        ).count()
        
        return {
            'total_profiles': total_profiles,
            'public_profiles': public_profiles,
            'complete_profiles': complete_profiles,
            'newsletter_subscribers': newsletter_subscribers,
            'profiles_with_social': profiles_with_social,
            'completion_rate': (complete_profiles / total_profiles * 100) if total_profiles > 0 else 0,
            'public_profile_rate': (public_profiles / total_profiles * 100) if total_profiles > 0 else 0
        }