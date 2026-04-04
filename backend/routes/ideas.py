"""Ideas generation routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserPreferences, DateIdea
from routes.auth import get_current_user
from services.serp_search import search_all
from services.llm_synthesis import synthesize_ideas
from services.preference_learn import _calculate_weights_from_reviews

router = APIRouter(prefix="/api/ideas", tags=["ideas"])


@router.post("/generate")
async def generate_ideas(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate new date ideas based on user preferences."""
    user_id = current_user.id
    
    # Fetch user preferences
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if not prefs:
        raise HTTPException(status_code=404, detail="Please set your preferences first")
    
    if not prefs.city:
        raise HTTPException(status_code=400, detail="City is required in preferences")
    
    # Load activity weights from past reviews
    activity_weights = _calculate_weights_from_reviews(db, user_id)
    
    # Fetch past high-rated ideas (for context)
    past_ideas = (
        db.query(DateIdea)
        .filter(DateIdea.user_id == user_id)
        .order_by(DateIdea.created_at.desc())
        .limit(3)
        .all()
    )
    
    try:
        # Parallel web search
        search_results = await search_all(
            city=prefs.city,
            budget=prefs.budget_max,
            interests=prefs.her_interests,
            restrictions=prefs.dietary_restrictions,
        )

        # LLM synthesis
        ideas = await synthesize_ideas(
            city=prefs.city,
            budget_min=prefs.budget_min,
            budget_max=prefs.budget_max,
            duration_min=prefs.available_duration_min,
            duration_max=prefs.available_duration_max,
            her_interests=prefs.her_interests,
            activity_types=prefs.activity_types,
            dietary_restrictions=prefs.dietary_restrictions,
            search_results=search_results,
            past_high_rated_ideas=[
                {
                    "title": idea.title,
                    "description": idea.description,
                }
                for idea in past_ideas
            ],
            activity_weights=activity_weights,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Idea generation failed: {e}")
    
    # Save ideas to database
    saved_ideas = []
    for idea_data in ideas:
        db_idea = DateIdea(
            user_id=user_id,
            title=idea_data.get("title", ""),
            description=idea_data.get("description", ""),
            estimated_cost=idea_data.get("estimated_cost", 0),
            duration_minutes=idea_data.get("duration_minutes", 0),
            location=idea_data.get("location", prefs.city),
            activity_types=idea_data.get("activity_types", []),
            difficulty=idea_data.get("difficulty", "medium"),
            season=idea_data.get("season", "any"),
            reasoning=idea_data.get("reasoning", ""),
            confidence=idea_data.get("confidence", 0.5),
            search_results=search_results,
        )
        db.add(db_idea)
        db.flush()  # Flush to get the ID without committing
        saved_ideas.append(db_idea)
    
    db.commit()
    
    # Refresh and return
    for idea in saved_ideas:
        db.refresh(idea)
    
    return [
        {
            "id": str(idea.id),
            "title": idea.title,
            "description": idea.description,
            "estimated_cost": idea.estimated_cost,
            "duration_minutes": idea.duration_minutes,
            "location": idea.location,
            "activity_types": idea.activity_types,
            "difficulty": idea.difficulty,
            "reasoning": idea.reasoning,
            "confidence": idea.confidence,
            "created_at": idea.created_at,
        }
        for idea in saved_ideas
    ]


@router.get("", response_model=list)
def list_ideas(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's generated ideas."""
    user_id = current_user.id
    
    ideas = (
        db.query(DateIdea)
        .filter(DateIdea.user_id == user_id)
        .order_by(DateIdea.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": str(idea.id),
            "title": idea.title,
            "description": idea.description,
            "estimated_cost": idea.estimated_cost,
            "duration_minutes": idea.duration_minutes,
            "location": idea.location,
            "confidence": idea.confidence,
            "created_at": idea.created_at,
        }
        for idea in ideas
    ]


@router.get("/{idea_id}")
def get_idea(idea_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific idea."""
    user_id = current_user.id
    
    idea = db.query(DateIdea).filter(
        DateIdea.id == idea_id,
        DateIdea.user_id == user_id
    ).first()
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "id": str(idea.id),
        "title": idea.title,
        "description": idea.description,
        "estimated_cost": idea.estimated_cost,
        "duration_minutes": idea.duration_minutes,
        "location": idea.location,
        "activity_types": idea.activity_types,
        "reasoning": idea.reasoning,
        "confidence": idea.confidence,
        "created_at": idea.created_at,
    }


@router.delete("/{idea_id}")
def delete_idea(idea_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete an idea."""
    user_id = current_user.id
    
    idea = db.query(DateIdea).filter(
        DateIdea.id == idea_id,
        DateIdea.user_id == user_id
    ).first()
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    db.delete(idea)
    db.commit()
    
    return {"message": "Idea deleted"}
