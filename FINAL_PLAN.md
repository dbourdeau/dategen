# Date Planning Agent - Final Plan

## Executive Summary
Build a web app that generates personalized date ideas using LLM + web search + preference learning. 
- **Stack**: FastAPI (backend) + React/TypeScript (frontend) + PostgreSQL + Redis
- **Timeline**: 5 weeks MVP
- **Deployment**: Railway (auto-deploy from GitHub)
- **Inspired by**: PELAGOR architecture patterns (parallel search, LLM synthesis, preference learning)

---

## 1. What We're Building

A web application that:
1. **Stores preferences** — Budget, location, her interests, activity types, availability, seasonal preferences
2. **Generates date ideas** — Web search (restaurants, events, activities) + LLM synthesis → 3–5 personalized ideas
3. **Learns from reviews** — After each date, rate it (1–5) + feedback → system weights future suggestions
4. **Improves over time** — Algorithm gets better as it learns what she actually enjoys

---

## 2. Architecture Overview

```
FRONTEND (React/TypeScript/Vite)
    ├─ Preference Form
    ├─ Idea Display (cards with details)
    ├─ Review Submission (rating + feedback)
    └─ Analytics Dashboard

         ↓ HTTP ↑

BACKEND (FastAPI/Python)
    ├─ Auth & User Management (JWT)
    ├─ Preference Service (CRUD)
    ├─ Idea Generation Pipeline
    │   ├─ Web Search (SerpAPI - 3 parallel queries)
    │   ├─ LLM Synthesis (OpenRouter → GPT-4o)
    │   └─ Cache layer (Redis)
    ├─ Review & Learning Service
    └─ Analytics Service

         ↓ SQL ↑ (PostgreSQL)
         ↓ Cache (Redis)

DATABASE
    ├─ users
    ├─ user_preferences
    ├─ date_ideas
    └─ date_reviews
```

---

## 3. Data Model (PostgreSQL)

### Users
```sql
id (UUID) | email | password_hash | created_at
```

### User Preferences
```sql
id | user_id | budget_min | budget_max | city | state | zip | radius_miles
activity_types (JSONB) | her_interests (JSONB) | dietary_restrictions (JSONB)
available_duration_min | available_duration_max | seasonal_outdoor_preferred
weather_tolerance | notes | created_at | updated_at
```

### Date Ideas
```sql
id | user_id | title | description | estimated_cost | duration_minutes
location | activity_types (JSONB) | difficulty | season | maps_link
search_results (JSONB) | reasoning | confidence | created_at
```

### Date Reviews
```sql
id | date_idea_id | user_id | rating (1-5) | did_you_go (boolean)
went_well (text) | could_improve (text) | would_recommend
new_insights | tags_learned (JSONB) | created_at
```

---

## 4. Tech Stack (Final Choice)

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI (Python) | Async, JSON validation (Pydantic), easy LLM integration |
| **Frontend** | React + TypeScript + Vite | Type-safe, fast builds, PELAGOR pattern |
| **Primary DB** | PostgreSQL | ACID compliance, structured data, JSON support |
| **Cache** | Redis | Fast search result caching, avoid redundant API calls |
| **LLM** | OpenRouter (GPT-4o) | Cost control, single API for multiple models |
| **Web Search** | SerpAPI | High-quality structured results, reliable |
| **Deployment** | Railway | Simple, auto-deploys from GitHub, proven (PELAGOR) |
| **Auth** | JWT | Stateless, simple, scalable |

