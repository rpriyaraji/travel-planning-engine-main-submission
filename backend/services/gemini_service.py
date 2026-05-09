"""Gemini 1.5 Pro service for generating travel itineraries via Vertex AI."""

import json
import re
from typing import Any

import vertexai
from vertexai.generative_models import GenerativeModel


async def generate_itinerary(
    preferences: dict[str, Any],
    project_id: str = "promptwars-rr",
    location: str = "us-central1",
) -> dict[str, Any]:
    """Generate a structured day-by-day travel itinerary using Gemini 1.5 Pro.

    Args:
        preferences: A dict describing the traveller's preferences, e.g.
            destination, duration, interests, budget, travel_style.
        project_id: GCP project that hosts the Vertex AI endpoint.
        location: GCP region for Vertex AI (default: us-central1).

    Returns:
        Parsed dict with keys:
          - destination (str)
          - days (list[dict]): each entry has day, morning, afternoon,
            evening, tips keys.
        On JSON parse failure returns:
          - raw_text (str): the model's raw response.
          - error (str): description of the parse failure.
    """
    try:
        vertexai.init(project=project_id, location=location)

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

        model: GenerativeModel = GenerativeModel("gemini-2.0-flash")
        response = await model.generate_content_async(prompt)
        raw_text: str = response.text.strip()

        # Strip optional markdown code fences if present
        cleaned: str = re.sub(r"^```(?:json)?\s*", "", raw_text)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        itinerary: dict[str, Any] = json.loads(cleaned)
        return itinerary

    except json.JSONDecodeError as exc:
        return {
            "raw_text": raw_text if "raw_text" in dir() else "",
            "error": f"Failed to parse Gemini response as JSON: {exc}",
        }
    except Exception as exc:
        return {
            "raw_text": "",
            "error": f"Itinerary generation failed: {exc}",
        }
