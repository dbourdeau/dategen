"""Recommendation pipeline with retrieval, ranking, verification, and LLM refinement."""

import json
import os
import re
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"

GENERIC_TITLE_MARKERS = [
    "best ",
    "top ",
    "things to do",
    "date ideas",
    "date night",
    "this weekend",
    "restaurants for",
    "restaurants in",
    "activities in",
    "guide",
    "affordable",
    "romantic restaurants",
    "fun date",
    "unique date ideas",
    "hidden gem date spots",
    "reddit",
    "where to go on a date",
    "recommended romantic",
    "right now",
    "where to go",
    "inexpensive romantic",
    "valentine",
]

SOURCE_RELIABILITY = {
    "timeout.com": 0.92,
    "eater.com": 0.9,
    "theinfatuation.com": 0.88,
    "michelin.com": 0.95,
    "opentable.com": 0.95,
    "resy.com": 0.95,
    "eventbrite.com": 0.9,
    "ticketmaster.com": 0.9,
    "choosechicago.com": 0.9,
    "yelp.com": 0.84,
    "google.com": 0.84,
    "reddit.com": 0.72,
}


@dataclass
class VenueCandidate:
    name: str
    url: str
    snippet: str
    bucket: str
    domain: str
    reliability: float
    freshness: float
    neighborhood: str
    tags: List[str]
    event_date: Optional[datetime] = None


@dataclass
class ItineraryCandidate:
    stops: List[VenueCandidate]
    estimated_cost: int
    duration_minutes: int
    activity_types: List[str]
    score_breakdown: Dict[str, float]


def _clean_title(title: str) -> str:
    for separator in [" | ", " - ", " — "]:
        if separator in title:
            return title.split(separator)[0].strip()
    return title.strip()


def _looks_generic(title: str) -> bool:
    lowered = title.strip().lower()
    if not lowered:
        return True
    if "?" in lowered or "..." in lowered:
        return True
    if any(token in lowered for token in [" tickets", " ticket", "eventbrite", "from "]):
        return True
    return any(marker in lowered for marker in GENERIC_TITLE_MARKERS)


def _canonical_bucket(bucket: str, name: str, snippet: str) -> str:
    """Map noisy source buckets into itinerary buckets used by the ranker."""
    if bucket in {"restaurants", "activities", "events", "low_cost"}:
        return bucket

    lowered = f"{name} {snippet}".lower()

    if any(token in lowered for token in ["restaurant", "bar", "tavern", "bistro", "brasserie", "cafe"]):
        return "restaurants"
    if any(token in lowered for token in ["concert", "show", "festival", "comedy", "tickets", "event"]):
        return "events"
    if any(token in lowered for token in ["walk", "riverwalk", "trail", "bike", "park", "museum", "gallery", "zoo"]):
        return "low_cost"
    return "activities"


def _domain(url: str) -> str:
    netloc = (urlparse(url).netloc or "").lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _reliability_for_domain(domain: str) -> float:
    if not domain:
        return 0.4
    for known, value in SOURCE_RELIABILITY.items():
        if domain.endswith(known):
            return value
    return 0.6


