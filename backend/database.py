"""Database configuration and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Get database URL from environment.
# Railway can provide an empty string when the app service variable is not wired.
raw_database_url = (os.getenv("DATABASE_URL") or "").strip()
if not raw_database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. Set DATABASE_URL in your app service, "
        "for example: ${{Postgres.DATABASE_URL}}"
    )

# Some providers expose postgres://; SQLAlchemy expects postgresql://
DATABASE_URL = raw_database_url.replace("postgres://", "postgresql://", 1)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,  # Test connections before using
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """Dependency for FastAPI routes to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
