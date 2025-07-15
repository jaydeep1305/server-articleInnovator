"""
Article service module for the Blog Microservice.

This module implements business logic for article management including
publishing, searching, categorization, and analytics.

Classes:
    ArticleService: Service class for article-related operations
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

from app.models import Article, ArticleStatus, User
from .base_service import BaseService, PaginationResult


class ArticleService(BaseService[Article]):
    """
    Service class for article-related business logic operations.
    
    This service handles article creation, publishing, searching, and analytics
    with proper validation and error handling.
    
    Methods:
        create_article: Create a new article
        publish_article: Publish an article
        unpublish_article: Unpublish an article
        archive_article: Archive an article
        get_by_slug: Get article by slug
        get_published_articles: Get all published articles
        get_featured_articles: Get featured articles
        search_articles: Search articles by various criteria
        get_articles_by_author: Get articles by author
        get_articles_by_category: Get articles by category
        get_popular_articles: Get articles by view count
        increment_view_count: Increment article view count
        get_article_analytics: Get article analytics
    """
    
    def __init__(self, db: SQLAlchemy):
        """
        Initialize the ArticleService.
        
        Args:
            db: SQLAlchemy database instance
        """
        super().__init__(Article, db)
    
    def create_article(self, title: str, content: str, author_id: int,
                      **kwargs) -> Article:
        """
        Create a new article with validation.
        
        Args:
            title: Article title
            content: Article content
            author_id: ID of the author
            **kwargs: Additional article attributes
            
        Returns:
            Created article instance
            
        Raises:
            ValueError: If validation fails or author not found
            
        Example:
            article = article_service.create_article(
                title='My First Article',
                content='This is the content...',
                author_id=1,
                excerpt='Short description',
                category='Technology'
            )
        """
        # Verify author exists
        author = self.db.session.get(User, author_id)
        if not author:
            raise ValueError(f"Author with ID {author_id} not found")
        
        # Check if slug already exists (if provided)
        if 'slug' in kwargs:
            if self.exists(slug=kwargs['slug']):
                raise ValueError(f"Article with slug '{kwargs['slug']}' already exists")
        else:
            # Generate unique slug
            base_slug = Article.generate_slug(title)
            slug = base_slug
            counter = 1
            while self.exists(slug=slug):
                slug = f"{base_slug}-{counter}"
                counter += 1
            kwargs['slug'] = slug
        
        return self.create(title=title, content=content, author_id=author_id, **kwargs)
    
    def publish_article(self, article_id: int) -> Optional[Article]:
        """
        Publish an article by changing its status.
        
        Args:
            article_id: ID of the article to publish
            
        Returns:
            Updated article instance if found, None otherwise
            
        Example:
            article = article_service.publish_article(1)
        """
        article = self.get_by_id(article_id)
        if not article:
            return None
        
        article.publish()
        article.save()
        return article
    
    def unpublish_article(self, article_id: int) -> Optional[Article]:
        """
        Unpublish an article by changing its status to draft.
        
        Args:
            article_id: ID of the article to unpublish
            
        Returns:
            Updated article instance if found, None otherwise
            
        Example:
            article = article_service.unpublish_article(1)
        """
        article = self.get_by_id(article_id)
        if not article:
            return None
        
        article.unpublish()
        article.save()
        return article
    
    def archive_article(self, article_id: int) -> Optional[Article]:
        """
        Archive an article by changing its status.
        
        Args:
            article_id: ID of the article to archive
            
        Returns:
            Updated article instance if found, None otherwise
            
        Example:
            article = article_service.archive_article(1)
        """
        article = self.get_by_id(article_id)
        if not article:
            return None
        
        article.archive()
        article.save()
        return article
    
    def get_by_slug(self, slug: str, published_only: bool = True) -> Optional[Article]:
        """
        Get an article by its slug.
        
        Args:
            slug: Article slug
            published_only: Only return published articles
            
        Returns:
            Article instance if found, None otherwise
            
        Example:
            article = article_service.get_by_slug('my-first-article')
        """
        query = self.db.session.query(Article).filter(Article.slug == slug)
        
        if published_only:
            query = query.filter(Article.status == ArticleStatus.PUBLISHED)
        
        return query.first()
    
    def get_published_articles(self, order_by: str = '-published_at',
                              include_featured: bool = True) -> List[Article]:
        """
        Get all published articles.
        
        Args:
            order_by: Field to order by (prefix with '-' for descending)
            include_featured: Whether to include featured articles
            
        Returns:
            List of published article instances
            
        Example:
            articles = article_service.get_published_articles()
        """
        filters = {'status': ArticleStatus.PUBLISHED}
        return self.get_all(filters=filters, order_by=order_by)
    
    def get_featured_articles(self, limit: Optional[int] = None) -> List[Article]:
        """
        Get featured articles that are published.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of featured article instances
            
        Example:
            featured = article_service.get_featured_articles(limit=5)
        """
        query = self.db.session.query(Article).filter(
            Article.status == ArticleStatus.PUBLISHED,
            Article.is_featured == True
        ).order_by(Article.published_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def search_articles(self, query: str, published_only: bool = True,
                       search_content: bool = False) -> List[Article]:
        """
        Search articles by title, excerpt, and optionally content.
        
        Args:
            query: Search query string
            published_only: Only search published articles
            search_content: Whether to search in article content
            
        Returns:
            List of matching article instances
            
        Example:
            articles = article_service.search_articles('python programming')
        """
        search_filter = f"%{query.lower()}%"
        
        db_query = self.db.session.query(Article)
        
        # Build search conditions
        search_conditions = [
            Article.title.ilike(search_filter),
            Article.excerpt.ilike(search_filter),
            Article.tags.ilike(search_filter)
        ]
        
        if search_content:
            search_conditions.append(Article.content.ilike(search_filter))
        
        db_query = db_query.filter(self.db.or_(*search_conditions))
        
        if published_only:
            db_query = db_query.filter(Article.status == ArticleStatus.PUBLISHED)
        
        return db_query.order_by(Article.published_at.desc()).all()
    
    def get_articles_by_author(self, author_id: int, 
                              published_only: bool = False) -> List[Article]:
        """
        Get articles by a specific author.
        
        Args:
            author_id: ID of the author
            published_only: Only return published articles
            
        Returns:
            List of article instances by the author
            
        Example:
            articles = article_service.get_articles_by_author(1)
        """
        filters = {'author_id': author_id}
        if published_only:
            filters['status'] = ArticleStatus.PUBLISHED
        
        return self.get_all(filters=filters, order_by='-created_at')
    
    def get_articles_by_category(self, category: str, 
                                published_only: bool = True) -> List[Article]:
        """
        Get articles by category.
        
        Args:
            category: Category name
            published_only: Only return published articles
            
        Returns:
            List of article instances in the category
            
        Example:
            articles = article_service.get_articles_by_category('Technology')
        """
        filters = {'category': category}
        if published_only:
            filters['status'] = ArticleStatus.PUBLISHED
        
        return self.get_all(filters=filters, order_by='-published_at')
    
    def get_articles_by_tag(self, tag: str, published_only: bool = True) -> List[Article]:
        """
        Get articles that contain a specific tag.
        
        Args:
            tag: Tag to search for
            published_only: Only return published articles
            
        Returns:
            List of article instances containing the tag
            
        Example:
            articles = article_service.get_articles_by_tag('python')
        """
        query = self.db.session.query(Article).filter(
            Article.tags.ilike(f"%{tag.lower()}%")
        )
        
        if published_only:
            query = query.filter(Article.status == ArticleStatus.PUBLISHED)
        
        return query.order_by(Article.published_at.desc()).all()
    
    def get_popular_articles(self, limit: int = 10, 
                           days: Optional[int] = None) -> List[Article]:
        """
        Get popular articles based on view count.
        
        Args:
            limit: Maximum number of articles to return
            days: Limit to articles published within this many days
            
        Returns:
            List of popular article instances
            
        Example:
            popular = article_service.get_popular_articles(limit=10, days=30)
        """
        query = self.db.session.query(Article).filter(
            Article.status == ArticleStatus.PUBLISHED
        )
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Article.published_at >= cutoff_date)
        
        return query.order_by(Article.view_count.desc()).limit(limit).all()
    
    def get_recent_articles(self, limit: int = 10) -> List[Article]:
        """
        Get recently published articles.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of recent article instances
            
        Example:
            recent = article_service.get_recent_articles(limit=5)
        """
        return self.db.session.query(Article).filter(
            Article.status == ArticleStatus.PUBLISHED
        ).order_by(Article.published_at.desc()).limit(limit).all()
    
    def increment_view_count(self, article_id: int) -> Optional[Article]:
        """
        Increment the view count for an article.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Updated article instance if found, None otherwise
            
        Example:
            article = article_service.increment_view_count(1)
        """
        article = self.get_by_id(article_id)
        if not article:
            return None
        
        article.increment_view_count()
        article.save()
        return article
    
    def get_article_analytics(self, article_id: int) -> Dict[str, Any]:
        """
        Get comprehensive analytics for an article.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Dictionary containing article analytics
            
        Raises:
            ValueError: If article not found
            
        Example:
            analytics = article_service.get_article_analytics(1)
        """
        article = self.get_by_id(article_id)
        if not article:
            raise ValueError("Article not found")
        
        from app.models import Comment
        
        # Get comment statistics
        total_comments = self.db.session.query(Comment)\
            .filter(Comment.article_id == article_id)\
            .count()
        
        approved_comments = self.db.session.query(Comment)\
            .filter(Comment.article_id == article_id)\
            .filter(Comment.status == 'approved')\
            .count()
        
        # Calculate engagement metrics
        days_since_published = 0
        if article.published_at:
            days_since_published = (datetime.utcnow() - article.published_at).days
        
        return {
            'article_id': article.id,
            'title': article.title,
            'status': article.status.value,
            'view_count': article.view_count,
            'total_comments': total_comments,
            'approved_comments': approved_comments,
            'is_featured': article.is_featured,
            'days_since_published': days_since_published,
            'reading_time': article.get_reading_time(),
            'word_count': len(article.content.split()) if article.content else 0,
            'tags': article.get_tags_list(),
            'category': article.category
        }
    
    def get_category_statistics(self) -> Dict[str, int]:
        """
        Get statistics for all categories.
        
        Returns:
            Dictionary mapping category names to article counts
            
        Example:
            stats = article_service.get_category_statistics()
            # Returns: {'Technology': 15, 'Science': 8, 'Business': 12}
        """
        results = self.db.session.query(
            Article.category, self.db.func.count(Article.id)
        ).filter(
            Article.status == ArticleStatus.PUBLISHED,
            Article.category.isnot(None)
        ).group_by(Article.category).all()
        
        return {category: count for category, count in results}
    
    def get_tag_statistics(self, limit: int = 20) -> Dict[str, int]:
        """
        Get statistics for tags across all articles.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            Dictionary mapping tag names to usage counts
            
        Example:
            stats = article_service.get_tag_statistics(limit=10)
        """
        # Get all published articles with tags
        articles = self.db.session.query(Article.tags).filter(
            Article.status == ArticleStatus.PUBLISHED,
            Article.tags.isnot(None)
        ).all()
        
        # Count tag occurrences
        tag_counts = {}
        for (tags_str,) in articles:
            if tags_str:
                tags = [tag.strip().lower() for tag in tags_str.split(',')]
                for tag in tags:
                    if tag:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort by count and return top tags
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_tags[:limit])
    
    def paginate_articles(self, page: int = 1, per_page: int = 20,
                         status: Optional[ArticleStatus] = None,
                         author_id: Optional[int] = None,
                         category: Optional[str] = None,
                         featured_only: bool = False,
                         search_query: Optional[str] = None) -> PaginationResult:
        """
        Get paginated articles with filtering options.
        
        Args:
            page: Page number
            per_page: Items per page
            status: Filter by article status
            author_id: Filter by author ID
            category: Filter by category
            featured_only: Only include featured articles
            search_query: Search query for title/content
            
        Returns:
            PaginationResult with articles and pagination info
            
        Example:
            result = article_service.paginate_articles(
                page=1, per_page=10, status=ArticleStatus.PUBLISHED
            )
        """
        query = self.db.session.query(Article)
        
        # Apply filters
        if status:
            query = query.filter(Article.status == status)
        
        if author_id:
            query = query.filter(Article.author_id == author_id)
        
        if category:
            query = query.filter(Article.category == category)
        
        if featured_only:
            query = query.filter(Article.is_featured == True)
        
        if search_query:
            search_filter = f"%{search_query.lower()}%"
            query = query.filter(
                (Article.title.ilike(search_filter)) |
                (Article.excerpt.ilike(search_filter)) |
                (Article.content.ilike(search_filter))
            )
        
        # Order by publication date for published articles, creation date for others
        if status == ArticleStatus.PUBLISHED:
            query = query.order_by(Article.published_at.desc())
        else:
            query = query.order_by(Article.created_at.desc())
        
        # Calculate pagination
        total = query.count()
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        return PaginationResult(items, total, page, per_page)