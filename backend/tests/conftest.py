"""Shared pytest fixtures for the travel planner backend test suite."""

import pytest


@pytest.fixture
def plan_payload() -> dict:
    return {
        "preferences": {
            "destination": "Tokyo, Japan",
            "duration_days": 4,
            "interests": ["culture", "food"],
            "budget": "moderate",
            "origin": "London, UK",
        },
        "user_id": "fixture-user",
    }


@pytest.fixture
def fake_itinerary() -> dict:
    return {
        "destination": "Tokyo, Japan",
        "days": [
            {
                "day": 1,
                "morning": "Senso-ji Temple",
                "afternoon": "Akihabara electronics district",
                "evening": "Ramen dinner in Shinjuku",
                "tips": "Get a Suica card at the airport",
            }
        ],
    }


@pytest.fixture
def fake_saved_doc(fake_itinerary: dict) -> dict:
    return {
        **fake_itinerary,
        "id": "saved-doc-001",
        "user_id": "fixture-user",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
