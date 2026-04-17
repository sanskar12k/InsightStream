from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.database.database import Base
from datetime import datetime
import enum

class Status(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    google_id = Column(String(255), unique=True, nullable=True, index=True)  # Google OAuth ID
    auth_provider = Column(Enum(AuthProvider, values_callable=lambda x: [e.value for e in x]), default=AuthProvider.LOCAL, nullable=False)  # Auth method
    last_login = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    max_limit = Column(Integer, default=1, nullable=False)  # Maximum allowed searches (1 for free users)
    current_limit = Column(Integer, default=0, nullable=False)  # Number of searches already performed


    searches = relationship("Search", back_populates="owner")    

class Search(Base):
    __tablename__ = 'searches'

    search_id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, index=True)
    platforms = Column(String(200), default="amazon", nullable=False)  # Comma-separated platforms
    product_name = Column(String(100), nullable=False)
    status = Column(Enum(Status), default=Status.PENDING, nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    deep_details = Column(Integer, default=0, nullable=False)  # 0 or 1
    max_products = Column(Integer, default=0, nullable=False)
    include_reviews = Column(Integer, nullable=False)  # 0 or 1
    total_products_scraped = Column(Integer, default=0, nullable=True)  # Actual number of products scraped
    insight_generated = Column(Integer, default=0, nullable=False)  # 0 or 1 - Whether insights have been generated
    auto_generate_insights = Column(Integer, default=0, nullable=False)  # 0 or 1 - Auto-generate insights after scraping
    data_quality_passed = Column(Integer, default=1, nullable=False)  # 0 or 1 - Whether data quality checks passed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    output_filename = Column(String(255), nullable=True)  # Path to the stored data file

    owner = relationship("User", back_populates="searches")