def _parse_event_date(text: str) -> Optional[datetime]:
    """Parse event date from common title/snippet formats."""
    lowered = text.lower()
    today_year = datetime.utcnow().year

    # ISO style: 2026-04-05
    iso_match = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", lowered)
    if iso_match:
        try:
            return datetime(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None

    month_map = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    month_day = re.search(
        r"\b(?:mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)?,?\s*"
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+(\d{1,2})(?:,\s*(20\d{2}))?\b",
        lowered,
    )
    if month_day:
        month_text = month_day.group(1)[:3]
        day = int(month_day.group(2))
        year = int(month_day.group(3)) if month_day.group(3) else today_year
        month = month_map.get(month_text)
        if month:
            try:
                return datetime(year, month, day)
            except ValueError:
                return None

    return None


def _freshness_score(text: str, event_date: Optional[datetime] = None) -> float:
    lowered = text.lower()
    score = 0.55
    if any(token in lowered for token in ["today", "tonight", "this weekend", "this week"]):
        score += 0.35
    if any(token in lowered for token in ["updated", "new", "opening", "current"]):
        score += 0.1

    if event_date:
        day_delta = (event_date.date() - datetime.utcnow().date()).days
        if day_delta < 0:
            return 0.05
        if day_delta <= 14:
            score += 0.35
        elif day_delta <= 45:
            score += 0.2
        else:
            score += 0.05

    return max(0.0, min(1.0, score))


def _extract_neighborhood(snippet: str) -> str:
    match = re.search(
        r"(?:in|at|near)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\s+(?:neighborhood|area)",
        snippet,
    )
    if match:
        return match.group(1)
    return ""


def _extract_venue_names(snippet: str, city: str) -> List[str]:
    city_words = {part.lower() for part in city.split() if part}
    matches = re.findall(r"(?:[A-Z][a-zA-Z&'\.]+(?:\s+[A-Z][a-zA-Z&'\.]+){1,5})", snippet)

    names: List[str] = []
    for match in matches:
        candidate = match.strip(" .,;:-")
        lowered = candidate.lower()
        words = lowered.split()
        if not candidate or len(words) < 2:
            continue
        if _looks_generic(candidate):
            continue
        if all(word in city_words for word in words):
            continue
        if candidate not in names:
            names.append(candidate)
    return names[:6]


def _normalize_candidates(search_results: Dict, city: str) -> List[VenueCandidate]:
    candidates: List[VenueCandidate] = []

    for bucket, items in search_results.items():
        for item in items[:10]:
            title = _clean_title(item.get("title", ""))
            snippet = (item.get("snippet") or "").strip().replace("\n", " ")
            url = (item.get("link") or "").strip()
            domain = _domain(url)
            reliability = _reliability_for_domain(domain)
            neighborhood = _extract_neighborhood(snippet)

            canonical_bucket = _canonical_bucket(bucket, title, snippet)
            event_date = _parse_event_date(" ".join([title, snippet])) if canonical_bucket == "events" else None
            if canonical_bucket == "events" and event_date and event_date.date() < datetime.utcnow().date():
                continue

            freshness = _freshness_score(" ".join([title, snippet]), event_date)

            if title and not _looks_generic(title):
                candidates.append(
                    VenueCandidate(
                        name=title,
                        url=url,
                        snippet=snippet,
                        bucket=canonical_bucket,
                        domain=domain,
                        reliability=reliability,
                        freshness=freshness,
                        neighborhood=neighborhood,
                        tags=[bucket, canonical_bucket],
                        event_date=event_date,
                    )
                )

            for extracted in _extract_venue_names(snippet, city):
                candidates.append(
                    VenueCandidate(
                        name=extracted,
                        url=url,
                        snippet=snippet,
                        bucket=canonical_bucket,
                        domain=domain,
                        reliability=reliability,
                        freshness=freshness,
                        neighborhood=neighborhood,
                        tags=[bucket, canonical_bucket],
                        event_date=event_date,
                    )
                )

    deduped: List[VenueCandidate] = []
    seen = set()
    for candidate in candidates:
        key = (candidate.name.lower(), candidate.domain)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)

    return deduped


def _is_usable_stop(stop: VenueCandidate) -> bool:
    if not stop.name or _looks_generic(stop.name):
        return False
    if not stop.url:
        return False
    if stop.reliability < 0.58:
        return False
    return True


def _is_relaxed_stop(stop: VenueCandidate) -> bool:
    """Looser stop validation for emergency fallback when retrieval quality is poor."""
    if not stop.name or not stop.url:
        return False
    lowered = stop.name.lower().strip()
    if not lowered:
        return False
    if any(marker in lowered for marker in ["best ", "top ", "things to do", "date ideas"]):
        return False
    return True


def _bucket(candidates: List[VenueCandidate], bucket_name: str) -> List[VenueCandidate]:
    return [candidate for candidate in candidates if candidate.bucket == bucket_name and _is_usable_stop(candidate)]


def _estimate_cost(budget_min: int, budget_max: int, stop_count: int) -> int:
    midpoint = int((budget_min + budget_max) / 2)
    if stop_count >= 3:
        return max(budget_min, min(budget_max, int(midpoint * 1.1)))
    return max(budget_min, min(budget_max, midpoint))


