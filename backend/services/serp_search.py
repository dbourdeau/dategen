"""Web search service using Exa API."""

import os
import httpx
from typing import List, Dict

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


async def search_with_exa(query: str, num_results: int = 5) -> List[Dict]:
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
        "useAutoprompt": True,
    }
    
    try:
        async with httpx.AsyncClient() as client:
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
            else:
                raise RuntimeError(f"Exa API error: {response.status_code}")
    except Exception as e:
        raise RuntimeError(f"Search error: {e}")


async def search_restaurants(city: str, budget_max: int, dietary_restrictions: List[str] = None) -> List[Dict]:
    """
    Search for restaurants matching budget and restrictions.
    
    Returns list of restaurant results from Exa API.
    """
    dietary_query = " ".join(dietary_restrictions) if dietary_restrictions else ""
    queries = [
        f"best romantic restaurants in {city} under ${budget_max} {dietary_query}".strip(),
        f"best date night restaurants {city} with specific venue names",
        f"Eater {city} best restaurants date night",
        f"Michelin guide {city} bib gourmand date night",
    ]

    results = []
    for query in queries:
        results.extend(await search_with_exa(query, num_results=4))

    return _dedupe_results(results, limit=10)


async def search_activities(city: str, interests: List[str]) -> List[Dict]:
    """
    Search for activities and attractions matching interests.
    """
    interests_query = " ".join(interests[:4]) if interests else "museums art music"
    queries = [
        f"best couples activities in {city} with exact venue names {interests_query}",
        f"best museums and exhibits in {city} this weekend",
        f"best cocktails speakeasy jazz bars in {city} for dates",
        f"top interactive date activities in {city} (pottery classes, cooking classes, comedy clubs)",
    ]

    results = []
    for query in queries:
        results.extend(await search_with_exa(query, num_results=4))

    return _dedupe_results(results, limit=10)


async def search_events(city: str) -> List[Dict]:
    """
    Search for upcoming events in the city.
    """
    queries = [
        f"events happening this weekend in {city} for couples",
        f"Eventbrite {city} date night events this week",
        f"Time Out {city} best events this weekend",
        f"concerts comedy shows in {city} this weekend",
    ]

    results = []
    for query in queries:
        results.extend(await search_with_exa(query, num_results=4))

    return _dedupe_results(results, limit=10)


async def search_date_idea_lists(city: str) -> List[Dict]:
    """Search curated editorial lists that contain highly specific date ideas and venues."""
    queries = [
        f"best date ideas in {city} with specific places",
        f"Time Out {city} date ideas",
        f"The Infatuation {city} date night guide",
        f"Choose Chicago romantic things to do",
    ]

    results = []
    for query in queries:
        results.extend(await search_with_exa(query, num_results=4))

    return _dedupe_results(results, limit=10)


async def search_reddit_date_ideas(city: str) -> List[Dict]:
    """Search Reddit threads for hyper-local date recommendations with named places."""
    queries = [
        f"site:reddit.com best date night in {city}",
        f"site:reddit.com {city} best restaurants for date night",
        f"site:reddit.com {city} museum date ideas",
        f"site:reddit.com {city} hidden gem date spots",
    ]

    results = []
    for query in queries:
        results.extend(await search_with_exa(query, num_results=4))

    return _dedupe_results(results, limit=10)


async def search_all(city: str, budget: int, interests: List[str], restrictions: List[str] = None) -> Dict:
    """
    Parallel search across restaurants, activities, and events.
    """
    import asyncio
    
    results = await asyncio.gather(
        search_restaurants(city, budget, restrictions),
        search_activities(city, interests),
        search_events(city),
        search_date_idea_lists(city),
        search_reddit_date_ideas(city),
    )
    
    return {
        "restaurants": results[0],
        "activities": results[1],
        "events": results[2],
        "date_ideas": results[3],
        "reddit": results[4],
    }
