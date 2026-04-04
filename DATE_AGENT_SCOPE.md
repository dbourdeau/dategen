# Date Planning Agent - Final Plan

## Executive Summary
Build a web app that generates personalized date ideas using LLM + web search + preference learning. Stack: **FastAPI + React + PostgreSQL + OpenAI/Claude**. MVP in 5 weeks. Deploy on Railway.

---

## 1. Project Overview
A web application that intelligently generates date ideas by combining:
- Your preferences and constraints (budget, location, activity types, etc.)
- Your girlfriend's interests and preferences  
- Real-time web search for current venues, restaurants, and events
- Learning from past date reviews to improve future suggestions

---

## 2. Core Architecture

### 2.1 High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Web UI)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Preferences  │  │ Idea Gen     │  │ Date         │   │
│  │ Management   │  │ Interface    │  │ History/     │   │
│  │              │  │              │  │ Reviews      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↑ ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│              Backend API (Node.js/Python)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Preference   │  │ Idea         │  │ Review/      │   │
│  │ Service      │  │ Generation   │  │ Training     │   │
│  │              │  │ Engine       │  │ Service      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ External Integrations                            │   │
│  │ - Web Search (Google Search API / Serp)          │   │
│  │ - Google Maps / Geolocation API                  │   │
│  │ - LLM (OpenAI GPT / Anthropic Claude)            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↑ ↓ SQL/NoSQL
┌─────────────────────────────────────────────────────────┐
│                    Database                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ User Profile │  │ Past Dates   │  │ Feedback     │   │
│  │ & Prefs      │  │ History      │  │ Ratings      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 9. API Endpoints (FastAPI)

```
Authentication
  POST   /auth/register              Register new user
  POST   /auth/login                 Login (returns JWT token)

Preferences
  GET    /api/preferences            Get current preferences
  POST   /api/preferences            Create/update preferences
  PATCH  /api/preferences            Update subset of preferences

Ideas
  POST   /api/ideas/generate         Generate new ideas (takes current prefs)
                                     → returns [DateIdea, ...]
  GET    /api/ideas                  List all generated ideas (paginated)
  GET    /api/ideas/{id}             Get single idea details
  DELETE /api/ideas/{id}             Remove idea

Reviews
  POST   /api/reviews                Submit review for a date idea
                                     {idea_id, rating, feedback, ...}
  GET    /api/reviews                List all reviews for this user
  PATCH  /api/reviews/{id}           Update review

Analytics (Phase 2+)
  GET    /api/analytics/top-activities      Top rated activity types
  GET    /api/analytics/trends              Preference trends over time
  GET    /api/jobs/{job_id}                 Retrieve old generation (shareable URL)
```

---

## 10. Learning Algorithm



---

## 5. Interaction Flows

### 5.1 Flow 1: New User Setup
```
User → Sign Up → Enter Preferences → System Stores → Ready to Generate
                  (Budget, location, 
                   interests, etc.)
```

### 5.2 Flow 2: Generate Date Idea
```
User → Click "Get Ideas"
       ↓
System checks current preferences
       ↓
Web search:
  - Restaurants in [city] [budget]
  - Events happening [date]
  - Activities [interests] [location]
       ↓
LLM synthesizes 3-5 ideas with:
  - Title + description
  - Cost estimate
  - Duration
  - Why it matches preferences
       ↓
Display ideas with save/bookmark options
```

### 5.3 Flow 3: Review After Date
```
User → Log past date → Rate (1-5) → Write feedback
                         ↓
System extracts:
  - Which activities rated well
  - Budget bands that worked
  - Location preferences
       ↓
Algorithm learns preferences
```

### 5.4 Flow 4: Continuous Learning
```
Past reviews → Weight adjustments
              (if she loved hiking, suggest more outdoor activities)
                    ↓
Next idea generation uses updated weights
```

---

## 6. Tech Stack (Final Choice)

### Backend
- **Framework**: Python FastAPI (same as PELAGOR, proven at scale)
- **Database**: PostgreSQL + Redis
  - PostgreSQL: user data, dates, reviews, preferences
  - Redis: cache web search results (avoid redundant calls)
- **LLM**: OpenAI GPT-4o via OpenRouter (cost control + flexibility)
- **Web Search**: SerpAPI (structured results, high quality)
- **Deployment**: Railway (auto-deploy from GitHub, same as PELAGOR)