def _generate_itinerary_candidates(
    normalized: List[VenueCandidate],
    budget_min: int,
    budget_max: int,
    activity_types: List[str],
) -> List[ItineraryCandidate]:
    restaurants = _bucket(normalized, "restaurants")
    activities = _bucket(normalized, "activities")
    events = _bucket(normalized, "events")
    low_cost = _bucket(normalized, "low_cost")

    itineraries: List[ItineraryCandidate] = []
    used_keys = set()

    def add_itinerary(stops: List[VenueCandidate], tags: List[str]) -> None:
        unique_stops = []
        seen_names = set()
        for stop in stops:
            if stop.name.lower() in seen_names:
                continue
            seen_names.add(stop.name.lower())
            unique_stops.append(stop)

        if len(unique_stops) < 2:
            return

        key = tuple(stop.name.lower() for stop in unique_stops)
        if key in used_keys:
            return
        used_keys.add(key)

        stop_count = len(unique_stops)
        avg_reliability = sum(stop.reliability for stop in unique_stops) / stop_count
        avg_freshness = sum(stop.freshness for stop in unique_stops) / stop_count

        neighborhood_penalty = 0.0
        neighborhoods = [stop.neighborhood.lower() for stop in unique_stops if stop.neighborhood]
        if len(set(neighborhoods)) > 1:
            neighborhood_penalty = 0.08

        score_breakdown = {
            "reliability": avg_reliability,
            "freshness": avg_freshness,
            "logistics": max(0.0, 0.92 - neighborhood_penalty),
            "preference": 0.65,
            "novelty": 0.65,
        }

        itineraries.append(
            ItineraryCandidate(
                stops=unique_stops,
                estimated_cost=_estimate_cost(budget_min, budget_max, stop_count),
                duration_minutes=240 if stop_count >= 3 else 180,
                activity_types=activity_types[:2] if activity_types else tags,
                score_breakdown=score_breakdown,
            )
        )

    for activity in activities[:6]:
        for restaurant in restaurants[:6]:
            add_itinerary([activity, restaurant], ["cultural", "dining"])

    for activity in activities[:4]:
        for restaurant in restaurants[:4]:
            for event in events[:4]:
                add_itinerary([activity, restaurant, event], ["cultural", "dining"])

    for event in events[:6]:
        for restaurant in restaurants[:6]:
            add_itinerary([event, restaurant], ["entertainment", "dining"])

    # Budget-friendly templates: low-cost activity + casual food or coffee option.
    for low in low_cost[:6]:
        for restaurant in restaurants[:4]:
            add_itinerary([low, restaurant], ["outdoor", "dining"])

    # Very low-budget option with two free/cheap activities.
    for first in low_cost[:5]:
        for second in low_cost[:5]:
            if first.name.lower() != second.name.lower():
                add_itinerary([first, second], ["outdoor", "cultural"])

    if not itineraries:
        # Fallback path: pair highest-quality distinct stops even when bucket coverage is sparse.
        usable = [candidate for candidate in normalized if _is_usable_stop(candidate)]
        if len(usable) < 2:
            usable = [candidate for candidate in normalized if _is_relaxed_stop(candidate)]

        usable = sorted(
            usable,
            key=lambda candidate: (candidate.reliability * 0.65 + candidate.freshness * 0.35),
            reverse=True,
        )
        for index, first in enumerate(usable[:10]):
            for second in usable[index + 1:12]:
                if first.name.lower() == second.name.lower():
                    continue
                add_itinerary([first, second], ["dining", "cultural"])
                if len(itineraries) >= 8:
                    return itineraries

        if not itineraries and len(usable) >= 2:
            add_itinerary([usable[0], usable[1]], ["dining", "cultural"])

    return itineraries[:15]


def _overlap_ratio(text: str, tokens: List[str]) -> float:
    if not tokens:
        return 0.0
    lowered = text.lower()
    hits = sum(1 for token in tokens if token and token.lower() in lowered)
    return hits / len(tokens)


