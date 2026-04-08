"""Admin-managed curated venue catalog routes."""

import os
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import CuratedVenue, User
from routes.auth import get_current_user
from schemas import CuratedVenueCreate, CuratedVenueResponse, CuratedVenueUpdate
from services.curated_catalog import get_chicago_seed_rows

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def _domain(url: str) -> str:
    netloc = (urlparse(url).netloc or "").lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _require_admin_token(x_admin_token: str = Header(default="")) -> None:
    configured = (os.getenv("CATALOG_ADMIN_TOKEN") or "").strip()
    if not configured:
        raise HTTPException(status_code=503, detail="CATALOG_ADMIN_TOKEN is not configured")
    if not x_admin_token or x_admin_token != configured:
        raise HTTPException(status_code=403, detail="Admin token required")


@router.get("", response_model=List[CuratedVenueResponse])
def list_catalog(
    city: str = Query(default="Chicago"),
    category: Optional[str] = Query(default=None),
    active_only: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List curated venues by city/category."""
    _ = current_user

    query = db.query(CuratedVenue).filter(CuratedVenue.city.ilike(city))
    if category:
        query = query.filter(CuratedVenue.category == category)
    if active_only:
        query = query.filter(CuratedVenue.is_active.is_(True), CuratedVenue.deleted_at.is_(None))

    return query.order_by(CuratedVenue.category.asc(), CuratedVenue.curated_rank.asc(), CuratedVenue.created_at.desc()).all()


@router.post("", response_model=CuratedVenueResponse)
def upsert_catalog_venue(
    payload: CuratedVenueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin_token),
):
    """Create or update a curated venue by city/category/name."""
    _ = current_user

    existing = (
        db.query(CuratedVenue)
        .filter(
            CuratedVenue.city.ilike(payload.city),
            CuratedVenue.category == payload.category,
            CuratedVenue.name.ilike(payload.name),
            CuratedVenue.deleted_at.is_(None),
        )
        .first()
    )

    if existing:
        existing.url = payload.url
        existing.snippet = payload.snippet or ""
        existing.curated_rank = payload.curated_rank or 50
        existing.estimated_cost = payload.estimated_cost
        existing.tags = payload.tags or []
        existing.opening_date = payload.opening_date
        existing.event_date = payload.event_date
        existing.is_active = payload.is_active if payload.is_active is not None else True
        existing.source_domain = _domain(payload.url)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    venue = CuratedVenue(
        city=payload.city,
        category=payload.category,
        name=payload.name,
        url=payload.url,
        snippet=payload.snippet or "",
        source_domain=_domain(payload.url),
        curated_rank=payload.curated_rank or 50,
        estimated_cost=payload.estimated_cost,
        tags=payload.tags or [],
        opening_date=payload.opening_date,
        event_date=payload.event_date,
        is_active=payload.is_active if payload.is_active is not None else True,
    )
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


@router.patch("/{venue_id}", response_model=CuratedVenueResponse)
def update_catalog_venue(
    venue_id: str,
    payload: CuratedVenueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin_token),
):
    """Update curated venue fields."""
    _ = current_user

    venue = db.query(CuratedVenue).filter(CuratedVenue.id == venue_id, CuratedVenue.deleted_at.is_(None)).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Catalog venue not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "url" and value:
            venue.url = value
            venue.source_domain = _domain(value)
        else:
            setattr(venue, key, value)

    venue.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(venue)
    return venue


@router.delete("/{venue_id}")
def soft_delete_catalog_venue(
    venue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin_token),
):
    """Soft-delete a curated venue for audit trail."""
    _ = current_user

    venue = db.query(CuratedVenue).filter(CuratedVenue.id == venue_id, CuratedVenue.deleted_at.is_(None)).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Catalog venue not found")

    venue.deleted_at = datetime.utcnow()
    venue.is_active = False
    venue.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Catalog venue deleted"}


@router.post("/seed/chicago")
def seed_chicago_catalog(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin_token),
):
    """Seed curated Chicago baseline data (idempotent by city/category/name)."""
    _ = current_user

    seed_rows = get_chicago_seed_rows()
    created = 0
    updated = 0

    for row in seed_rows:
        existing = (
            db.query(CuratedVenue)
            .filter(
                CuratedVenue.city.ilike(row["city"]),
                CuratedVenue.category == row["category"],
                CuratedVenue.name.ilike(row["name"]),
                CuratedVenue.deleted_at.is_(None),
            )
            .first()
        )

        if existing:
            existing.url = row["url"]
            existing.snippet = row.get("snippet", "")
            existing.source_domain = _domain(row["url"])
            existing.curated_rank = row.get("curated_rank", 50)
            existing.estimated_cost = row.get("estimated_cost")
            existing.tags = row.get("tags", [])
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            updated += 1
        else:
            venue = CuratedVenue(
                city=row["city"],
                category=row["category"],
                name=row["name"],
                url=row["url"],
                snippet=row.get("snippet", ""),
                source_domain=_domain(row["url"]),
                curated_rank=row.get("curated_rank", 50),
                estimated_cost=row.get("estimated_cost"),
                tags=row.get("tags", []),
                is_active=True,
            )
            db.add(venue)
            created += 1

    db.commit()
    return {
        "message": "Chicago catalog seed complete",
        "created": created,
        "updated": updated,
        "total_seed_rows": len(seed_rows),
    }
