"""Gemini 2.0 Flash service for generating travel itineraries."""

import json
import os
import re
from typing import Any

import google.generativeai as genai


def _get_api_key() -> str:
    try:
        from backend.core.secrets import get_secret
        return get_secret("gemini-api-key")
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")


async def generate_itinerary(
    preferences: dict[str, Any],
    project_id: str = "promptwars-rr",
    location: str = "us-central1",
) -> dict[str, Any]:
    """Generate a structured day-by-day travel itinerary using Gemini 2.0 Flash.

    Args:
        preferences: A dict describing the traveller's preferences.
        project_id: GCP project (kept for API compatibility).
        location: GCP region (kept for API compatibility).

    Returns:
        Parsed dict with destination and days keys, or error dict on failure.
    """
    raw_text: str = ""
    try:
        api_key = _get_api_key()
        genai.configure(api_key=api_key)

        destination: str = preferences.get("destination", "an unspecified destination")
        duration: int = int(preferences.get("duration_days", 3))
        interests: list[str] = preferences.get("interests", [])
        budget: str = preferences.get("budget", "moderate")
        travel_style: str = preferences.get("travel_style", "balanced")

        interests_text: str = (
            ", ".join(interests) if interests else "general sightseeing"
        )

        prompt: str = f"""You are an expert travel planner. Create a detailed {duration}-day itinerary for {destination}.

Traveller preferences:
- Interests: {interests_text}
- Budget: {budget}
- Travel style: {travel_style}

Return ONLY a valid JSON object — no markdown fences, no extra text — with this exact structure:
{{
  "destination": "<city or region name>",
  "days": [
    {{
      "day": 1,
      "morning": "<morning activity description>",
      "afternoon": "<afternoon activity description>",
      "evening": "<evening activity description>",
      "tips": "<practical tip for the day>"
    }}
  ]
}}

Generate exactly {duration} day objects. Make each activity specific and actionable."""

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = await model.generate_content_async(prompt)
        raw_text = response.text.strip()

        cleaned: str = re.sub(r"^```(?:json)?\s*", "", raw_text)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        itinerary: dict[str, Any] = json.loads(cleaned)
        return itinerary

    except json.JSONDecodeError as exc:
        return {
            "raw_text": raw_text,
            "error": f"Failed to parse Gemini response as JSON: {exc}",
        }
    except Exception as exc:
        return {
            "raw_text": raw_text,
            "error": f"Itinerary generation failed: {exc}",
        }