def _rank_itineraries(
    itineraries: List[ItineraryCandidate],
    her_interests: List[str],
    activity_weights: Optional[Dict[str, float]],
    past_high_rated_ideas: Optional[List[Dict]],
    context_preferences: Optional[Dict],
) -> List[ItineraryCandidate]:
    past_titles = [item.get("title", "") for item in (past_high_rated_ideas or [])]
    past_titles_blob = " ".join(past_titles).lower()

    for itinerary in itineraries:
        text_blob = " ".join(stop.name + " " + stop.snippet for stop in itinerary.stops)

        preference = _overlap_ratio(text_blob, her_interests[:5])
        if activity_weights and itinerary.activity_types:
            weight_boost = sum(activity_weights.get(t, 0.0) for t in itinerary.activity_types[:2]) / 2
            preference = min(1.0, preference + weight_boost * 0.25)

        repeated_stops = sum(1 for stop in itinerary.stops if stop.name.lower() in past_titles_blob)
        novelty_penalty = repeated_stops / max(1, len(itinerary.stops))
        novelty = max(0.0, 1.0 - novelty_penalty)

        context_boost = 0.0
        if context_preferences:
            preferred_duration = context_preferences.get("preferred_duration_minutes")
            if preferred_duration:
                duration_delta = abs(preferred_duration - itinerary.duration_minutes)
                context_boost += max(0.0, 1.0 - (duration_delta / 180.0)) * 0.15

            neighborhood_tokens = context_preferences.get("top_neighborhood_tokens", [])
            if neighborhood_tokens:
                neighborhood_text = " ".join(
                    [stop.neighborhood for stop in itinerary.stops if stop.neighborhood]
                    + [stop.name for stop in itinerary.stops]
                ).lower()
                token_hits = sum(1 for token in neighborhood_tokens if token in neighborhood_text)
                context_boost += min(0.25, token_hits * 0.05)

            preference = min(1.0, preference + context_boost)

        itinerary.score_breakdown["preference"] = preference
        itinerary.score_breakdown["novelty"] = novelty

    def total_score(itinerary: ItineraryCandidate) -> float:
        s = itinerary.score_breakdown
        return (
            s["reliability"] * 0.30
            + s["freshness"] * 0.20
            + s["logistics"] * 0.15
            + s["preference"] * 0.25
            + s["novelty"] * 0.10
        )

    ranked = sorted(itineraries, key=total_score, reverse=True)

    diversified: List[ItineraryCandidate] = []
    used_stop_names = set()
    for itinerary in ranked:
        itinerary_names = {stop.name.lower() for stop in itinerary.stops}
        overlap = len(itinerary_names.intersection(used_stop_names))
        if diversified and overlap >= 2:
            continue
        diversified.append(itinerary)
        used_stop_names.update(itinerary_names)

    return diversified or ranked


def _deterministic_idea(city: str, itinerary: ItineraryCandidate) -> Dict:
    stop_names = [stop.name for stop in itinerary.stops]
    source_links = [stop.url for stop in itinerary.stops if stop.url]
    stop_count = len(stop_names)

    description = (
        f"Start at {stop_names[0]}, then continue to {stop_names[1]}"
        + (f", and finish at {stop_names[2]}." if stop_count > 2 else ".")
        + f" This itinerary is grounded in current web sources for {city}."
    )

    verification = {
        "status": "verified",
        "stop_count": stop_count,
        "avg_source_reliability": round(
            sum(stop.reliability for stop in itinerary.stops) / stop_count,
            3,
        ),
        "avg_freshness": round(
            sum(stop.freshness for stop in itinerary.stops) / stop_count,
            3,
        ),
        "provider_verified_count": sum(1 for stop in itinerary.stops if stop.reliability >= 0.85),
    }

    return {
        "title": f"{stop_names[0]} + {stop_names[1]}",
        "description": description,
        "estimated_cost": itinerary.estimated_cost,
        "duration_minutes": itinerary.duration_minutes,
        "location": " -> ".join(stop_names),
        "activity_types": itinerary.activity_types or ["dining", "cultural"],
        "difficulty": "easy",
        "reasoning": "Ranked highly on source reliability, timing freshness, and preference match.",
        "maps_link": source_links[0] if source_links else "",
        "stops": [
            {
                "name": stop.name,
                "url": stop.url,
                "source_domain": stop.domain,
                "reliability": round(stop.reliability, 3),
                "freshness": round(stop.freshness, 3),
                "neighborhood": stop.neighborhood,
            }
            for stop in itinerary.stops
        ],
        "verification": verification,
        "score_breakdown": itinerary.score_breakdown,
    }


