"""LLM synthesis service using OpenRouter."""

import os
import json
import httpx
from typing import List, Dict, Optional

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"


async def synthesize_ideas(
    city: str,
    budget_min: int,
    budget_max: int,
    duration_min: int,
    duration_max: int,
    her_interests: List[str],
    activity_types: List[str],
    dietary_restrictions: List[str],
    search_results: Dict,
    past_high_rated_ideas: List[Dict] = None,
    activity_weights: Dict[str, float] = None,
) -> List[Dict]:
    """
    Use LLM to synthesize date ideas from search results and preferences.
    
    Returns list of 3-5 date ideas with title, description, cost, duration, reasoning.
    """
    
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")
    
    # Build context
    weighted_interests = sorted(her_interests) if not activity_weights else sorted(
        her_interests, 
        key=lambda x: activity_weights.get(x, 0), 
        reverse=True
    )[:5]
    
    weighted_activities = sorted(activity_types) if not activity_weights else sorted(
        activity_types,
        key=lambda x: activity_weights.get(x, 0),
        reverse=True
    )[:5]
    
    past_ideas_context = ""
    if past_high_rated_ideas:
        past_ideas_context = "Previous highly-rated dates:\n" + "\n".join([
            f"- {idea['title']}: {idea['description'][:100]}..."
            for idea in past_high_rated_ideas[:3]
        ])
    
    prompt = f"""
You are a creative date planner. Generate 3-4 date ideas for a couple in {city}.

CONSTRAINTS:
- Budget: ${budget_min}-${budget_max}
- Duration: {duration_min}-{duration_max} hours
- Her top interests: {', '.join(weighted_interests)}
- Activity types to prioritize: {', '.join(weighted_activities)}
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}

RESEARCH CONTEXT:
Top restaurants available:
{json.dumps(search_results.get('restaurants', [])[:3], indent=2)}

Top activities:
{json.dumps(search_results.get('activities', [])[:3], indent=2)}

Upcoming events:
{json.dumps(search_results.get('events', [])[:3], indent=2)}

{past_ideas_context}

Generate creative, specific date ideas. Avoid repeating recent suggestions.

Return ONLY valid JSON (no extra text) with structure:
{{
  "ideas": [
    {{
      "title": "Activity name",
      "description": "2-3 sentence description",
      "estimated_cost": 75,
      "duration_minutes": 180,
      "location": "specific place or neighborhood",
      "activity_types": ["outdoor", "dining"],
      "difficulty": "medium",
      "reasoning": "Why this matches their preferences"
    }}
  ]
}}
"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEFAULT_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful date planning assistant. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 1500,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Parse JSON from response
                # Try to extract JSON from markdown code blocks first
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                ideas_data = json.loads(content.strip())
                
                # Add confidence and search results to each idea
                for idea in ideas_data.get("ideas", []):
                    idea["confidence"] = 0.85
                    idea["search_results"] = search_results
                    # Ensure activity_types exists
                    if "activity_types" not in idea:
                        idea["activity_types"] = []
                
                return ideas_data.get("ideas", [])
            else:
                raise RuntimeError(f"OpenRouter error: {response.status_code}")
                
    except Exception as e:
        raise RuntimeError(f"LLM synthesis error: {e}")
