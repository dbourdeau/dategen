"""LLM synthesis service using OpenRouter."""

import os
import json
import httpx
from typing import List, Dict, Optional

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"


def _clean_title(title: str) -> str:
    """Trim noisy title suffixes from search result titles."""
    for separator in [" | ", " - ", " — "]:
        if separator in title:
            return title.split(separator)[0].strip()
    return title.strip()


def _collect_candidates(search_results: Dict) -> Dict[str, List[Dict]]:
    """Normalize top search results into named venue candidates by bucket."""
    buckets: Dict[str, List[Dict]] = {}
    for bucket, items in search_results.items():
        buckets[bucket] = []
        for item in items[:8]:
            title = _clean_title(item.get("title", ""))
            if not title:
                continue
            buckets[bucket].append(
                {
                    "title": title,
                    "link": (item.get("link") or "").strip(),
                    "snippet": (item.get("snippet") or "").strip().replace("\n", " "),
                }
            )
    return buckets


def _build_search_grounded_ideas(
    city: str,
    budget_min: int,
    budget_max: int,
    search_results: Dict,
    her_interests: List[str],
    activity_types: List[str],
) -> List[Dict]:
    """Build specific itineraries directly from search results when LLM output is too generic."""
    candidates = _collect_candidates(search_results)
    restaurants = candidates.get("restaurants", [])
    activities = candidates.get("activities", [])
    events = candidates.get("events", [])
    reddit = candidates.get("reddit", [])
    editorial = candidates.get("date_ideas", [])

    ideas: List[Dict] = []

    pairings = [
        (activities[0] if activities else None, restaurants[0] if restaurants else None, events[0] if events else None),
        (reddit[0] if reddit else (activities[1] if len(activities) > 1 else None), restaurants[1] if len(restaurants) > 1 else (restaurants[0] if restaurants else None), None),
        (editorial[0] if editorial else (events[1] if len(events) > 1 else None), restaurants[2] if len(restaurants) > 2 else (restaurants[0] if restaurants else None), activities[2] if len(activities) > 2 else None),
    ]

    for first_stop, second_stop, third_stop in pairings:
        stops = [stop for stop in [first_stop, second_stop, third_stop] if stop and stop.get("title")]
        unique_titles = []
        for stop in stops:
            if stop["title"] not in unique_titles:
                unique_titles.append(stop["title"])
        if len(unique_titles) < 2:
            continue

        title = " + ".join(unique_titles[:2])
        itinerary = " -> ".join(unique_titles)
        links = [stop.get("link") for stop in stops if stop.get("link")]
        snippets = [stop.get("snippet") for stop in stops if stop.get("snippet")]
        interest_text = ", ".join(her_interests[:3]) if her_interests else "shared interests"
        activity_text = activity_types[:2] if activity_types else ["dining", "cultural"]

        ideas.append(
            {
                "title": title,
                "description": (
                    f"Start at {unique_titles[0]}, then continue to {unique_titles[1]}"
                    + (f", and finish at {unique_titles[2]}." if len(unique_titles) > 2 else ".")
                    + (f" This route is grounded in current web recommendations for {city}." if city else "")
                ),
                "estimated_cost": max(budget_min, min(budget_max, int((budget_min + budget_max) / 2))),
                "duration_minutes": 180 if len(unique_titles) == 2 else 240,
                "location": itinerary,
                "activity_types": activity_text,
                "difficulty": "easy",
                "reasoning": (
                    f"Uses specific currently recommended venues and matches interests around {interest_text}."
                    + (f" Research highlights: {snippets[0][:140]}" if snippets else "")
                ),
                "maps_link": links[0] if links else "",
            }
        )

    return ideas[:3]


def _format_search_context(search_results: Dict) -> str:
    """Format search results into compact venue lines for stronger grounding."""
    lines: List[str] = []
    for bucket in search_results.keys():
        lines.append(f"{bucket.upper()}:")
        for idx, item in enumerate(search_results.get(bucket, [])[:5], start=1):
            title = item.get("title", "").strip()
            link = item.get("link", "").strip()
            snippet = item.get("snippet", "").strip().replace("\n", " ")
            lines.append(f"{idx}. {title} | {link} | {snippet[:200]}")
        lines.append("")
    return "\n".join(lines)


