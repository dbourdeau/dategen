"""Curated catalog storage helpers and seed data."""

from typing import Dict, List
from sqlalchemy.orm import Session
from models import CuratedVenue


def _normalize_city(city: str) -> str:
    return " ".join((city or "").strip().lower().split())


def _rows_to_grouped(items: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = {
        "restaurants": [],
        "activities": [],
        "events": [],
        "date_ideas": [],
        "reddit": [],
        "low_cost": [],
        "new_openings": [],
    }
    for item in items:
        bucket = item.get("category") or "activities"
        if bucket not in grouped:
            bucket = "activities"
        grouped[bucket].append(
            {
                "title": item.get("name", ""),
                "link": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            }
        )
    return grouped


def get_chicago_seed_rows() -> List[Dict[str, object]]:
    """Seed rows for Chicago baseline catalog."""
    return [
        {
            "city": "Chicago",
            "category": "restaurants",
            "name": "Bavette's Bar & Boeuf",
            "url": "https://www.bavettessteakhouse.com/chicago/",
            "snippet": "Classic downtown date-night steakhouse with a strong cocktail program.",
            "curated_rank": 10,
            "estimated_cost": 90,
            "tags": ["steakhouse", "romantic", "west-loop-adjacent"],
        },
        {
            "city": "Chicago",
            "category": "restaurants",
            "name": "Monteverde Restaurant & Pastificio",
            "url": "https://www.monteverdechicago.com/",
            "snippet": "Highly rated West Loop Italian restaurant ideal for shared plates.",
            "curated_rank": 12,
            "estimated_cost": 85,
            "tags": ["italian", "west-loop", "dinner"],
        },
        {
            "city": "Chicago",
            "category": "restaurants",
            "name": "Daisies Chicago",
            "url": "https://www.daisieschicago.com/",
            "snippet": "Seasonal Logan Square favorite with handmade pasta and warm ambiance.",
            "curated_rank": 15,
            "estimated_cost": 70,
            "tags": ["logan-square", "seasonal", "cozy"],
        },
        {
            "city": "Chicago",
            "category": "activities",
            "name": "Chicago Riverwalk",
            "url": "https://www.chicagoriverwalk.us/",
            "snippet": "Scenic waterfront walk with flexible stops and skyline views.",
            "curated_rank": 8,
            "estimated_cost": 0,
            "tags": ["walk", "scenic", "downtown"],
        },
        {
            "city": "Chicago",
            "category": "activities",
            "name": "Navy Pier Centennial Wheel",
            "url": "https://navypier.org/attractions/centennial-wheel/",
            "snippet": "Lakefront views and evening lights for a classic Chicago date.",
            "curated_rank": 16,
            "estimated_cost": 20,
            "tags": ["lakefront", "attraction", "views"],
        },
        {
            "city": "Chicago",
            "category": "low_cost",
            "name": "Lincoln Park Zoo",
            "url": "https://www.lpzoo.org/",
            "snippet": "Free-entry zoo and nearby park paths for a low-cost date.",
            "curated_rank": 7,
            "estimated_cost": 0,
            "tags": ["free", "outdoor", "animals"],
        },
        {
            "city": "Chicago",
            "category": "low_cost",
            "name": "Chicago Cultural Center",
            "url": "https://www.chicago.gov/city/en/depts/dca/supp_info/chicago_culturalcenter.html",
            "snippet": "Free exhibits and architecture in the Loop with easy transit access.",
            "curated_rank": 9,
            "estimated_cost": 0,
            "tags": ["free", "architecture", "exhibits"],
        },
        {
            "city": "Chicago",
            "category": "low_cost",
            "name": "The 606 Trail",
            "url": "https://www.the606.org/",
            "snippet": "Bike or walk together on an elevated trail through Chicago neighborhoods.",
            "curated_rank": 11,
            "estimated_cost": 0,
            "tags": ["bike", "walk", "outdoor"],
        },
    ]


def get_curated_city_results(db: Session, city: str) -> Dict[str, List[Dict[str, str]]]:
    """Load active curated venues from Postgres for a city."""
    normalized_city = _normalize_city(city)
    like_value = f"%{city.strip()}%" if city and city.strip() else "%"

    rows = (
        db.query(CuratedVenue)
        .filter(
            CuratedVenue.city.ilike(like_value),
            CuratedVenue.is_active.is_(True),
            CuratedVenue.deleted_at.is_(None),
        )
        .order_by(CuratedVenue.category.asc(), CuratedVenue.curated_rank.asc(), CuratedVenue.created_at.desc())
        .all()
    )
    if rows:
        return _rows_to_grouped(
            [
                {
                    "category": row.category,
                    "name": row.name,
                    "url": row.url,
                    "snippet": row.snippet or "",
                }
                for row in rows
            ]
        )

    if normalized_city in {"chicago", "chicago, il", "chicago il"}:
        return _rows_to_grouped(get_chicago_seed_rows())

    return _rows_to_grouped([])
