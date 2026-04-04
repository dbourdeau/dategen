"""Create initial database and seed with default data."""

from database import engine, Base
from models import User, UserPreferences, DateIdea, DateReview

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Database initialized successfully!")
print("📊 Tables created:")
print("   - users")
print("   - user_preferences")
print("   - date_ideas")
print("   - date_reviews")