### API Keys Needed
- `OPENROUTER_API_KEY` — LLM access (OpenAI GPT-4o)
- `SERP_API_KEY` — Web search
- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` — Redis connection

---

## 5. MVP Scope (Weeks 1–5)

### Week 1: Backend Scaffolding
- [ ] FastAPI app skeleton
- [ ] PostgreSQL schema setup
- [ ] User registration + JWT login
- [ ] `.env.template` + secrets management

**Deliverable**: Users can sign up/login

### Week 2: Preferences Storage
- [ ] Preference model + CRUD endpoints
- [ ] React form for preference input (budget, location, interests, etc.)
- [ ] Save/update preferences in DB

**Deliverable**: Users can save preferences

### Week 3: Idea Generation Engine
- [ ] Integrate SerpAPI (parallel searches for restaurants, events, activities)
- [ ] Integrate OpenRouter (LLM synthesis prompt)
- [ ] Pipeline: search → LLM → save to DB
- [ ] Endpoint: `POST /api/ideas/generate`
- [ ] Frontend: Display 3–5 generated ideas

**Deliverable**: Users can generate date ideas

### Week 4: Review & Learning Loop
- [ ] Endpoints for submitting reviews (rating + feedback)
- [ ] Store reviews in DB
- [ ] Simple weight updates (track which activity types got high ratings)
- [ ] Modify idea generation prompt to use weighted preferences

**Deliverable**: System learns from reviews, improves suggestions

### Week 5: Testing & Deployment
- [ ] Local testing (docker-compose with Postgres + Redis)
- [ ] QA, bug fixes
- [ ] Deploy to Railway
- [ ] Documentation (README.md, setup instructions)

**Deliverable**: Live app at `dateideas.app`

---

## 6. API Endpoints

### Auth
```
POST   /auth/register              {email, password} → JWT token
POST   /auth/login                 {email, password} → JWT token
```

### Preferences
```
GET    /api/preferences            → {budget, location, interests, ...}
POST   /api/preferences            {budget, location, ...} → saved pref
PATCH  /api/preferences            {activity_types, notes} → updated pref
```

### Ideas
```
POST   /api/ideas/generate         {} → [{title, description, cost, ...}, ...]
GET    /api/ideas                  → list all generated ideas
GET    /api/ideas/{id}             → single idea details
DELETE /api/ideas/{id}             (soft delete preferred for history)
```

### Reviews
```
POST   /api/reviews                {idea_id, rating, feedback, ...} → saved review
GET    /api/reviews                → list all user reviews
PATCH  /api/reviews/{id}           {rating, feedback} → updated review
```

### Analytics (Phase 2+)
```
GET    /api/analytics/top-activities    → [{activity: "hiking", avg_rating: 4.8}, ...]
GET    /api/analytics/trends            → preference evolution over time
```

---

## 7. Idea Generation Workflow

```
1. User clicks "Get Ideas"
   ↓
2. Fetch user preferences from DB
   ↓
3. Search in parallel (via SerpAPI):
   - "best restaurants in [city] under $[budget]"
   - "outdoor activities for couples in [city]"
   - "events happening this weekend in [city]"
   ↓
4. Cache results in Redis (30 min TTL)
   ↓
5. Call LLM (OpenRouter → GPT-4o) with:
   - Search results
   - User preferences
   - Past highly-rated ideas (top 3)
   - Activity type weights (from learned preferences)
   ↓
6. Prompt response: "Generate 3-5 date ideas for this couple..."
   ↓
7. LLM returns JSON:
   [{
     "title": "Brewery tour + food truck",
     "description": "...",
     "estimated_cost": 60,
     "duration_minutes": 180,
     "reasoning": "Matches hiking/outdoor interests",
     "confidence": 0.87
   }, ...]
   ↓
8. Save to date_ideas table
   ↓
9. Return to frontend
```

---

## 8. Learning Algorithm

After each date review, update preference weights:

```python
# Pseudocode
def update_weights(review_rating, date_idea):
    if review_rating >= 4:
        for activity in date_idea.activity_types:
            activity_weight[activity] += 0.05
        location_score[date_idea.location] += 0.1
    elif review_rating <= 2:
        for activity in date_idea.activity_types:
            activity_weight[activity] -= 0.05
```

**Cold Start Problem**: First 2–3 ideas won't be personalized (no rating history). After 3–5 reviewed dates, algorithm learns her preferences.

**Next generation uses updated weights**:
```python
def generate_ideas_prompt(preferences):
    weighted_interests = sort_by_weight(preferences.her_interests)
    return f"""
    Generate 3 date ideas for a couple in {city}.
    
    Her top interests (by what she rated highly):
    1. {weighted_interests[0]}
    2. {weighted_interests[1]}
    3. {weighted_interests[2]}
    
    Budget: ${budget_min}–${budget_max}
    Duration: {duration_min}–{duration_max} hours
    
    Past highly-rated dates:
    {top_3_reviews}
    
    Generate ideas she hasn't tried before.
    """
