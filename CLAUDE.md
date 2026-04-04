# DateGen Developer Guide

## Alignment Rules

### Code Style
- Backend: PEP 8, type hints everywhere
- Frontend: TypeScript, React hooks
- Consistent naming: snake_case (Python), camelCase (JS)

### API Contract
- All endpoints require JWT token in `Authorization: Bearer <token>` header
- Responses use `application/json`
- Errors return appropriate HTTP codes with `{"detail": "error message"}`

### Database
- All user data is associated via `user_id` (FK)
- Soft deletes preferred for audit trail (add `deleted_at` column)
- Use indexes on frequently queried columns (user_id, created_at)

### LLM Prompts
- Always include reasoning in synthesis
- Return structured JSON only (no markdown wrapping in production)
- Include confidence scores for ideas
- Store search results for citations

### Preference Learning
- Weight updates happen immediately after review submission
- Normalize weights to 0-1 range
- Cold start: fallback to mock ideas first 2-3 dates
- Historical average: use past N reviews (default 5)

## Deployment Pipeline

1. Push to GitHub `main` branch
2. Railway auto-builds and deploys
3. Database migrations (if any): manual up `.sql` files
4. Rollback: previous builds are kept in Railway

## Common Tasks

### Add New Preference Field
1. Add column to `UserPreferences` model in `models.py`
2. Add field to schemas in `schemas.py`
3. Migrate database (create migration script)
4. Add UI input in `Preferences.tsx`

### Add New Idea Criteria
1. Update LLM prompt in `llm_synthesis.py`
2. Modify `DateIdea` model if storing new data
3. Update learning logic in `preference_learn.py` if it affects weights

### Debug Failing Forecast
- Check logs in Railway dashboard
- Verify API keys in environment
- Test LLM endpoint manually: `curl -X POST https://openrouter.ai/api/v1/chat/completions ...`
- Test search: `curl "https://serpapi.com/search?q=test&api_key=YOUR_KEY"`

## Performance

- Cache search results in Redis (30 min TTL)
- Batch database queries where possible
- Use indexes on `user_id`, `created_at`
- Async endpoints for I/O (search, LLM calls)

## Security

- Hash passwords with bcrypt
- JWTs expire after 24 hours
- Validate inputs with Pydantic (reject invalid schemas)
- Sanitize user text inputs (use parameterized queries)
- CORS limited to frontend domain

---

Questions? Check the README.md or open an issue!
