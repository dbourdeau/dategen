"""Preferences routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserPreferences
from schemas import UserPreferencesCreate, UserPreferencesUpdate, UserPreferencesResponse
from routes.auth import get_current_user
import jwt

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferencesResponse)
def get_preferences(token: str = "", db: Session = Depends(get_db)):
    """Get user's current preferences."""
    try:
        # Extract user ID from token
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    return prefs


@router.post("", response_model=UserPreferencesResponse)
def create_preferences(preferences: UserPreferencesCreate, token: str = "", db: Session = Depends(get_db)):
    """Create or update user preferences."""
    try:
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check if preferences exist
    existing = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    
    if existing:
        # Update existing
        for key, value in preferences.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        db_prefs = UserPreferences(user_id=user_id, **preferences.dict())
        db.add(db_prefs)
        db.commit()
        db.refresh(db_prefs)
        return db_prefs


@router.patch("", response_model=UserPreferencesResponse)
def update_preferences(preferences: UserPreferencesUpdate, token: str = "", db: Session = Depends(get_db)):
    """Partially update preferences."""
    try:
        payload = jwt.decode(token, "your-secret-key-change-in-production", algorithms=["HS256"])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if not db_prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    # Update only provided fields
    update_data = preferences.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prefs, key, value)
    
    db.commit()
    db.refresh(db_prefs)
    return db_prefs
