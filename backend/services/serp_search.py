"""Web search service using Exa API."""

import os
import httpx
import json
from typing import List, Dict

EXA_API_KEY = (os.getenv("EXA_API_KEY") or "").strip()
EXA_API_URL = "https://api.exa.ai/search"


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
    query = f"best restaurants in {city} under ${budget_max} {dietary_query}".strip()
    
    return await search_with_exa(query, num_results=5)


async def search_activities(city: str, interests: List[str]) -> List[Dict]:
    """
    Search for activities and attractions matching interests.
    """
    interests_query = " ".join(interests) if interests else "activities"
    query = f"best {interests_query} activities in {city} couples"
    
    return await search_with_exa(query, num_results=5)


async def search_events(city: str) -> List[Dict]:
    """
    Search for upcoming events in the city.
    """
    query = f"events happening this weekend in {city}"
    
    return await search_with_exa(query, num_results=5)


async def search_all(city: str, budget: int, interests: List[str], restrictions: List[str] = None) -> Dict:
    """
    Parallel search across restaurants, activities, and events.
    """
    import asyncio
    
    results = await asyncio.gather(
        search_restaurants(city, budget, restrictions),
        search_activities(city, interests),
        search_events(city),
    )
    
    return {
        "restaurants": results[0],
        "activities": results[1],
        "events": results[2],
    }
