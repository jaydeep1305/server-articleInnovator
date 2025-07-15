"""
User service module for the Blog Microservice.

This module implements business logic for user management including
authentication, registration, and profile management.

Classes:
    UserService: Service class for user-related operations
"""

from typing import Optional, Dict, Any, List
from flask_sqlalchemy import SQLAlchemy

from app.models import User
from .base_service import BaseService, PaginationResult


class UserService(BaseService[User]):
    """
    Service class for user-related business logic operations.
    
    This service handles user registration, authentication, profile management,
    and user-specific queries with proper validation and error handling.
    
    Methods:
        authenticate: Authenticate user with credentials
        register: Register a new user
        get_by_username: Get user by username
        get_by_email: Get user by email
        activate_user: Activate user account
        deactivate_user: Deactivate user account
        verify_email: Mark user email as verified
        update_password: Update user password
        search_users: Search users by various criteria
        get_user_statistics: Get user activity statistics
    """
    
    def __init__(self, db: SQLAlchemy):
        """
        Initialize the UserService.
        
        Args:
            db: SQLAlchemy database instance
        """
        super().__init__(User, db)
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username/email and password.
        
        Args:
            username: Username or email address
            password: Plain text password
            
        Returns:
            User instance if authentication successful, None otherwise
            
        Example:
            user = user_service.authenticate('john_doe', 'password123')
            if user:
                # User authenticated successfully
                pass
        """
        # Try to find user by username or email
        user = self.get_by_username(username)
        if not user:
            user = self.get_by_email(username)
        
        # Check if user exists and is active
        if not user or not user.is_active:
            return None
        
        # Verify password
        if user.check_password(password):
            return user
        
        return None
    
    def register(self, username: str, email: str, password: str, 
                 **kwargs) -> User:
        """
        Register a new user with validation.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password
            **kwargs: Additional user attributes
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If username or email already exists or validation fails
            
        Example:
            user = user_service.register(
                username='john_doe',
                email='john@example.com',
                password='SecurePass123',
                first_name='John',
                last_name='Doe'
            )
        """
        # Check if username already exists
        if self.exists(username=username.lower()):
            raise ValueError(f"Username '{username}' already exists")
        
        # Check if email already exists
        if self.exists(email=email.lower()):
            raise ValueError(f"Email '{email}' already exists")
        
        # Create new user
        user_data = {
            'username': username,
            'email': email,
            'password': password,
            **kwargs
        }
        
        return self.create(**user_data)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username (case-insensitive).
        
        Args:
            username: Username to search for
            
        Returns:
            User instance if found, None otherwise
            
        Example:
            user = user_service.get_by_username('john_doe')
        """
        return self.db.session.query(User).filter(
            User.username.ilike(username.lower())
        ).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address (case-insensitive).
        
        Args:
            email: Email address to search for
            
        Returns:
            User instance if found, None otherwise
            
        Example:
            user = user_service.get_by_email('john@example.com')
        """
        return self.db.session.query(User).filter(
            User.email.ilike(email.lower())
        ).first()
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """
        Activate a user account.
        
        Args:
            user_id: ID of the user to activate
            
        Returns:
            Updated user instance if found, None otherwise
            
        Example:
            user = user_service.activate_user(1)
        """
        return self.update(user_id, is_active=True)
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: ID of the user to deactivate
            
        Returns:
            Updated user instance if found, None otherwise
            
        Example:
            user = user_service.deactivate_user(1)
        """
        return self.update(user_id, is_active=False)
    
    def verify_email(self, user_id: int) -> Optional[User]:
        """
        Mark a user's email as verified.
        
        Args:
            user_id: ID of the user to verify
            
        Returns:
            Updated user instance if found, None otherwise
            
        Example:
            user = user_service.verify_email(1)
        """
        return self.update(user_id, is_verified=True)
    
    def update_password(self, user_id: int, current_password: str, 
                       new_password: str) -> bool:
        """
        Update a user's password with current password verification.
        
        Args:
            user_id: ID of the user
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password was updated successfully
            
        Raises:
            ValueError: If current password is incorrect or new password is invalid
            
        Example:
            success = user_service.update_password(1, 'old_pass', 'new_pass')
        """
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not user.check_password(current_password):
            raise ValueError("Current password is incorrect")
        
        # Validate new password
        User.validate_password(new_password)
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        return True
    
    def search_users(self, query: str, include_inactive: bool = False) -> List[User]:
        """
        Search users by username, email, first name, or last name.
        
        Args:
            query: Search query string
            include_inactive: Whether to include inactive users
            
        Returns:
            List of matching user instances
            
        Example:
            users = user_service.search_users('john')
        """
        search_filter = f"%{query.lower()}%"
        
        db_query = self.db.session.query(User).filter(
            (User.username.ilike(search_filter)) |
            (User.email.ilike(search_filter)) |
            (User.first_name.ilike(search_filter)) |
            (User.last_name.ilike(search_filter))
        )
        
        if not include_inactive:
            db_query = db_query.filter(User.is_active == True)
        
        return db_query.order_by(User.username).all()
    
    def get_active_users(self, order_by: str = '-created_at') -> List[User]:
        """
        Get all active users.
        
        Args:
            order_by: Field to order by (prefix with '-' for descending)
            
        Returns:
            List of active user instances
            
        Example:
            active_users = user_service.get_active_users()
        """
        return self.get_all(filters={'is_active': True}, order_by=order_by)
    
    def get_verified_users(self, order_by: str = '-created_at') -> List[User]:
        """
        Get all verified users.
        
        Args:
            order_by: Field to order by (prefix with '-' for descending)
            
        Returns:
            List of verified user instances
            
        Example:
            verified_users = user_service.get_verified_users()
        """
        return self.get_all(filters={'is_verified': True}, order_by=order_by)
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing user statistics
            
        Raises:
            ValueError: If user not found
            
        Example:
            stats = user_service.get_user_statistics(1)
            # Returns: {
            #     'article_count': 5,
            #     'comment_count': 23,
            #     'published_articles': 3,
            #     'draft_articles': 2
            # }
        """
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        from app.models import Article, Comment, ArticleStatus
        
        # Count articles by status
        article_counts = self.db.session.query(Article.status, self.db.func.count(Article.id))\
            .filter(Article.author_id == user_id)\
            .group_by(Article.status)\
            .all()
        
        article_stats = {}
        total_articles = 0
        for status, count in article_counts:
            article_stats[f"{status.value}_articles"] = count
            total_articles += count
        
        # Count comments
        comment_count = self.db.session.query(Comment)\
            .filter(Comment.author_id == user_id)\
            .count()
        
        # Calculate total article views
        total_views = self.db.session.query(self.db.func.sum(Article.view_count))\
            .filter(Article.author_id == user_id)\
            .scalar() or 0
        
        return {
            'total_articles': total_articles,
            'total_comments': comment_count,
            'total_article_views': total_views,
            **article_stats
        }
    
    def get_user_activity_summary(self, user_id: int, 
                                 days: int = 30) -> Dict[str, Any]:
        """
        Get user activity summary for the specified number of days.
        
        Args:
            user_id: ID of the user
            days: Number of days to look back
            
        Returns:
            Dictionary containing activity summary
            
        Example:
            activity = user_service.get_user_activity_summary(1, days=30)
        """
        from datetime import datetime, timedelta
        from app.models import Article, Comment
        
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Recent articles
        recent_articles = self.db.session.query(Article)\
            .filter(Article.author_id == user_id)\
            .filter(Article.created_at >= cutoff_date)\
            .count()
        
        # Recent comments
        recent_comments = self.db.session.query(Comment)\
            .filter(Comment.author_id == user_id)\
            .filter(Comment.created_at >= cutoff_date)\
            .count()
        
        return {
            'period_days': days,
            'recent_articles': recent_articles,
            'recent_comments': recent_comments,
            'user_since': user.created_at.isoformat(),
            'last_activity': max(
                user.updated_at,
                # Could add last login timestamp here if implemented
            ).isoformat()
        }
    
    def paginate_users(self, page: int = 1, per_page: int = 20,
                      active_only: bool = True, verified_only: bool = False,
                      search_query: Optional[str] = None) -> PaginationResult:
        """
        Get paginated users with filtering options.
        
        Args:
            page: Page number
            per_page: Items per page
            active_only: Only include active users
            verified_only: Only include verified users
            search_query: Search query for username/email/name
            
        Returns:
            PaginationResult with users and pagination info
            
        Example:
            result = user_service.paginate_users(
                page=1, per_page=10, search_query='john'
            )
        """
        query = self.db.session.query(User)
        
        # Apply filters
        if active_only:
            query = query.filter(User.is_active == True)
        
        if verified_only:
            query = query.filter(User.is_verified == True)
        
        if search_query:
            search_filter = f"%{search_query.lower()}%"
            query = query.filter(
                (User.username.ilike(search_filter)) |
                (User.email.ilike(search_filter)) |
                (User.first_name.ilike(search_filter)) |
                (User.last_name.ilike(search_filter))
            )
        
        # Order by username
        query = query.order_by(User.username)
        
        # Calculate pagination
        total = query.count()
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        return PaginationResult(items, total, page, per_page)