```

---

## 9. File Structure (Git)

```
dategen/
├── backend/
│   ├── main.py                      # FastAPI entry point
│   ├── models.py                    # SQLAlchemy models
│   ├── schemas.py                   # Pydantic request/response
│   ├── database.py                  # DB connection + session
│   ├── routes/
│   │   ├── auth.py                  # /auth/*
│   │   ├── preferences.py           # /api/preferences/*
│   │   ├── ideas.py                 # /api/ideas/*
│   │   └── reviews.py               # /api/reviews/*
│   ├── services/
│   │   ├── serp_search.py           # SerpAPI wrapper
│   │   ├── llm_synthesis.py         # OpenRouter + LLM
│   │   └── preference_learn.py      # Weight updates
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Preferences.tsx      # Settings page
│   │   │   ├── GenerateIdeas.tsx    # Main idea gen UI
│   │   │   └── ReviewDate.tsx       # Rate past date
│   │   ├── components/
│   │   │   ├── IdeaCard.tsx
│   │   │   ├── PreferenceForm.tsx
│   │   │   └── ReviewForm.tsx
│   │   ├── api.ts                   # Axios client
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml               # Postgres + Redis local
├── railway.toml                     # Railway deployment config
├── .env.template
├── .gitignore
├── README.md
├── CLAUDE.md                        # Developer guidelines
└── FINAL_PLAN.md                    # This file
```

---

## 10. Getting Started (Setup Commands)

### 1. Create GitHub repo
```bash
cd ~/dategen
git init
git remote add origin https://github.com/YOUR_USERNAME/dategen.git
```

### 2. Copy `.env.template` → `.env` and fill in API keys
```bash
cp .env.template .env
# Edit .env with your API keys:
# - OPENROUTER_API_KEY
# - SERP_API_KEY
# - DATABASE_URL (local Postgres)
# - REDIS_URL (local Redis)
```

### 3. Start local environment (Docker)
```bash
docker-compose up -d
```

### 4. Install backend dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 5. Set up database
```bash
cd backend
python -c "from main import app; from database import engine; Base.metadata.create_all(engine)"
```

### 6. Start backend (http://localhost:8000)
```bash
cd backend
uvicorn main:app --reload
```

### 7. Start frontend (in another terminal)
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

---

## 11. Deployment to Railway

1. **Push to GitHub** (on `main` branch)
2. **Connect Railway** to GitHub repo (auto-deploy enabled)
3. **Set environment variables** in Railway dashboard:
   - `OPENROUTER_API_KEY`
   - `SERP_API_KEY`
   - `DATABASE_URL` (Railway PostgreSQL)
   - `REDIS_URL` (Railway Redis)
4. **Deploy** — Railway auto-builds and deploys on every push to `main`
5. **App URL** — Railway assigns a public URL (e.g., `dateideas.up.railway.app`)

---

## 12. Success Metrics

- [ ] MVP launches in 5 weeks
- [ ] Users can set preferences
- [ ] Idea generation works (<5 sec response time)
- [ ] System learns: ratings ≥4 improve suggestions, ratings ≤2 reduce them
- [ ] Average suggestion rating: 4.0+ after 5 reviews
- [ ] 80%+ of suggestions tried

---

## 13. Future Phases (Post-MVP)

### Phase 2: Analytics & Sharing
- Job-based persistence (shareable URLs for ideas)
- CSV export of past dates
- Analytics dashboard ("Your top activity types")
- Bulk CSV upload for preference seeding

### Phase 3: Advanced Features
- Real-time SSE streaming during idea generation
- Calendar integration (detect anniversaries)
- Photo gallery from past dates
- Surprise mode ("plan something I've never tried")
- Smart model routing (ensemble for conflict resolution)

### Phase 4: Scale
- Image storage (S3 or Cloudinary)
- Email notifications
- Mobile app
- Friend collaboration (plan dates together)

---

## 14. Next Action

**Ready to code?** I can scaffold the backend now:
- [ ] FastAPI boilerplate
- [ ] SQLAlchemy models + migrations
- [ ] Auth routes (register/login)
- [ ] Pydantic schema
- [ ] `.env.template`
- [ ] Docker setup

Just say the word and I'll generate the starter files!
