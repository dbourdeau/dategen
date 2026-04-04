"""Web search service using SerpAPI."""

import os
import httpx
import json
from typing import List, Dict

SERP_API_KEY = os.getenv("SERP_API_KEY", "demo")
SERP_API_URL = "https://serpapi.com/search"


async def search_restaurants(city: str, budget_max: int, dietary_restrictions: List[str] = None) -> List[Dict]:
    """
    Search for restaurants matching budget and restrictions.
    
    Returns list of restaurant results from SerpAPI.
    """
    dietary_query = " ".join(dietary_restrictions) if dietary_restrictions else ""
    query = f"best restaurants in {city} under ${budget_max} {dietary_query}".strip()
    
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": 5,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(SERP_API_URL, params=params, timeout=10)
            data = response.json()
            
            # Extract relevant results
            results = []
            if "organic_results" in data:
                for result in data["organic_results"][:5]:
                    results.append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                    })
            return results
    except Exception as e:
        print(f"Restaurant search error: {e}")
        return []


async def search_activities(city: str, interests: List[str]) -> List[Dict]:
    """
    Search for activities and attractions matching interests.
    """
    interests_query = " ".join(interests) if interests else "activities"
    query = f"best {interests_query} activities in {city} couples"
    
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": 5,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(SERP_API_URL, params=params, timeout=10)
            data = response.json()
            
            results = []
            if "organic_results" in data:
                for result in data["organic_results"][:5]:
                    results.append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                    })
            return results
    except Exception as e:
        print(f"Activities search error: {e}")
        return []


async def search_events(city: str) -> List[Dict]:
    """
    Search for upcoming events in the city.
    """
    query = f"events happening this weekend in {city}"
    
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": 5,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(SERP_API_URL, params=params, timeout=10)
            data = response.json()
            
            results = []
            if "organic_results" in data:
                for result in data["organic_results"][:5]:
                    results.append({
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                    })
            return results
    except Exception as e:
        print(f"Events search error: {e}")
        return []


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
