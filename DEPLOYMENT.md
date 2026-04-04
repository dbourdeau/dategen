# DateGen Deployment Guide

## Pre-Deployment Checklist

- [ ] All environment variables set in `.env`
- [ ] GitHub repo created and code pushed
- [ ] API keys obtained:
  - [ ] OpenRouter API key (for LLM)
  - [ ] SerpAPI key (for web search)
- [ ] Railway account created
- [ ] PostgreSQL and Redis provisioned (or using Railway's add-ons)

---

## Step 1: Set Up GitHub Repository

```bash
cd dategen
git init
git add .
git commit -m "chore: initial commit"
git remote add origin https://github.com/YOUR_USERNAME/dategen.git
git push -u origin main
```

---

## Step 2: Configure Railway

### Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project

### Add Services

#### Database (PostgreSQL)
1. Click "Add Service"
2. Select "Database"
3. Choose "PostgreSQL"
4. Railway auto-creates and provides `DATABASE_URL`

#### Cache (Redis)
1. Click "Add Service"
2. Select "Database"
3. Choose "Redis"
4. Railway auto-creates and provides `REDIS_URL`

#### Connect GitHub Repo
1. Click "Add Service"
2. Select "GitHub"
3. Authorize and select `dategen` repo
4. Railway auto-detects `Dockerfile` and deploys

---

## Step 3: Set Environment Variables in Railway

In Railway dashboard → Variables:

```
OPENROUTER_API_KEY=sk-or-...          # From https://openrouter.ai
SERP_API_KEY=...                        # From https://serpapi.com
SECRET_KEY=generate-secure-key          # Use: python -c "import secrets; print(secrets.token_urlsafe(32))"
CORS_ORIGINS=${{ Railway.domain }}      # Auto-populated
ENV=production
```

---

## Step 4: Prepare Backend

### Update database.py for Railway
Railway sets `DATABASE_URL` automatically. Ensure `models.py` imports are correct:

```python
# backend/models.py - already has correct imports
from database import Base
```

---

## Step 5: Deploy

### Via Railway CLI
```bash
npm install -g @railway/cli
railway login
railway deploy
```

### Via GitHub Auto-Deploy
1. Push code to `main` branch
2. Railway automatically detects and deploys
3. Monitor at https://railway.app/dashboard

---

## Step 6: Verify Deployment

```bash
# Get Railway app URL
railway variables

# Test health endpoint
curl https://your-app.railway.app/health

# Should return:
# {"status": "ok"}
```

---

## Step 7: Run Database Migrations

If first deployment, initialize database:

```bash
railway shell
cd backend
python init_db.py
exit
```

---

## Post-Deployment Checklist

- [ ] Frontend loads at Railway URL
- [ ] API responds to health check
- [ ] Can register/login
- [ ] Can set preferences
- [ ] Can generate ideas
- [ ] Can submit reviews

---

## Troubleshooting

### Can't connect to database?
```bash
# Check DATABASE_URL is set
railway variables | grep DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### LLM not working?
```bash
# Verify API key
railway variables | grep OPENROUTER

# Test OpenRouter manually
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Search not working?
```bash
# Verify SerpAPI key
railway variables | grep SERP_API_KEY

# Test search
curl "https://serpapi.com/search?q=test&api_key=$SERP_API_KEY"
```

### Frontend not loading?
```bash
# Check CORS origins
railway variables | grep CORS_ORIGINS

# Frontend should be able to call backend API
```

---

## Updating After Deployment

1. Make code changes locally
2. Commit and push to GitHub
3. Railway auto-rebuilds and deploys
4. Monitor logs:
   ```bash
   railway logs
   ```

---

## Scaling

If traffic increases:

1. **Increase Railway CPU/RAM** in dashboard
2. **Add more Redis capacity** if caching hit rate drops
3. **Consider database read replicas** for high traffic

---

## Security

- [ ] Rotate `SECRET_KEY` regularly
- [ ] Keep API keys secure (use Railway environment variables)
- [ ] Enable HTTPS (Railway does this automatically)
- [ ] Set up monitoring/alerts in Railway dashboard
- [ ] Regularly update dependencies

---

## Support

Issues? Check:
1. Railway logs: `railway logs`
2. Backend errors: `railway logs --service backend`
3. Database: `railway shell` → `psql $DATABASE_URL`
4. Environment: `railway variables`

---

**Ready to launch?** Push to GitHub and Railway handles the rest! 🚀

Contact: [your contact info]
