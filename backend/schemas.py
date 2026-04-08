"""Pydantic schemas for request/response validation."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Preference Schemas
class UserPreferencesBase(BaseModel):
    budget_min: Optional[int] = 20
    budget_max: Optional[int] = 150
    currency: Optional[str] = "USD"
    city: Optional[str] = ""
    state: Optional[str] = ""
    zip_code: Optional[str] = ""
    radius_miles: Optional[int] = 10
    activity_types: Optional[List[str]] = []
    her_interests: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []
    available_duration_min: Optional[int] = 1
    available_duration_max: Optional[int] = 3
    seasonal_outdoor_preferred: Optional[bool] = True
    seasonal_indoor_preferred: Optional[bool] = False
    weather_tolerance: Optional[str] = "medium"
    notes: Optional[str] = ""


class UserPreferencesCreate(UserPreferencesBase):
    pass


class UserPreferencesUpdate(BaseModel):
    """Partial update schema."""
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    city: Optional[str] = None
    activity_types: Optional[List[str]] = None
    her_interests: Optional[List[str]] = None
    notes: Optional[str] = None


class UserPreferencesResponse(UserPreferencesBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Idea Schemas
class DateIdeaBase(BaseModel):
    title: str
    description: str
    estimated_cost: float
    duration_minutes: int
    location: str
    activity_types: Optional[List[str]] = []
    difficulty: Optional[str] = "medium"
    season: Optional[str] = "any"
    reasoning: str
    confidence: Optional[float] = 0.5


class IdeaStop(BaseModel):
    name: str
    url: str
    source_domain: Optional[str] = ""
    reliability: Optional[float] = 0.0
    freshness: Optional[float] = 0.0
    neighborhood: Optional[str] = ""


class IdeaVerification(BaseModel):
    status: Optional[str] = "unknown"
    avg_source_reliability: Optional[float] = 0.0
    avg_freshness: Optional[float] = 0.0
    provider_verified_count: Optional[int] = 0


class DateIdeaCreate(DateIdeaBase):
    pass


class DateIdeaResponse(DateIdeaBase):
    id: str
    user_id: str
    maps_link: Optional[str] = None
    stops: Optional[List[IdeaStop]] = []
    verification: Optional[IdeaVerification] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Review Schemas
class DateReviewBase(BaseModel):
    rating: int  # 1-5
    did_you_go: Optional[bool] = True
    went_well: Optional[str] = ""
    could_improve: Optional[str] = ""
    would_recommend: Optional[bool] = True
    new_insights: Optional[str] = ""
    tags_learned: Optional[List[str]] = []


class DateReviewCreate(BaseModel):
    date_idea_id: str
    rating: int
    did_you_go: Optional[bool] = True
    went_well: Optional[str] = ""
    could_improve: Optional[str] = ""
    would_recommend: Optional[bool] = True
    new_insights: Optional[str] = ""
    tags_learned: Optional[List[str]] = []


class DateReviewUpdate(BaseModel):
    rating: Optional[int] = None
    went_well: Optional[str] = None
    could_improve: Optional[str] = None
    would_recommend: Optional[bool] = None
    new_insights: Optional[str] = None


class DateReviewResponse(DateReviewBase):
    id: str
    date_idea_id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics Schemas
class ActivityScore(BaseModel):
    activity: str
    avg_rating: float
    count: int


class TopActivitiesResponse(BaseModel):
    top_activities: List[ActivityScore]


# Curated catalog schemas
class CuratedVenueBase(BaseModel):
    city: str
    category: str
    name: str
    url: str
    snippet: Optional[str] = ""
    curated_rank: Optional[int] = 50
    estimated_cost: Optional[float] = None
    tags: Optional[List[str]] = []
    opening_date: Optional[date] = None
    event_date: Optional[datetime] = None
    is_active: Optional[bool] = True


class CuratedVenueCreate(CuratedVenueBase):
    pass


class CuratedVenueUpdate(BaseModel):
    category: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    curated_rank: Optional[int] = None
    estimated_cost: Optional[float] = None
    tags: Optional[List[str]] = None
    opening_date: Optional[date] = None
    event_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class CuratedVenueResponse(CuratedVenueBase):
    id: str
    source_domain: Optional[str] = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