def _collect_candidate_titles(search_results: Dict) -> List[str]:
    """Collect candidate venue titles from search results for specificity checks."""
    titles: List[str] = []
    for bucket in search_results.keys():
        for item in search_results.get(bucket, [])[:5]:
            title = (item.get("title") or "").strip()
            if title:
                titles.append(title)
    return titles


def _is_specific_idea(idea: Dict, city: str, candidate_titles: List[str]) -> bool:
    """Check whether an idea references concrete venues and avoids generic-only output."""
    combined = " ".join([
        str(idea.get("title", "")),
        str(idea.get("description", "")),
        str(idea.get("location", "")),
    ]).lower()

    city_only = str(idea.get("location", "")).strip().lower() in {city.lower(), "", "downtown"}
    venue_hits = sum(1 for t in candidate_titles if t and t.lower() in combined)
    has_url = "http://" in combined or "https://" in combined

    return (not city_only) and (venue_hits >= 1 or has_url)


def _validate_specificity(ideas: List[Dict], city: str, search_results: Dict) -> bool:
    """Require most ideas to include concrete venues from web results."""
    if not ideas:
        return False

    candidate_titles = _collect_candidate_titles(search_results)
    specific_count = sum(1 for idea in ideas if _is_specific_idea(idea, city, candidate_titles))
    return specific_count >= max(2, len(ideas) - 1)


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
    
    search_context = _format_search_context(search_results)

    prompt = f"""
You are a creative date planner. Generate 3-4 date ideas for a couple in {city}.

CONSTRAINTS:
- Budget: ${budget_min}-${budget_max}
- Duration: {duration_min}-{duration_max} hours
- Her top interests: {', '.join(weighted_interests)}
- Activity types to prioritize: {', '.join(weighted_activities)}
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}

RESEARCH CONTEXT:
{search_context}

{past_ideas_context}

Generate creative, HYPER-SPECIFIC date ideas. Avoid repeating recent suggestions.

NON-NEGOTIABLE SPECIFICITY RULES:
- Every idea must include exact place names (restaurant, museum, venue, event space) from the research context above.
- Every idea must include a concrete mini-itinerary (2-3 stops in order).
- Never use generic phrases like "a local restaurant" or "a nearby museum".
- `location` must name specific venues and neighborhood, not just "{city}".
- Include at least one source URL per idea in `maps_link`.

Return ONLY valid JSON (no extra text) with structure:
{{
  "ideas": [
    {{
      "title": "Activity name",
      "description": "2-3 sentence description",
      "estimated_cost": 75,
      "duration_minutes": 180,
            "location": "Venue A (neighborhood) -> Venue B (neighborhood)",
      "activity_types": ["outdoor", "dining"],
      "difficulty": "medium",
            "reasoning": "Why this matches their preferences",
            "maps_link": "https://..."
    }}
  ]
}}
"""
    
    try:
        async with httpx.AsyncClient() as client:
            for attempt in range(2):
                current_prompt = prompt
                if attempt == 1:
                    current_prompt += (
                        "\n\nYour previous output was too generic. "
                        "Retry and ensure every idea names exact venues from RESEARCH CONTEXT."
                    )

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
                            {"role": "user", "content": current_prompt}
                        ],
                        "temperature": 0.6,
                        "max_tokens": 1800,
                    },
                    timeout=30,
                )

                if response.status_code != 200:
                    raise RuntimeError(f"OpenRouter error: {response.status_code}")

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON from response
                # Try to extract JSON from markdown code blocks first
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                ideas_data = json.loads(content.strip())
                ideas = ideas_data.get("ideas", [])

                # Add confidence and search results to each idea
                for idea in ideas:
                    idea["confidence"] = 0.85
                    idea["search_results"] = search_results
                    # Ensure activity_types exists
                    if "activity_types" not in idea:
                        idea["activity_types"] = []

                if _validate_specificity(ideas, city, search_results):
                    return ideas

            grounded_ideas = _build_search_grounded_ideas(
                city=city,
                budget_min=budget_min,
                budget_max=budget_max,
                search_results=search_results,
                her_interests=her_interests,
                activity_types=activity_types,
            )
            if grounded_ideas:
                for idea in grounded_ideas:
                    idea["confidence"] = 0.78
                    idea["search_results"] = search_results
                return grounded_ideas

            raise RuntimeError("LLM returned ideas that were too generic")
                
    except Exception as e:
        raise RuntimeError(f"LLM synthesis error: {e}")
