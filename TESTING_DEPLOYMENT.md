# DateGen - Testing & Deployment Guide

## Part 1: Local Testing (Docker)

### Prerequisites
- Docker & Docker Compose installed
- API keys: OpenRouter, SerpAPI
- Code in `/dategen` folder

### Step 1: Set Up Environment

```bash
cd c:\Users\Daniel.Bourdeau\dategen

# Copy template
copy .env.template .env

# Edit .env with your API keys
# Open .env in editor and fill in:
# - OPENROUTER_API_KEY=sk-or-...
# - SERP_API_KEY=...
# - SECRET_KEY=your-secret-key
```

### Step 2: Start Services (One Command)

**Windows:**
```bash
setup.bat
```

**Mac/Linux:**
```bash
bash setup.sh
```

Or manually:
```bash
docker-compose up -d
```

### Step 3: Verify Services Are Running

```bash
# Check all containers
docker-compose ps

# Should show:
# NAME          STATUS
# postgres      Up (healthy)
# redis         Up (healthy)
# backend       Up
# frontend      Up
```

### Step 4: Test Backend Health

```bash
# Terminal window (PowerShell)
curl http://localhost:8000/health

# Should return:
# {"status":"ok"}
```

If it fails:
```bash
# Check logs
docker-compose logs backend

# Or just backend
docker-compose logs backend -f
```

---

## Part 2: Test the App (Local)

### Access Frontend
Open browser: **http://localhost:5173**

### Test 1: User Registration

1. Look for login/register button (if implemented)
2. Or directly test via API:

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Should return JWT token:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }

# Save token in variable
$token = "eyJ0eXAiOiJKV1QiLCJhbGc..."  # your token
```

### Test 2: Set Preferences

```bash
# Set preferences
curl -X POST http://localhost:8000/api/preferences \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "budget_min": 30,
    "budget_max": 100,
    "city": "Denver",
    "activity_types": ["outdoor", "dining"],
    "her_interests": ["hiking", "coffee", "live music"],
    "dietary_restrictions": [],
    "available_duration_min": 2,
    "available_duration_max": 4
  }'

# Should return:
# {
#   "id": "...",
#   "user_id": "...",
#   "budget_min": 30,
#   "budget_max": 100,
#   ...
# }
```

### Test 3: Generate Date Ideas

```bash
# Generate ideas
curl -X POST http://localhost:8000/api/ideas/generate \
  -H "Authorization: Bearer $token"

# Should return 3-5 ideas:
# [
#   {
#     "title": "Brewery tour + food truck",
#     "description": "...",
#     "estimated_cost": 75,
#     "duration_minutes": 180,
#     "location": "Denver",
#     "activity_types": ["outdoor", "dining"],
#     "reasoning": "Matches your interests...",
#     "confidence": 0.87
#   },
#   ...
# ]
```

**If it fails:**
- Check API keys in `.env`: `docker-compose exec backend cat /app/.env | grep -E "OPENROUTER|SERP"`
- Check backend logs: `docker-compose logs backend -f`
- Test LLM directly: See troubleshooting section

### Test 4: Submit a Review

```bash
# Get idea ID from previous step
$idea_id = "..."

# Submit review (rate the date)
curl -X POST http://localhost:8000/api/reviews \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "date_idea_id": "'$idea_id'",
    "rating": 5,
    "did_you_go": true,
    "went_well": "Great atmosphere and food!",
    "would_recommend": true,
    "tags_learned": ["outdoor", "hiking"]
  }'

# Should return review with timestamp
```

### Test 5: Verify Learning (Generate Again)

```bash
# Generate ideas again
curl -X POST http://localhost:8000/api/ideas/generate \
  -H "Authorization: Bearer $token"

# Should now prioritize "outdoor" and "hiking" 
# (though first time may not be noticeable)
```

### Test 6: Get Analytics

```bash
# Top activities by rating
curl http://localhost:8000/api/reviews/analytics/top-activities \
  -H "Authorization: Bearer $token"

# Should return activities ranked by avg rating
```

---

## Part 3: Frontend UI Testing

### Navigate to http://localhost:5173

#### Page 1: Ideas (Default)
- [ ] Button "✨ Get Date Ideas" appears
- [ ] Click it (may take 10-15 seconds for LLM)
- [ ] 3-5 ideas appear as cards
- [ ] Each card shows: title, description, cost, duration, activities

#### Page 2: Settings ⚙️
- [ ] Click "⚙️ Settings" tab
- [ ] Form loads with preference fields
- [ ] Edit budget, city, interests
- [ ] Click "Save Preferences"
- [ ] Message "Preferences saved" appears

#### Page 3: Reviews ⭐
- [ ] Click "⭐ Reviews" tab
- [ ] Shows past dates (currently placeholder)

---

## Part 4: Troubleshooting Local Setup

### Issue: Containers not starting

```bash
# Check if ports are in use
netstat -ano | findstr :5432
netstat -ano | findstr :6379
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Stop conflicting services and restart
docker-compose down
docker-compose up -d --rebuild
```

### Issue: Database connection error

```bash
# Check if PostgreSQL is healthy
docker-compose exec postgres pg_isready

# View postgres logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend python init_db.py
```

### Issue: OpenRouter API returns 401

```bash
# Verify key is set
docker-compose exec backend sh -c "echo \$OPENROUTER_API_KEY"

