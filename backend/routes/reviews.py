"""Reviews and ratings routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import DateReview, DateIdea, UserPreferences
from schemas import DateReviewCreate, DateReviewUpdate, DateReviewResponse
from services.preference_learn import update_activity_weights, get_top_activities
import jwt

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=DateReviewResponse)
def create_review(review: DateReviewCreate, token: str = "", db: Session = Depends(get_db)):
    """Submit a review for a date idea."""
    try:
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Verify idea exists and belongs to user
    idea = db.query(DateIdea).filter(
        DateIdea.id == review.date_idea_id,
        DateIdea.user_id == user_id
    ).first()
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    # Create review
    db_review = DateReview(
        date_idea_id=idea.id,
        user_id=user_id,
        rating=review.rating,
        did_you_go=review.did_you_go,
        went_well=review.went_well,
        could_improve=review.could_improve,
        would_recommend=review.would_recommend,
        new_insights=review.new_insights,
        tags_learned=review.tags_learned,
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Update preference weights based on this review
    update_activity_weights(db, user_id, str(idea.id), review.rating)
    
    return db_review


@router.get("")
def list_reviews(skip: int = 0, limit: int = 20, token: str = "", db: Session = Depends(get_db)):
    """List user's reviews."""
    try:
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    reviews = (
        db.query(DateReview)
        .filter(DateReview.user_id == user_id)
        .order_by(DateReview.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": str(review.id),
            "date_idea_id": str(review.date_idea_id),
            "rating": review.rating,
            "went_well": review.went_well,
            "created_at": review.created_at,
        }
        for review in reviews
    ]


@router.patch("/{review_id}", response_model=DateReviewResponse)
def update_review(review_id: str, review: DateReviewUpdate, token: str = "", db: Session = Depends(get_db)):
    """Update a review."""
    try:
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db_review = db.query(DateReview).filter(
        DateReview.id == review_id,
        DateReview.user_id == user_id
    ).first()
    
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Update fields
    update_data = review.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_review, key, value)
    
    db.commit()
    db.refresh(db_review)
    
    return db_review


@router.get("/analytics/top-activities")
def get_top_activities_endpoint(token: str = "", db: Session = Depends(get_db)):
    """Get top-rated activities for this user."""
    try:
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    top_activities = get_top_activities(db, user_id, limit=10)
    
    return {"top_activities": top_activities}


@router.get("/analytics/trends")
def get_trends(token: str = "", db: Session = Depends(get_db)):
    """Get preference trends over time (placeholder)."""
    try:
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    reviews = (
        db.query(DateReview)
        .filter(DateReview.user_id == user_id)
        .order_by(DateReview.created_at)
        .all()
    )
    
    # Simple trend: average rating over time
    if not reviews:
        return {"trends": []}
    
    # Group by week or month (for now, just return all)
    return {
        "trends": [
            {
                "date": review.created_at.isoformat(),
                "rating": review.rating,
            }
            for review in reviews
        ]
    }
