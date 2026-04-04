# DateGen - AI Date Planning Agent

AI-powered date idea generator that learns from feedback and generates personalized suggestions based on preferences, web search, and LLM synthesis.

## Features

✨ **Smart Idea Generation**
- AI-powered date idea synthesis using LLM (OpenAI GPT-4o via OpenRouter)
- Real-time web search for restaurants, events, and activities
- Context-aware suggestions based on preferences and past reviews

🧠 **Learning System**
- Tracks what worked (and what didn't) from past dates
- Dynamically weights activity types based on feedback
- Improves suggestions over time

💰 **Preference Management**
- Budget ranges, location, activity types
- Her interests and dietary restrictions
- Available time and seasonal preferences

📊 **Analytics**
- View top-rated activity types
- Track preference evolution over time
- Review history and ratings

## Tech Stack

- **Backend**: FastAPI + Python (async)
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Database**: PostgreSQL
- **Cache**: Redis
- **LLM**: OpenRouter (OpenAI GPT-4o)
- **Search**: SerpAPI
- **Deployment**: Railway
- **Dev**: Docker Compose

## Quick Start

### Prerequisites

- Docker & Docker Compose (for local dev)
- Node.js 20+ (for frontend dev without Docker)
- Python 3.11+ (for backend dev without Docker)

### Local Development (Docker)

1. **Clone the repo**
   ```bash
   git clone https://github.com/dbourdeau/dategen.git
   cd dategen
   ```

2. **Set up environment**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys:
   # - OPENROUTER_API_KEY
   # - SERP_API_KEY
   ```

3. **Start local environment**
   ```bash
   docker-compose up
   ```

4. **Access the app**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development (Manual)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Preferences
- `GET /api/preferences` - Get current preferences
- `POST /api/preferences` - Create/update preferences
- `PATCH /api/preferences` - Partial update

### Ideas
- `POST /api/ideas/generate` - Generate new date ideas
- `GET /api/ideas` - List generated ideas
- `GET /api/ideas/{id}` - Get specific idea
- `DELETE /api/ideas/{id}` - Delete idea

### Reviews
- `POST /api/reviews` - Submit review/rating
- `GET /api/reviews` - List reviews
- `PATCH /api/reviews/{id}` - Update review
- `GET /api/reviews/analytics/top-activities` - Get top activities
- `GET /api/reviews/analytics/trends` - Get trends

## Database Schema

### Users
- Store user accounts with JWT auth

### User Preferences
- Budget, location, activity types, her interests
- Duration, seasonal preferences

### Date Ideas
- Generated ideas with description, cost, duration
- Activity types, reasoning, confidence score

### Date Reviews
- Rating (1-5), feedback, date outcome
- Learning signals for preference adjustment

## Learning Algorithm

1. User rates a date idea (1-5 stars)
2. System calculates average rating per activity type
3. Updates preference weights:
   - High ratings (4-5) → boost activity type weight
   - Low ratings (1-2) → reduce activity type weight
4. Next idea generation uses updated weights

## Deployment (Railway)

1. **Connect GitHub repo** to Railway
2. **Set environment variables** in Railway dashboard:
   - `OPENROUTER_API_KEY`
   - `SERP_API_KEY`
   - `DATABASE_URL` (Railway PostgreSQL)
   - `REDIS_URL` (Railway Redis)
3. **Push to GitHub** → Auto-deploy
4. **Access app** at Railway-provided URL

### Add Services to Railway

- PostgreSQL (primary database)
- Redis (caching)

## Development

### Project Structure
```
dategen/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # DB connection
│   ├── routes/              # API endpoints
│   │   ├── auth.py
│   │   ├── preferences.py
│   │   ├── ideas.py
│   │   └── reviews.py
│   ├── services/            # Business logic
│   │   ├── serp_search.py
│   │   ├── llm_synthesis.py
│   │   └── preference_learn.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api.ts
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── railway.toml
└── .env.template
```

### Adding Features

1. Create new route in `backend/routes/`
2. Add schema in `backend/schemas.py`
3. Add model if needed in `backend/models.py`
4. Add service logic in `backend/services/`
5. Create React component in `frontend/src/components/`
6. Wire up API call in `frontend/src/api.ts`

## Future Enhancements

- [ ] Real-time SSE streaming during idea generation
- [ ] Job-based persistence (shareable URLs)
- [ ] CSV export/import
- [ ] Photo gallery from past dates
- [ ] Calendar integration
- [ ] Email notifications
- [ ] Mobile app
- [ ] Friend collaboration
- [ ] Advanced analytics dashboard

## Troubleshooting

**Database connection error?**
- Ensure PostgreSQL is running: `docker-compose ps`
- Check `DATABASE_URL` in `.env`

**LLM API key issues?**
- Verify `OPENROUTER_API_KEY` is set in `.env`
- Test at https://openrouter.ai

**Search not working?**
- Check `SERP_API_KEY` in `.env`
- Try a test search at https://serpapi.com

**Frontend not connecting to backend?**
- Check CORS origin in `.env` matches frontend URL
- Verify backend is running: http://localhost:8000/health

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT

## Contact

Questions? Ideas? Reach out or open an issue!

---

Made with ❤️ to help you plan better dates
