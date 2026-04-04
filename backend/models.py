"""SQLAlchemy models for database."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    date_ideas = relationship("DateIdea", back_populates="user", cascade="all, delete-orphan")
    date_reviews = relationship("DateReview", back_populates="user", cascade="all, delete-orphan")


class UserPreferences(Base):
    """User preferences model."""
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Budget
    budget_min = Column(Integer, default=20)
    budget_max = Column(Integer, default=150)
    currency = Column(String(10), default="USD")
    
    # Location
    city = Column(String(255), default="")
    state = Column(String(255), default="")
    zip_code = Column(String(10), default="")
    radius_miles = Column(Integer, default=10)
    
    # Preferences (JSON arrays)
    activity_types = Column(JSON, default=[])  # ["outdoor", "dining", ...]
    her_interests = Column(JSON, default=[])   # ["hiking", "museums", ...]
    dietary_restrictions = Column(JSON, default=[])
    
    # Duration
    available_duration_min = Column(Integer, default=1)  # hours
    available_duration_max = Column(Integer, default=3)
    
    # Seasonal
    seasonal_outdoor_preferred = Column(Boolean, default=True)
    seasonal_indoor_preferred = Column(Boolean, default=False)
    weather_tolerance = Column(String(50), default="medium")  # low, medium, high
    
    # Notes
    notes = Column(Text, default="")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="preferences")


class DateIdea(Base):
    """Generated date idea."""
    __tablename__ = "date_ideas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Idea details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    location = Column(String(255), nullable=False)
    
    # Classification
    activity_types = Column(JSON, default=[])
    difficulty = Column(String(50), default="medium")  # easy, medium, hard
    season = Column(String(100), default="any")
    
    # External links
    maps_link = Column(String(1000), nullable=True)
    
    # Search context
    search_results = Column(JSON, default=[])  # Raw search results for citations
    
    # ML/reasoning
    reasoning = Column(Text, nullable=False)  # Why this was suggested
    confidence = Column(Float, default=0.5)  # 0-1
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="date_ideas")
    reviews = relationship("DateReview", back_populates="date_idea", cascade="all, delete-orphan")


class DateReview(Base):
    """Review of a date after it happened."""
    __tablename__ = "date_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date_idea_id = Column(UUID(as_uuid=True), ForeignKey("date_ideas.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Rating and feedback
    rating = Column(Integer, nullable=False)  # 1-5
    did_you_go = Column(Boolean, default=True)
    went_well = Column(Text, default="")
    could_improve = Column(Text, default="")
    would_recommend = Column(Boolean, default=True)
    
    # Learning
    new_insights = Column(Text, default="")
    tags_learned = Column(JSON, default=[])  # Inferred interests
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    date_idea = relationship("DateIdea", back_populates="reviews")
    user = relationship("User", back_populates="date_reviews")
