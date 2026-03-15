from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from backend.models.db_models import User, Search, Status, AuthProvider
from datetime import datetime
from sqlalchemy import func, desc


class DatabaseService:
    """
    Service for handling database operations related to users and searches.
    """

    @staticmethod
    def create_user(db: Session, name: str, email: str, password_hash: str = "") -> User:
        """
        Create a new user in the database.
        """
        new_user = User(name=name, email=email, password_hash=password_hash)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    def update_last_login(db: Session, id: str) -> User:
        user = db.query(User).filter(User.user_id == id).first()
        if user:
            user.last_login = datetime.now()
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def update_user_password(db: Session, user_id: int, new_password_hash: str) -> bool:
        """
        Update user's password hash
        
        Args:
            db: Database session
            user_id: User ID
            new_password_hash: New bcrypt password hash
        
        Returns:
            True if updated successfully, False if user not found
        """
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        user.password_hash = new_password_hash
        db.commit()
        db.refresh(user)
        
        return True
    
    @staticmethod
    def getUserById(db: Session, user_id: int) -> User:
        """
        Retrieve a user by their ID.
        """
        users = db.query(User).filter(User.user_id == user_id).all()
        return users[0] if users else None
    
    @staticmethod
    def getUserByEmail(db: Session, email: str) -> User:
        """
        Retrieve a user by their email.
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def getUserByGoogleId(db: Session, google_id: str) -> Optional[User]:
        """
        Retrieve a user by their Google OAuth ID.

        Args:
            db: Database session
            google_id: Google OAuth ID

        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.google_id == google_id).first()

    @staticmethod
    def create_oauth_user(db: Session, name: str, email: str, google_id: str, auth_provider: str = AuthProvider.GOOGLE) -> User:
        """
        Create a new OAuth user (without password).

        Args:
            db: Database session
            name: User's display name
            email: User's email
            google_id: Google OAuth ID
            auth_provider: Authentication provider (default: GOOGLE)

        Returns:
            Created User object
        """
        new_user = User(
            name=name,
            email=email,
            google_id=google_id,
            auth_provider=auth_provider,
            password_hash=None  # OAuth users don't have passwords
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def update_or_create_google_user(db: Session, google_id: str, email: str, name: str) -> User:
        """
        Update existing Google user or create new one.

        Args:
            db: Database session
            google_id: Google OAuth ID
            email: User's email
            name: User's display name

        Returns:
            User object (created or updated)
        """
        # Try to find by google_id first
        user = DatabaseService.getUserByGoogleId(db, google_id)

        if user:
            # Update last login
            user.last_login = datetime.now()
            db.commit()
            db.refresh(user)
            return user

        # Check if email exists (might be a local account)
        user = DatabaseService.getUserByEmail(db, email)

        if user:
            # Link Google account to existing user
            user.google_id = google_id
            if user.auth_provider == AuthProvider.LOCAL:
                user.auth_provider = AuthProvider.GOOGLE  # Switch to Google auth
            user.last_login = datetime.now()
            db.commit()
            db.refresh(user)
            return user

        # Create new Google user
        return DatabaseService.create_oauth_user(db, name, email, google_id)  
    
    @staticmethod
    def create_search(db: Session, user_id: int, platforms: str, product_name: str, category: str = None, deep_details: bool = True, max_products: int = 80, include_reviews: bool = False, auto_generate_insights: bool = False) -> Search:
        """
        Create a new search record in the database.
        """
        search_id = str(uuid.uuid4())
        new_search = Search(
            search_id=search_id,
            user_id=user_id,
            platforms=platforms,
            product_name=product_name,
            category=category,
            deep_details=int(deep_details),
            max_products=max_products,
            include_reviews=int(include_reviews),
            auto_generate_insights=int(auto_generate_insights)
        )
        db.add(new_search)
        db.commit()
        db.refresh(new_search)
        return new_search
        
    
    @staticmethod
    def get_search_by_id(db: Session, search_id: str) -> Search:
        """
        Retrieve a search record by its ID.
        """
        return db.query(Search).filter(Search.search_id == search_id).first()
    
    @staticmethod
    def update_search_status(db: Session, search_id: str, status: Status) -> Search:
        """
        Update the status of a search record.
        """
        search = db.query(Search).filter(Search.search_id == search_id).first()
        if search:
            search.status = status
            if status == Status.COMPLETED or status == Status.FAILED:
                search.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(search)
        return search
    
    @staticmethod
    def update_started_at(db: Session, search_id: int) -> Search:
        """
        Update the started_at timestamp of a search record.
        """
        search = db.query(Search).filter(Search.search_id == search_id).first()
        if search:
            search.started_at = datetime.utcnow()
            db.commit()
            db.refresh(search)
        return search
    
    @staticmethod
    def update_completed_at(db: Session, search_id: int) -> Search:
        """
        Update the completed_at timestamp of a search record.
        """
        search = db.query(Search).filter(Search.search_id == search_id).first()
        if search:
            search.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(search)
        return search
    
    @staticmethod
    def update_output_path(db: Session, search_id: int, output_path: str) -> Search:
        """
        Update the output_path of a search record.
        """
        search = db.query(Search).filter(Search.search_id == search_id).first()
        if search:
            search.output_filename = output_path
            db.commit()
            db.refresh(search)
        return search

    @staticmethod
    def get_searches_by_user_id(db: Session, user_id: int, limit: int = 10, offset: int = 0) -> list[Search]:
        """
        Retrieve all search records for a given user ID.
        """
        return db.query(Search).filter(Search.user_id == user_id).order_by(Search.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_search(db: Session, search_id: int) -> Search:
        """
        Retrieve a search record by its ID.
        """
        return db.query(Search).filter(Search.search_id == search_id).first()
    
    @staticmethod
    def get_all_users(db: Session, limit: int = 10, offset: int = 0) -> List[User]:
        """Get all users (paginated)"""
        return db.query(User)\
            .order_by(desc(User.created_at))\
            .limit(limit)\
            .offset(offset)\
            .all()

    @staticmethod
    def get_user_search_statistics(db: Session, user_id: int) -> dict:
        """
        Get aggregate statistics for user's searches

        Args:
            db: Database session
            user_id: User ID to get statistics for

        Returns:
            Dictionary with total, completed, in_progress, and failed counts
        """
        from sqlalchemy import case

        stats = db.query(
            func.count(Search.search_id).label('total'),
            func.sum(case((Search.status == Status.COMPLETED, 1), else_=0)).label('completed'),
            func.sum(case((Search.status.in_([Status.IN_PROGRESS, Status.PENDING]), 1), else_=0)).label('in_progress'),
            func.sum(case((Search.status == Status.FAILED, 1), else_=0)).label('failed'),
        ).filter(Search.user_id == user_id).first()

        return {
            'total': int(stats.total or 0),
            'completed': int(stats.completed or 0),
            'in_progress': int(stats.in_progress or 0),
            'failed': int(stats.failed or 0)
        }

    @staticmethod
    def update_total_products_scraped(db: Session, search_id: str, total_products: int) -> Search:
        """
        Update the total number of products scraped for a search record.
        """
        search = db.query(Search).filter(Search.search_id == search_id).first()
        if search:
            search.total_products_scraped = total_products
            db.commit()
            db.refresh(search)
        return search

    @staticmethod
    def update_insight_generated(db: Session, search_id: str, insight_generated: bool) -> Search:
        """
        Update the insight_generated flag for a search record.
        """
        search = db.query(Search).filter(Search.search_id == search_id).first()
        if search:
            search.insight_generated = int(insight_generated)
            db.commit()
            db.refresh(search)
        return search

    @staticmethod
    def update_data_quality_passed(db: Session, search_id: str, data_quality_passed: bool) -> Search:
        """
        Update the data_quality_passed flag for a search record.
        """
        search = db.query(Search).filter(Search.search_id == search_id).first()
        if search:
            search.data_quality_passed = int(data_quality_passed)
            db.commit()
            db.refresh(search)
        return search