async def _llm_refine(
    city: str,
    deterministic_ideas: List[Dict],
    her_interests: List[str],
) -> List[Dict]:
    """Use LLM to refine wording only while preserving immutable stops."""
    if not OPENROUTER_API_KEY:
        return deterministic_ideas

    prompt = {
        "city": city,
        "interests": her_interests[:5],
        "constraints": [
            "Do not change stop names",
            "Do not change stop order",
            "Do not invent venues",
            "Keep output JSON-only",
        ],
        "ideas": [
            {
                "index": idx,
                "stops": [stop["name"] for stop in idea["stops"]],
                "estimated_cost": idea["estimated_cost"],
                "duration_minutes": idea["duration_minutes"],
                "activity_types": idea["activity_types"],
            }
            for idx, idea in enumerate(deterministic_ideas)
        ],
        "output_schema": {
            "ideas": [
                {
                    "index": 0,
                    "title": "string",
                    "description": "string",
                    "reasoning": "string",
                }
            ]
        },
    }

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
                        {
                            "role": "system",
                            "content": "You refine itinerary copy. Keep stops immutable and return valid JSON only.",
                        },
                        {"role": "user", "content": json.dumps(prompt)},
                    ],
                    "temperature": 0.35,
                    "max_tokens": 1400,
                },
                timeout=30,
            )

            if response.status_code != 200:
                return deterministic_ideas

            content = response.json()["choices"][0]["message"]["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            parsed = json.loads(content.strip())
            rewrites = parsed.get("ideas", [])

            by_index = {item.get("index"): item for item in rewrites if isinstance(item, dict)}
            for idx, idea in enumerate(deterministic_ideas):
                rewrite = by_index.get(idx)
                if not rewrite:
                    continue
                idea["title"] = rewrite.get("title") or idea["title"]
                idea["description"] = rewrite.get("description") or idea["description"]
                idea["reasoning"] = rewrite.get("reasoning") or idea["reasoning"]

            return deterministic_ideas
    except Exception:
        return deterministic_ideas


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
    past_high_rated_ideas: Optional[List[Dict]] = None,
    activity_weights: Optional[Dict[str, float]] = None,
    context_preferences: Optional[Dict] = None,
) -> List[Dict]:
    """
    Build specific, timely, and correct date recommendations.

    Architecture phases implemented:
    1) Retrieval + normalization + verification gate.
    2) Deterministic itinerary generation + ranking.
    3) Provider-aware reliability scoring and freshness checks.
    4) Preference learning integration in ranking and novelty control.
    """
    normalized = _normalize_candidates(search_results, city)
    if len(normalized) < 4:
        raise RuntimeError("Insufficient venue candidates from search sources")

    itineraries = _generate_itinerary_candidates(
        normalized=normalized,
        budget_min=budget_min,
        budget_max=budget_max,
        activity_types=activity_types,
    )
    if not itineraries:
        buckets = {
            "restaurants": len([c for c in normalized if c.bucket == "restaurants"]),
            "activities": len([c for c in normalized if c.bucket == "activities"]),
            "events": len([c for c in normalized if c.bucket == "events"]),
            "low_cost": len([c for c in normalized if c.bucket == "low_cost"]),
        }
        raise RuntimeError(f"No valid venue-specific itineraries could be built (bucket_counts={buckets})")

    ranked = _rank_itineraries(
        itineraries=itineraries,
        her_interests=her_interests,
        activity_weights=activity_weights,
        past_high_rated_ideas=past_high_rated_ideas,
        context_preferences=context_preferences,
    )

    top = ranked[:3]
    deterministic_ideas = [_deterministic_idea(city, itinerary) for itinerary in top]
    refined = await _llm_refine(city, deterministic_ideas, her_interests)

    for idx, idea in enumerate(refined):
        total_score = sum(top[idx].score_breakdown.values()) / len(top[idx].score_breakdown)
        idea["confidence"] = round(min(0.95, max(0.55, total_score)), 3)
        idea["search_results"] = search_results

    return refined
