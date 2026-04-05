"""Preference learning and weighting service."""

import json
from typing import Dict, List
from sqlalchemy.orm import Session
from models import DateIdea, DateReview


def update_activity_weights(db: Session, user_id: str, date_idea_id: str, rating: int) -> Dict[str, float]:
    """
    Update activity type weights based on review rating.
    
    Higher ratings boost activity type weights; lower ratings reduce them.
    """
    # Fetch the idea to get its activity types
    idea = db.query(DateIdea).filter(DateIdea.id == date_idea_id).first()
    if not idea:
        return {}
    
    # Load current weights from Redis or calculate from reviews
    weights = _calculate_weights_from_reviews(db, user_id)
    
    # Update weights based on rating
    if rating >= 4:
        # Boost activities that were rated highly
        for activity in idea.activity_types:
            weights[activity] = weights.get(activity, 0) + 0.05
    elif rating <= 2:
        # Reduce activities that were rated poorly
        for activity in idea.activity_types:
            weights[activity] = weights.get(activity, 0) - 0.05
    
    # Normalize weights to 0-1
    max_weight = max(weights.values()) if weights else 1
    if max_weight > 1:
        weights = {k: v / max_weight for k, v in weights.items()}
    
    return weights


def _calculate_weights_from_reviews(db: Session, user_id: str) -> Dict[str, float]:
    """
    Calculate activity weights based on past reviews.
    
    Weight = average rating of ideas of each activity type.
    """
    # Fetch all reviews for this user
    reviews = (
        db.query(DateReview)
        .filter(DateReview.user_id == user_id)
        .all()
    )
    
    if not reviews:
        return {}
    
    # Group by activity type
    activity_ratings: Dict[str, List[int]] = {}
    
    for review in reviews:
        idea = review.date_idea
        if idea:
            for activity in idea.activity_types:
                if activity not in activity_ratings:
                    activity_ratings[activity] = []
                activity_ratings[activity].append(review.rating)
    
    # Calculate average weight for each activity
    weights = {}
    for activity, ratings in activity_ratings.items():
        avg_rating = sum(ratings) / len(ratings)
        # Normalize to 0-1 range (5 stars = 1.0 weight, 1 star = 0.2 weight)
        weights[activity] = (avg_rating - 1) / 4
    
    return weights


def get_top_activities(db: Session, user_id: str, limit: int = 5) -> List[Dict]:
    """
    Get top-rated activity types for this user.
    
    Returns: [{"activity": "hiking", "avg_rating": 4.8, "count": 5}, ...]
    """
    reviews = (
        db.query(DateReview)
        .filter(DateReview.user_id == user_id)
        .all()
    )
    
    if not reviews:
        return []
    
    activity_stats: Dict[str, Dict] = {}
    
    for review in reviews:
        idea = review.date_idea
        if idea:
            for activity in idea.activity_types:
                if activity not in activity_stats:
                    activity_stats[activity] = {"ratings": [], "count": 0}
                activity_stats[activity]["ratings"].append(review.rating)
                activity_stats[activity]["count"] += 1
    
    # Calculate averages
    result = []
    for activity, stats in activity_stats.items():
        avg_rating = sum(stats["ratings"]) / len(stats["ratings"])
        result.append({
            "activity": activity,
            "avg_rating": round(avg_rating, 2),
            "count": stats["count"],
        })
    
    # Sort by average rating (descending)
    result.sort(key=lambda x: x["avg_rating"], reverse=True)
    
    return result[:limit]


def get_context_preferences(db: Session, user_id: str) -> Dict:
    """Learn contextual preferences from past positively rated dates."""
    reviews = (
        db.query(DateReview)
        .filter(DateReview.user_id == user_id)
        .all()
    )

    if not reviews:
        return {
            "top_neighborhood_tokens": [],
            "preferred_duration_minutes": None,
        }

    neighborhood_counts: Dict[str, int] = {}
    durations: List[int] = []

    for review in reviews:
        if review.rating < 4:
            continue
        idea = review.date_idea
        if not idea:
            continue

        durations.append(idea.duration_minutes)
        location = (idea.location or "").replace("->", " ")
        for token in location.split():
            normalized = token.strip(",.()[]{}-").lower()
            if len(normalized) < 4:
                continue
            neighborhood_counts[normalized] = neighborhood_counts.get(normalized, 0) + 1

    top_neighborhood_tokens = [
        token for token, _ in sorted(neighborhood_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    ]

    preferred_duration = int(sum(durations) / len(durations)) if durations else None

    return {
        "top_neighborhood_tokens": top_neighborhood_tokens,
        "preferred_duration_minutes": preferred_duration,
    }