### Frontend
- **Framework**: React + TypeScript + Vite (PELAGOR pattern)
- **UI Library**: option TailwindCSS or shadcn/ui
- **Deployment**: Railway (same backend/frontend deployment)

### DevOps
- **Version Control**: GitHub
- **CI/CD**: GitHub Actions
- **Local testing**: Docker + docker-compose
- **Environment**: .env.template pattern (PELAGOR style)

### APIs & Services
- **OpenRouter** — LLM access (OpenAI, Anthropic, Google behind single API)
- **SerpAPI** — web search (restaurants, events, activities)
- **Google Maps API** — location/distance calculations (optional, MVP can skip)

---

## 7. Implementation Plan (Phased)

### 7.1 Phase 1: MVP (Weeks 1–5)

**Goal**: Generate and review date ideas based on preferences.

| Week | Component | Tasks |
|------|-----------|-------|
| **1** | Backend Setup | FastAPI boilerplate, PostgreSQL schema (users, preferences, ideas, reviews), user auth (JWT) |
| **1** | Database | Create schema for UserProfile, DateIdea, DateReview tables |
| **2** | Web Search Integration | Integrate SerpAPI for restaurants/events/activities; cache results in Redis |
| **2** | LLM Integration | OpenRouter setup; prompt engineering for idea synthesis |
| **2** | Preference Intake | REST endpoint to save/update user preferences; validation |
| **3** | Core Engine | Build idea generation pipeline: fetch searches → call LLM → return 3–5 ideas with reasoning |
| **3** | Frontend Setup | React + TypeScript boilerplate; preference form UI |
| **3** | Idea Display | UI to show generated ideas (title, description, cost, duration, reasoning) |
| **4** | Review Submission | Endpoint + UI to log past dates; 1–5 star rating + written feedback |
| **4** | Preference Learning | Simple algorithm: track which activity types got 5-star ratings; weight them higher |
| **5** | Testing & Deploy | QA, bug fixes, deploy to Railway staging/production, docs |

**MVP Deliverable**: Users can set preferences, generate 3–5 date ideas, review past dates, and see improved suggestions over time.

---

### 7.2 Phase 2: Real-time Feedback (Week 6–7, post-MVP)

- Real-time SSE streaming during idea generation (show search progress)
- Better error handling & retry logic
- Refinement based on usage patterns

---

### 7.3 Phase 3: Analytics & Sharing (Week 8–9, post-MVP)

- Job-based persistence (every idea generation gets a shareable URL)
- CSV export of past dates + reviews
- Simple analytics dashboard ("Your top activity types")
- Bulk CSV upload for preference seeding

---

### 7.4 Future Phases (Optional)

- Photo gallery from past dates
- Calendar integration (detect anniversaries, special dates)
- Surprise mode ("plan something I've never tried")
- Smart routing (use faster models for easy decisions, ensemble for conflicts)

---

## 8. Database Schema (PostgreSQL)

## 8. Database Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- User Preferences
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  budget_min INTEGER,
  budget_max INTEGER,
  currency VARCHAR(10) DEFAULT 'USD',
  city VARCHAR(255),
  state VARCHAR(255),
  zip_code VARCHAR(10),
  radius_miles INTEGER,
  activity_types JSONB, -- ["outdoor", "dining", "cultural", ...]
  her_interests JSONB,  -- ["hiking", "museums", ...]
  dietary_restrictions JSONB,
  available_duration_min INTEGER, -- hours
  available_duration_max INTEGER,
  seasonal_outdoor_preferred BOOLEAN,
  seasonal_indoor_preferred BOOLEAN,
  weather_tolerance VARCHAR(50), -- "low", "medium", "high"
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT unique_user_prefs UNIQUE(user_id)
);

-- Date Ideas (generated)
CREATE TABLE date_ideas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  estimated_cost DECIMAL(10,2),
  duration_minutes INTEGER,
  location VARCHAR(255),
  activity_types JSONB,
  difficulty VARCHAR(50),
  season VARCHAR(100),
  maps_link VARCHAR(1000),
  search_results JSONB, -- citations from web search
  reasoning TEXT,
  confidence DECIMAL(3,2),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Date Reviews (after the date)
