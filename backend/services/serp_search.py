"""Web search service using Exa API."""

import asyncio
import os
import httpx
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from services.curated_catalog import get_curated_city_results

EXA_API_KEY = (os.getenv("EXA_API_KEY") or "").strip()
EXA_API_URL = "https://api.exa.ai/search"


def _dedupe_results(items: List[Dict], limit: int = 10) -> List[Dict]:
    """Dedupe aggregated search results by URL/title while preserving order."""
    seen = set()
    output: List[Dict] = []

    for item in items:
        key = ((item.get("link") or "").strip().lower(), (item.get("title") or "").strip().lower())
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
        if len(output) >= limit:
            break

    return output


async def search_with_exa(query: str, num_results: int = 5, use_autoprompt: bool = True) -> List[Dict]:
    """
    Search using Exa API.
    
    Returns list of search results with title, url, and snippet.
    """
    if not EXA_API_KEY:
        raise RuntimeError("EXA_API_KEY is not configured")
    
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }
    
    payload = {
        "query": query,
        "numResults": num_results,
        "useAutoprompt": use_autoprompt,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            for attempt in range(3):
                response = await client.post(
                    EXA_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    results = []
                    if "results" in data:
                        for result in data["results"][:num_results]:
                            results.append({
                                "title": result.get("title", ""),
                                "link": result.get("url", ""),
                                "snippet": result.get("text", ""),
                            })
                    return results

                if response.status_code == 429 and attempt < 2:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue

                raise RuntimeError(f"Exa API error: {response.status_code}")
    except Exception as e:
        raise RuntimeError(f"Search error: {e}")


async def search_with_exa_safe(query: str, num_results: int = 3, use_autoprompt: bool = True) -> List[Dict]:
    """Return empty results instead of aborting the entire pipeline on query-level failure."""
    try:
        return await search_with_exa(query, num_results=num_results, use_autoprompt=use_autoprompt)
    except Exception:
        return []


async def search_dining(city: str, budget_max: int, dietary_restrictions: List[str] = None) -> Dict[str, List[Dict]]:
    """Search for restaurants and new openings — covers dining options."""
    dietary_query = " ".join(dietary_restrictions) if dietary_restrictions else ""
    year = datetime.utcnow().year
    queries = [
        f"best romantic date night restaurants in {city} under ${budget_max} {dietary_query}".strip(),
        f"best date night restaurants {city} with specific venue names",
        f"new restaurant openings in {city} {year}",
    ]

    results = []
    for query in queries:
        results.extend(await search_with_exa_safe(query, num_results=4))

    return {"restaurants": _dedupe_results(results, limit=12)}


async def search_activities_and_events(city: str, interests: List[str]) -> Dict[str, List[Dict]]:
    """Search for activities, events, and low-cost ideas in one pass."""
    interests_query = " ".join(interests[:4]) if interests else "museums art music"
    queries = [
        f"best couples activities in {city} with exact venue names {interests_query}",
        f"events concerts comedy shows happening this weekend in {city}",
        f"free and cheap date ideas in {city} parks trails walks under $25",
    ]

    results = []
    for query in queries:
        results.extend(await search_with_exa_safe(query, num_results=4))

    deduped = _dedupe_results(results, limit=20)

    activities = []
    events = []
    low_cost = []
    for item in deduped:
        lowered = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
        if any(token in lowered for token in ["concert", "show", "festival", "comedy", "tickets", "event", "weekend"]):
            events.append(item)
        elif any(token in lowered for token in ["free", "cheap", "walk", "trail", "park", "riverwalk", "bike"]):
            low_cost.append(item)
        else:
            activities.append(item)

    return {
        "activities": activities[:10],
        "events": events[:10],
        "low_cost": low_cost[:10],
    }


async def search_editorial(city: str) -> Dict[str, List[Dict]]:
    """Search editorial guides and Reddit for curated date recommendations."""
    queries = [
        f"best date ideas in {city} with specific places Time Out Infatuation",
        f"site:reddit.com best date night spots in {city}",
    ]

    results = []
    for query in queries:
        results.extend(await search_with_exa_safe(query, num_results=4, use_autoprompt=False))

    return {"editorial": _dedupe_results(results, limit=10)}


async def search_all(
    city: str,
    budget: int,
    interests: List[str],
    restrictions: List[str] = None,
    db: Session = None,
) -> Dict:
    """
    Parallel search across 3 consolidated categories: dining, activities/events, editorial.
    """
    dining_result, activities_result, editorial_result = await asyncio.gather(
        search_dining(city, budget, restrictions),
        search_activities_and_events(city, interests),
        search_editorial(city),
    )

    curated = get_curated_city_results(db, city) if db else {
        "restaurants": [],
        "activities": [],
        "events": [],
        "low_cost": [],
    }

    aggregated = {
        "restaurants": _dedupe_results(curated.get("restaurants", []) + dining_result.get("restaurants", []), limit=12),
        "activities": _dedupe_results(curated.get("activities", []) + activities_result.get("activities", []), limit=12),
        "events": _dedupe_results(curated.get("events", []) + activities_result.get("events", []), limit=10),
        "low_cost": _dedupe_results(curated.get("low_cost", []) + activities_result.get("low_cost", []), limit=12),
        "editorial": _dedupe_results(editorial_result.get("editorial", []), limit=10),
    }

    if not any(aggregated.values()):
        raise RuntimeError("Exa rate limited or returned no usable search results")

    return aggregated