# Test API directly
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "test"}]}'
```

### Issue: SerpAPI returns error

```bash
# Test SerpAPI directly
curl "https://serpapi.com/search?q=restaurants in denver&api_key=YOUR_KEY"

# Check key format
docker-compose exec backend sh -c "echo \$SERP_API_KEY"
```

### Issue: Frontend can't connect to backend

```bash
# Check CORS in backend logs
docker-compose logs backend | grep -i cors

# Verify backend is running
curl http://localhost:8000/health

# Check frontend network request in browser console
# (Right-click → Inspect → Network tab)
```

---

## Part 5: Deploy to Production (Railway)

### Prerequisites
- GitHub repo created (https://github.com/dbourdeau/dategen)
- Code pushed to `main` branch
- Railway account (railway.app)
- API keys ready

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project"
4. Select "GitHub Repo"
5. Choose `dategen` repo
6. Click "Deploy"

### Step 2: Add Services

#### PostgreSQL Database
1. In Railway dashboard, click "Add Service"
2. Select "Database" → "PostgreSQL"
3. Railway automatically creates it and sets `DATABASE_URL`

#### Redis Cache
1. Click "Add Service"
2. Select "Database" → "Redis"
3. Railway automatically sets `REDIS_URL`

### Step 3: Configure Environment Variables

In Railway dashboard:
1. Go to your project
2. Click "Variables"
3. Add:

```
OPENROUTER_API_KEY=sk-or-... (your key)
SERP_API_KEY=...             (your key)
SECRET_KEY=generate-secure-key-here
CORS_ORIGINS=YOUR_RAILWAY_DOMAIN.railway.app
ENV=production
```

### Step 4: Deploy the App

1. Railway auto-detects your app
2. It reads `Dockerfile` from `backend/`
3. Deploys automatically on push to `main`

### Step 5: Verify Deployment

Railway gives you a public URL. Test it:

```bash
# Get the Railway URL (shown in dashboard)
$url = "https://your-app-name.railway.app"

# Test health
curl $url/health
# Should return: {"status":"ok"}

# Test API docs (interactive)
# Visit: https://your-app-name.railway.app/docs
```

### Step 6: Initialize Database (First Time Only)

```bash
# SSH into Railway container
railway shell

# Initialize DB
cd backend
python init_db.py

# Exit
exit
```

---

## Part 6: Full Integration Test (Production)

Once deployed, test end-to-end:

### Test 1: Register User
```bash
$url = "https://your-railway-app.railway.app"

curl -X POST $url/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "prod-test@example.com",
    "password": "testpass123"
  }'
```

### Test 2: Set Preferences
```bash
# Use token from registration above
$token = "..."

curl -X POST $url/api/preferences \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "budget_min": 25,
    "budget_max": 120,
    "city": "Denver",
    "activity_types": ["outdoor", "dining"],
    "her_interests": ["hiking", "restaurants"],
    "available_duration_min": 2,
    "available_duration_max": 5
  }'
```

### Test 3: Generate Ideas
```bash
curl -X POST $url/api/ideas/generate \
  -H "Authorization: Bearer $token"

# Monitor: open Railway logs
# railway logs -f --service backend
```

### Test 4: Submit Review
```bash
curl -X POST $url/api/reviews \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "date_idea_id": "...",
    "rating": 5,
    "went_well": "Amazing hike!"
  }'
```

---

## Part 7: Monitoring (Production)

### View Logs
```bash
railway logs -f

# Just backend
railway logs -f --service backend

# Just database
railway logs -f --service postgres
```

### Monitor Performance
In Railway dashboard:
- CPU/Memory usage
- Response times
- Error rates

### Check API Health
```bash
# Regular health check
curl https://your-app.railway.app/health

# Full diagnostic
curl https://your-app.railway.app/docs
```

---

## Summary: Quick Command Checklist

### Local Testing
```bash
# 1. Set up
copy .env.template .env
# Edit .env with API keys

# 2. Start
docker-compose up -d

# 3. Test backend
curl http://localhost:8000/health

# 4. Test in browser
# Open http://localhost:5173

# 5. Stop
docker-compose down
```

### Production Deployment
```bash
# 1. Push code
git add .
git commit -m "ready for prod"
git push origin main

# 2. In Railway dashboard
# - Connect repo
# - Add PostgreSQL
# - Add Redis
# - Set env variables
# - Deploy

# 3. Test
curl https://your-app.railway.app/health

# 4. Initialize DB
railway shell
python backend/init_db.py
```

---

## Expected Timings

| Action | Time |
|--------|------|
| Docker startup | 10-15 seconds |
| First idea generation | 10-20 seconds (LLM + search) |
| Subsequent generations | 5-10 seconds (cached) |
| Railway deployment | 2-5 minutes |
| Database init | 5 seconds |

---

## Success Criteria

✅ **Local Testing Passed** if:
- All 4 containers running
- `/health` returns `{"status":"ok"}`
- Registration works
- Ideas generate (even partial)
- Reviews submit

✅ **Production Ready** if:
- All tests pass against Railway URL
- Logs show no errors
- Response times reasonable (<10s for ideas)
- Performance monitoring works

---

## Need Help?

**Check logs:**
```bash
# Local
docker-compose logs -f [service-name]

# Production
railway logs -f
```

**Common errors:**
- `401 Unauthorized` → Check API keys
- `Connection refused` → Services not running
- `Timeout` → LLM/search APIs slow
- `CORS error` → Check CORS_ORIGINS setting