CREATE TABLE date_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date_idea_id UUID NOT NULL REFERENCES date_ideas(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  did_you_go BOOLEAN,
  went_well TEXT,
  could_improve TEXT,
  would_recommend BOOLEAN,
  new_insights TEXT,
  tags_learned JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_date_ideas_user_id ON date_ideas(user_id);
CREATE INDEX idx_date_ideas_created_at ON date_ideas(created_at DESC);
CREATE INDEX idx_date_reviews_user_id ON date_reviews(user_id);
CREATE INDEX idx_date_reviews_date_idea_id ON date_reviews(date_idea_id);
```

---

## 9. API Endpoints (FastAPI)
After each date review, update preference weights:

```python
def update_preference_weights(review_rating, idea):
    """Boost weights for activity types that got high ratings"""
    if review_rating >= 4:
        for activity in idea.activity_types:
            activity_weight[activity] += 0.05  # small boost
        location_score[idea.location] += 0.1
    elif review_rating <= 2:
        # Reduce weight for low ratings
        for activity in idea.activity_types:
            activity_weight[activity] -= 0.05

def generate_ideas_prompt(preferences, past_reviews):
    """Build LLM prompt with weighted preferences"""
    weighted_interests = sorted_by_weight(preferences.her_interests, activity_weight)
    return f"""
    Generate 3 date ideas for a couple in {preferences.city}.
    Budget: ${preferences.budget_min}–${preferences.budget_max}
    Duration: {preferences.available_duration_min}–{preferences.available_duration_max} hours
    
    Her top interests (by what she rated highly):
    {weighted_interests}
    
    Activity types to prioritize:
    {sorted_by_weight(preferences.activity_types, activity_weight)}
    
    Previous highly-rated dates to learn from:
    {past_reviews.filter(rating >= 4).top(3)}
    
    Generate creative, specific ideas. Avoid repeating recent suggestions.
    """
```

**Cold Start**: First few ideas won't be personalized. After 3–5 reviewed dates, algorithm becomes accurate.

---

## 11. Success Metrics

- [ ] MVP launches in 5 weeks
- [ ] Average rating of suggested dates: 4+ stars
- [ ] Idea generation time: <5 seconds (with web search)
- [ ] User reviews 80%+ of ideas they try
- [ ] Week-over-week improvement in rating as model learns

---

## 12. Deployment Checklist

- [ ] GitHub repo initialized
- [ ] `.env.template` created (API keys masked)
- [ ] `requirements.txt` and `package.json` in place
- [ ] `Dockerfile` + `docker-compose.yml` for local dev
- [ ] Railway `railway.toml` configured
- [ ] GitHub Actions workflow for auto-deploy on push to `main`
- [ ] `README.md` with setup + deployment instructions
- [ ] Basic logging (structured logs to stdout for Railway)

---

## 13. File Structure (Git Repo)

```
dategen/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── routes/
│   │   ├── auth.py
│   │   ├── preferences.py
│   │   ├── ideas.py
│   │   └── reviews.py
│   ├── services/
│   │   ├── serp_search.py      # SerpAPI wrapper
│   │   ├── llm_synthesis.py    # OpenRouter + LLM prompts
│   │   └── preference_learn.py # Weight updates
│   ├── database.py             # SQLAlchemy setup
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Preferences.tsx
│   │   │   ├── GenerateIdeas.tsx
│   │   │   └── ReviewDate.tsx
│   │   ├── components/
│   │   │   ├── IdeaCard.tsx
│   │   │   ├── PreferenceForm.tsx
│   │   │   └── ReviewForm.tsx
│   │   ├── api.ts              # API client
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml          # local postgres + redis
├── railway.toml
├── .env.template
├── .gitignore
├── README.md
├── CLAUDE.md                   # Developer guidelines (like PELAGOR)
└── DATE_AGENT_SCOPE.md         # This file
```

---

## 14. Getting Started (Next Steps)

1. **Initialize repo**: `git init`, create GitHub repo
2. **Set up local env**: Docker Compose (PostgreSQL + Redis)
3. **Backend Week 1**: FastAPI boilerplate + auth + DB setup
4. **Frontend Week 1–2**: React setup + preference form
5. **Integration Week 2–3**: Wire up web search + LLM
6. **Testing & Deploy Week 5**: QA + Railway deployment

**Ready to code?** Let me know and I'll scaffold the backend boilerplate to get you started!
