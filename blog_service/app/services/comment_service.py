"""
Comment service module for the Blog Microservice.

This module implements business logic for comment management including
moderation, threading, and spam detection.

Classes:
    CommentService: Service class for comment-related operations
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

from app.models import Comment, CommentStatus, Article, User
from .base_service import BaseService, PaginationResult


class CommentService(BaseService[Comment]):
    """
    Service class for comment-related business logic operations.
    
    This service handles comment creation, moderation, threading, and analytics
    with proper validation and error handling.
    
    Methods:
        create_comment: Create a new comment
        create_reply: Create a reply to a comment
        approve_comment: Approve a comment
        reject_comment: Reject a comment
        mark_as_spam: Mark comment as spam
        get_comments_by_article: Get comments for an article
        get_comments_by_author: Get comments by author
        get_pending_comments: Get comments pending moderation
        moderate_comment: Change comment moderation status
        get_comment_thread: Get full comment thread
        get_comment_analytics: Get comment analytics
    """
    
    def __init__(self, db: SQLAlchemy):
        """
        Initialize the CommentService.
        
        Args:
            db: SQLAlchemy database instance
        """
        super().__init__(Comment, db)
    
    def create_comment(self, content: str, article_id: int,
                      author_id: Optional[int] = None,
                      author_name: Optional[str] = None,
                      author_email: Optional[str] = None,
                      ip_address: Optional[str] = None) -> Comment:
        """
        Create a new comment with validation.
        
        Args:
            content: Comment content
            article_id: ID of the article being commented on
            author_id: ID of registered user (optional)
            author_name: Name for guest comment (required if no author_id)
            author_email: Email for guest comment (required if no author_id)
            ip_address: IP address of commenter (for moderation)
            
        Returns:
            Created comment instance
            
        Raises:
            ValueError: If validation fails or article not found
            
        Example:
            # Registered user comment
            comment = comment_service.create_comment(
                content='Great article!',
                article_id=1,
                author_id=2
            )
            
            # Guest comment
            comment = comment_service.create_comment(
                content='Nice post!',
                article_id=1,
                author_name='John Doe',
                author_email='john@example.com'
            )
        """
        # Verify article exists
        article = self.db.session.get(Article, article_id)
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")
        
        # Verify author exists if author_id provided
        if author_id:
            author = self.db.session.get(User, author_id)
            if not author:
                raise ValueError(f"User with ID {author_id} not found")
        
        # Validate guest comment requirements
        if not author_id and (not author_name or not author_email):
            raise ValueError("Guest comments require both author_name and author_email")
        
        comment_data = {
            'content': content,
            'article_id': article_id,
            'author_id': author_id,
            'author_name': author_name,
            'author_email': author_email,
            'ip_address': ip_address
        }
        
        # Auto-approve comments from verified users
        if author_id:
            author = self.db.session.get(User, author_id)
            if author and author.is_verified:
                comment_data['status'] = CommentStatus.APPROVED
        
        return self.create(**comment_data)
    
    def create_reply(self, content: str, parent_id: int,
                    author_id: Optional[int] = None,
                    author_name: Optional[str] = None,
                    author_email: Optional[str] = None,
                    ip_address: Optional[str] = None) -> Comment:
        """
        Create a reply to an existing comment.
        
        Args:
            content: Reply content
            parent_id: ID of the parent comment
            author_id: ID of registered user (optional)
            author_name: Name for guest reply (required if no author_id)
            author_email: Email for guest reply (required if no author_id)
            ip_address: IP address of commenter
            
        Returns:
            Created reply comment instance
            
        Raises:
            ValueError: If validation fails or parent comment not found
            
        Example:
            reply = comment_service.create_reply(
                content='I agree with your comment!',
                parent_id=5,
                author_id=3
            )
        """
        # Verify parent comment exists
        parent_comment = self.get_by_id(parent_id)
        if not parent_comment:
            raise ValueError(f"Parent comment with ID {parent_id} not found")
        
        # Create reply with same article_id as parent
        return self.create_comment(
            content=content,
            article_id=parent_comment.article_id,
            author_id=author_id,
            author_name=author_name,
            author_email=author_email,
            ip_address=ip_address
        ).update(parent_id=parent_id)
    
    def approve_comment(self, comment_id: int) -> Optional[Comment]:
        """
        Approve a comment for public display.
        
        Args:
            comment_id: ID of the comment to approve
            
        Returns:
            Updated comment instance if found, None otherwise
            
        Example:
            comment = comment_service.approve_comment(1)
        """
        comment = self.get_by_id(comment_id)
        if not comment:
            return None
        
        comment.approve()
        comment.save()
        return comment
    
    def reject_comment(self, comment_id: int) -> Optional[Comment]:
        """
        Reject a comment, hiding it from public display.
        
        Args:
            comment_id: ID of the comment to reject
            
        Returns:
            Updated comment instance if found, None otherwise
            
        Example:
            comment = comment_service.reject_comment(1)
        """
        comment = self.get_by_id(comment_id)
        if not comment:
            return None
        
        comment.reject()
        comment.save()
        return comment
    
    def mark_as_spam(self, comment_id: int) -> Optional[Comment]:
        """
        Mark a comment as spam.
        
        Args:
            comment_id: ID of the comment to mark as spam
            
        Returns:
            Updated comment instance if found, None otherwise
            
        Example:
            comment = comment_service.mark_as_spam(1)
        """
        comment = self.get_by_id(comment_id)
        if not comment:
            return None
        
        comment.mark_as_spam()
        comment.save()
        return comment
    
    def moderate_comment(self, comment_id: int, 
                        status: CommentStatus) -> Optional[Comment]:
        """
        Change the moderation status of a comment.
        
        Args:
            comment_id: ID of the comment to moderate
            status: New comment status
            
        Returns:
            Updated comment instance if found, None otherwise
            
        Example:
            comment = comment_service.moderate_comment(1, CommentStatus.APPROVED)
        """
        comment = self.get_by_id(comment_id)
        if not comment:
            return None
        
        comment.status = status
        comment.save()
        return comment
    
    def get_comments_by_article(self, article_id: int, 
                              approved_only: bool = True,
                              include_replies: bool = True) -> List[Comment]:
        """
        Get comments for a specific article.
        
        Args:
            article_id: ID of the article
            approved_only: Only return approved comments
            include_replies: Whether to include reply comments
            
        Returns:
            List of comment instances for the article
            
        Example:
            comments = comment_service.get_comments_by_article(1)
        """
        query = self.db.session.query(Comment).filter(
            Comment.article_id == article_id
        )
        
        if approved_only:
            query = query.filter(Comment.status == CommentStatus.APPROVED)
        
        if not include_replies:
            query = query.filter(Comment.parent_id.is_(None))
        
        return query.order_by(Comment.created_at.asc()).all()
    
    def get_comments_by_author(self, author_id: int,
                              approved_only: bool = False) -> List[Comment]:
        """
        Get comments by a specific author.
        
        Args:
            author_id: ID of the author
            approved_only: Only return approved comments
            
        Returns:
            List of comment instances by the author
            
        Example:
            comments = comment_service.get_comments_by_author(1)
        """
        filters = {'author_id': author_id}
        if approved_only:
            filters['status'] = CommentStatus.APPROVED
        
        return self.get_all(filters=filters, order_by='-created_at')
    
    def get_pending_comments(self, limit: Optional[int] = None) -> List[Comment]:
        """
        Get comments pending moderation.
        
        Args:
            limit: Maximum number of comments to return
            
        Returns:
            List of pending comment instances
            
        Example:
            pending = comment_service.get_pending_comments(limit=20)
        """
        query = self.db.session.query(Comment).filter(
            Comment.status == CommentStatus.PENDING
        ).order_by(Comment.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_recent_comments(self, limit: int = 10, 
                           approved_only: bool = True) -> List[Comment]:
        """
        Get recently posted comments.
        
        Args:
            limit: Maximum number of comments to return
            approved_only: Only return approved comments
            
        Returns:
            List of recent comment instances
            
        Example:
            recent = comment_service.get_recent_comments(limit=5)
        """
        query = self.db.session.query(Comment)
        
        if approved_only:
            query = query.filter(Comment.status == CommentStatus.APPROVED)
        
        return query.order_by(Comment.created_at.desc()).limit(limit).all()
    
    def get_comment_thread(self, comment_id: int, 
                          approved_only: bool = True) -> List[Comment]:
        """
        Get the full thread for a comment (parent and all replies).
        
        Args:
            comment_id: ID of the comment
            approved_only: Only return approved comments
            
        Returns:
            List of comments in the thread (parent first, then replies)
            
        Example:
            thread = comment_service.get_comment_thread(1)
        """
        comment = self.get_by_id(comment_id)
        if not comment:
            return []
        
        # Find the root comment
        root_comment = comment
        while root_comment.parent_id:
            root_comment = self.get_by_id(root_comment.parent_id)
            if not root_comment:
                break
        
        if not root_comment:
            return []
        
        # Get all replies in the thread
        query = self.db.session.query(Comment).filter(
            (Comment.id == root_comment.id) |
            (Comment.parent_id == root_comment.id)
        )
        
        if approved_only:
            query = query.filter(Comment.status == CommentStatus.APPROVED)
        
        return query.order_by(Comment.created_at.asc()).all()
    
    def search_comments(self, query: str, approved_only: bool = True) -> List[Comment]:
        """
        Search comments by content.
        
        Args:
            query: Search query string
            approved_only: Only search approved comments
            
        Returns:
            List of matching comment instances
            
        Example:
            results = comment_service.search_comments('great article')
        """
        search_filter = f"%{query.lower()}%"
        
        db_query = self.db.session.query(Comment).filter(
            Comment.content.ilike(search_filter)
        )
        
        if approved_only:
            db_query = db_query.filter(Comment.status == CommentStatus.APPROVED)
        
        return db_query.order_by(Comment.created_at.desc()).all()
    
    def get_comment_analytics(self, article_id: Optional[int] = None,
                             days: int = 30) -> Dict[str, Any]:
        """
        Get comment analytics for an article or overall.
        
        Args:
            article_id: ID of specific article (None for overall analytics)
            days: Number of days to analyze
            
        Returns:
            Dictionary containing comment analytics
            
        Example:
            analytics = comment_service.get_comment_analytics(article_id=1)
        """
        query = self.db.session.query(Comment)
        
        if article_id:
            query = query.filter(Comment.article_id == article_id)
        
        # Get status counts
        status_counts = query.with_entities(
            Comment.status, 
            self.db.func.count(Comment.id)
        ).group_by(Comment.status).all()
        
        status_stats = {}
        total_comments = 0
        for status, count in status_counts:
            status_stats[f"{status.value}_comments"] = count
            total_comments += count
        
        # Get recent activity
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_comments = query.filter(
            Comment.created_at >= cutoff_date
        ).count()
        
        # Get top commenters
        top_commenters = self.db.session.query(
            Comment.author_id,
            self.db.func.count(Comment.id).label('comment_count')
        ).filter(
            Comment.author_id.isnot(None),
            Comment.status == CommentStatus.APPROVED
        )
        
        if article_id:
            top_commenters = top_commenters.filter(Comment.article_id == article_id)
        
        top_commenters = top_commenters.group_by(Comment.author_id)\
            .order_by(self.db.func.count(Comment.id).desc())\
            .limit(5).all()
        
        return {
            'total_comments': total_comments,
            'recent_comments_count': recent_comments,
            'analysis_period_days': days,
            'top_commenters': [
                {'author_id': author_id, 'comment_count': count}
                for author_id, count in top_commenters
            ],
            **status_stats
        }
    
    def get_moderation_queue(self, page: int = 1, 
                           per_page: int = 20) -> PaginationResult:
        """
        Get paginated list of comments requiring moderation.
        
        Args:
            page: Page number
            per_page: Items per page
            
        Returns:
            PaginationResult with pending comments
            
        Example:
            queue = comment_service.get_moderation_queue(page=1, per_page=10)
        """
        query = self.db.session.query(Comment).filter(
            Comment.status == CommentStatus.PENDING
        ).order_by(Comment.created_at.asc())
        
        # Calculate pagination
        total = query.count()
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        return PaginationResult(items, total, page, per_page)
    
    def bulk_moderate_comments(self, comment_ids: List[int], 
                              status: CommentStatus) -> int:
        """
        Moderate multiple comments at once.
        
        Args:
            comment_ids: List of comment IDs to moderate
            status: New status for all comments
            
        Returns:
            Number of comments successfully moderated
            
        Example:
            moderated = comment_service.bulk_moderate_comments(
                [1, 2, 3], CommentStatus.APPROVED
            )
        """
        try:
            updated = self.db.session.query(Comment)\
                .filter(Comment.id.in_(comment_ids))\
                .update({'status': status}, synchronize_session=False)
            
            self.db.session.commit()
            return updated
        except Exception as e:
            self.db.session.rollback()
            raise e
    
    def delete_spam_comments(self, days_old: int = 30) -> int:
        """
        Delete comments marked as spam that are older than specified days.
        
        Args:
            days_old: Delete spam comments older than this many days
            
        Returns:
            Number of comments deleted
            
        Example:
            deleted = comment_service.delete_spam_comments(days_old=7)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        try:
            deleted = self.db.session.query(Comment)\
                .filter(
                    Comment.status == CommentStatus.SPAM,
                    Comment.created_at < cutoff_date
                ).delete(synchronize_session=False)
            
            self.db.session.commit()
            return deleted
        except Exception as e:
            self.db.session.rollback()
            raise e
    
    def paginate_comments(self, page: int = 1, per_page: int = 20,
                         article_id: Optional[int] = None,
                         author_id: Optional[int] = None,
                         status: Optional[CommentStatus] = None,
                         search_query: Optional[str] = None) -> PaginationResult:
        """
        Get paginated comments with filtering options.
        
        Args:
            page: Page number
            per_page: Items per page
            article_id: Filter by article ID
            author_id: Filter by author ID
            status: Filter by comment status
            search_query: Search query for content
            
        Returns:
            PaginationResult with comments and pagination info
            
        Example:
            result = comment_service.paginate_comments(
                page=1, per_page=10, status=CommentStatus.APPROVED
            )
        """
        query = self.db.session.query(Comment)
        
        # Apply filters
        if article_id:
            query = query.filter(Comment.article_id == article_id)
        
        if author_id:
            query = query.filter(Comment.author_id == author_id)
        
        if status:
            query = query.filter(Comment.status == status)
        
        if search_query:
            search_filter = f"%{search_query.lower()}%"
            query = query.filter(Comment.content.ilike(search_filter))
        
        # Order by creation date
        query = query.order_by(Comment.created_at.desc())
        
        # Calculate pagination
        total = query.count()
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        return PaginationResult(items, total, page, per_page)