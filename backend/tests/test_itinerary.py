"""
Tests for the Travel Planner FastAPI backend.

All Google Cloud clients are mocked so no real network calls are made.
"""

import sys
import os
import types
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Path setup — backend/ must be on sys.path so that 'services.*' and
# 'core.*' resolve the same way they do when main.py runs.
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(BACKEND_DIR))


# ---------------------------------------------------------------------------
# Stub out heavy Google Cloud libraries BEFORE anything imports them so that
# module-level client construction (e.g. firestore.AsyncClient()) doesn't
# fail in a test environment without credentials.
# ---------------------------------------------------------------------------

def _make_stub_module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


# -- google.cloud.firestore stub --
_mock_async_client_instance = MagicMock()
_mock_firestore_mod = _make_stub_module(
    "google.cloud.firestore",
    AsyncClient=MagicMock(return_value=_mock_async_client_instance),
    AsyncDocumentReference=MagicMock,
)

# -- google.cloud.secretmanager stub --
_mock_secretmanager_mod = _make_stub_module(
    "google.cloud.secretmanager",
    SecretManagerServiceClient=MagicMock(),
)

# -- vertexai stub --
_mock_vertexai_mod = _make_stub_module("vertexai", init=MagicMock())

# -- vertexai.generative_models stub --
_mock_gen_model_cls = MagicMock()
_mock_vertexai_gen_mod = _make_stub_module(
    "vertexai.generative_models",
    GenerativeModel=_mock_gen_model_cls,
)

# -- google.cloud.language_v2 stub --
_mock_lang_async_client = MagicMock()
_mock_lang_mod = _make_stub_module(
    "google.cloud.language_v2",
    LanguageServiceAsyncClient=MagicMock(return_value=_mock_lang_async_client),
    Document=MagicMock(),
    Entity=MagicMock(),
)

# -- google.cloud.translate_v2 stub --
_mock_translate_mod = _make_stub_module(
    "google.cloud.translate_v2",
    Client=MagicMock(),
)

# -- googlemaps stub --
_mock_gmaps_mod = _make_stub_module("googlemaps", Client=MagicMock())

# Register all stubs so imports resolve without hitting the real libraries.
_stubs = {
    "google": types.ModuleType("google"),
    "google.cloud": types.ModuleType("google.cloud"),
    "google.cloud.firestore": _mock_firestore_mod,
    "google.cloud.secretmanager": _mock_secretmanager_mod,
    "google.cloud.language_v2": _mock_lang_mod,
    "google.cloud.translate_v2": _mock_translate_mod,
    "vertexai": _mock_vertexai_mod,
    "vertexai.generative_models": _mock_vertexai_gen_mod,
    "googlemaps": _mock_gmaps_mod,
}
for _name, _mod in _stubs.items():
    sys.modules.setdefault(_name, _mod)

# Make google.cloud a proper sub-package of google.
sys.modules["google"].cloud = sys.modules["google.cloud"]  # type: ignore[attr-defined]

# Now it is safe to import application modules.
import httpx
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

# Import app — this also registers routes.
from main import app  # type: ignore[import]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PLAN_REQUEST_PAYLOAD = {
    "preferences": {
        "destination": "Paris",
        "duration_days": 3,
        "interests": ["food", "history"],
        "budget": "moderate",
        "origin": "New York",
    },
    "user_id": "user-123",
}

FAKE_ITINERARY_DATA = {
    "destination": "Paris",
    "days": [
        {
            "day": 1,
            "morning": "Visit the Eiffel Tower",
            "afternoon": "Lunch at a bistro",
            "evening": "Seine river cruise",
            "tips": "Book tickets in advance",
        }
    ],
}

FAKE_SAVED_ITINERARY = {
    "id": "doc-abc-123",
    "user_id": "user-123",
    "destination": "Paris",
    "days": FAKE_ITINERARY_DATA["days"],
    "created_at": "2025-01-01T00:00:00+00:00",
}


# ===========================================================================
# 1. GET /health
# ===========================================================================


@pytest.mark.asyncio
async def test_health_returns_200():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_returns_correct_body():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "travel-planner"


# ===========================================================================
# 2. POST /plan — success path
# ===========================================================================


@pytest.mark.asyncio
async def test_plan_success():
    """Mock both service functions; expect 200 and a valid PlanResponse."""
    with patch(
        "services.gemini_service.generate_itinerary",
        new=AsyncMock(return_value=FAKE_ITINERARY_DATA),
    ), patch(
        "services.firestore_service.save_itinerary",
        new=AsyncMock(return_value="doc-abc-123"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/plan", json=PLAN_REQUEST_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["itinerary_id"] == "doc-abc-123"
    assert body["status"] == "success"
    assert "message" in body


@pytest.mark.asyncio
async def test_plan_response_shape():
    """Verify all PlanResponse fields are present."""
    with patch(
        "services.gemini_service.generate_itinerary",
        new=AsyncMock(return_value=FAKE_ITINERARY_DATA),
    ), patch(
        "services.firestore_service.save_itinerary",
        new=AsyncMock(return_value="some-id"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/plan", json=PLAN_REQUEST_PAYLOAD)

    body = response.json()
    assert set(body.keys()) >= {"itinerary_id", "status", "message"}


# ===========================================================================
# 3. POST /plan — error path (gemini raises)
# ===========================================================================


@pytest.mark.asyncio
async def test_plan_gemini_error_returns_500():
    """When generate_itinerary raises, the endpoint must return 500."""
    with patch(
        "services.gemini_service.generate_itinerary",
        new=AsyncMock(side_effect=RuntimeError("Vertex AI unavailable")),
    ), patch(
        "services.firestore_service.save_itinerary",
        new=AsyncMock(return_value="will-not-be-called"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/plan", json=PLAN_REQUEST_PAYLOAD)

    assert response.status_code == 500
    assert "Failed to generate itinerary" in response.json()["detail"]


# ===========================================================================
# 4. GET /itineraries/{user_id} — list case
# ===========================================================================


@pytest.mark.asyncio
async def test_get_itineraries_success():
    """Mock get_itineraries_for_user returning one itinerary; expect 200 and list."""
    with patch(
        "services.firestore_service.get_itineraries_for_user",
        new=AsyncMock(return_value=[FAKE_SAVED_ITINERARY]),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/itineraries/user-123")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["id"] == "doc-abc-123"
    assert body[0]["user_id"] == "user-123"


@pytest.mark.asyncio
async def test_get_itineraries_list_shape():
    """Each item in the list must have the Itinerary fields."""
    with patch(
        "services.firestore_service.get_itineraries_for_user",
        new=AsyncMock(return_value=[FAKE_SAVED_ITINERARY]),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/itineraries/user-123")

    item = response.json()[0]
    assert set(item.keys()) >= {"id", "user_id", "destination", "days", "created_at"}


# ===========================================================================
# 5. GET /itineraries/{user_id} — empty list
# ===========================================================================


@pytest.mark.asyncio
async def test_get_itineraries_empty():
    """When no itineraries exist, the endpoint should return 200 and []."""
    with patch(
        "services.firestore_service.get_itineraries_for_user",
        new=AsyncMock(return_value=[]),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/itineraries/user-no-trips")

    assert response.status_code == 200
    assert response.json() == []


# ===========================================================================
# 6. core/secrets.py — get_secret success
# ===========================================================================


def test_get_secret_returns_decoded_string():
    """Mock secretmanager client; verify get_secret returns the decoded value."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.payload.data = b"super-secret-value"
    mock_client.access_secret_version.return_value = mock_response

    with patch(
        "google.cloud.secretmanager.SecretManagerServiceClient",
        return_value=mock_client,
    ):
        from core.secrets import get_secret  # type: ignore[import]
        result = get_secret("MY_SECRET", project_id="test-project")

    assert result == "super-secret-value"


# ===========================================================================
# 7. core/secrets.py — get_secret raises RuntimeError on client error
# ===========================================================================


def test_get_secret_raises_runtime_error_on_failure():
    """If the client raises, get_secret should wrap it in RuntimeError."""
    mock_client = MagicMock()
    mock_client.access_secret_version.side_effect = Exception("permission denied")

    with patch(
        "google.cloud.secretmanager.SecretManagerServiceClient",
        return_value=mock_client,
    ):
        from core.secrets import get_secret  # type: ignore[import]
        with pytest.raises(RuntimeError, match="Failed to fetch secret"):
            get_secret("MISSING_SECRET", project_id="test-project")


# ===========================================================================
# 8. services/gemini_service.py — generate_itinerary returns dict with "days"
# ===========================================================================


@pytest.mark.asyncio
async def test_gemini_generate_itinerary_returns_days():
    """Mock vertexai and GenerativeModel; verify the returned dict has 'days'."""
    import json as _json

    fake_response_text = _json.dumps(FAKE_ITINERARY_DATA)

    mock_model_instance = MagicMock()
    mock_model_instance.generate_content_async = AsyncMock(
        return_value=MagicMock(text=fake_response_text)
    )

    # Patch the name as it was imported into gemini_service's own namespace,
    # and also patch vertexai.init which was imported the same way.
    with patch("services.gemini_service.vertexai") as mock_vx, patch(
        "services.gemini_service.GenerativeModel",
        return_value=mock_model_instance,
    ):
        mock_vx.init = MagicMock()

        from services.gemini_service import generate_itinerary  # type: ignore[import]

        result = await generate_itinerary(
            preferences={
                "destination": "Paris",
                "duration_days": 3,
                "interests": ["food"],
                "budget": "moderate",
                "travel_style": "relaxed",
            }
        )

    assert isinstance(result, dict)
    assert "days" in result
    assert isinstance(result["days"], list)
    assert len(result["days"]) >= 1


# ===========================================================================
# 9. services/firestore_service.py — save_itinerary returns a string id
# ===========================================================================


@pytest.mark.asyncio
async def test_firestore_save_itinerary_returns_string_id():
    """Mock Firestore async client; verify save_itinerary returns a string."""
    mock_doc_ref = MagicMock()
    mock_doc_ref.id = "generated-doc-id"
    mock_doc_ref.set = AsyncMock()

    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection

    with patch("services.firestore_service._db", mock_db):
        from services.firestore_service import save_itinerary  # type: ignore[import]

        result = await save_itinerary(
            user_id="user-456",
            itinerary=FAKE_ITINERARY_DATA,
        )

    assert isinstance(result, str)
    assert result == "generated-doc-id"


# ===========================================================================
# 10. services/maps_service.py — geocode_location returns dict with lat/lng
# ===========================================================================


@pytest.mark.asyncio
async def test_maps_geocode_location_returns_lat_lng():
    """Mock googlemaps.Client; verify geocode_location returns lat and lng."""
    fake_geocode_result = [
        {
            "geometry": {
                "location": {"lat": 48.8566, "lng": 2.3522}
            }
        }
    ]

    mock_gmaps_client = MagicMock()
    mock_gmaps_client.geocode = MagicMock(return_value=fake_geocode_result)

    with patch("core.secrets.get_secret", return_value="fake-api-key"), patch(
        "googlemaps.Client", return_value=mock_gmaps_client
    ):
        from services.maps_service import geocode_location  # type: ignore[import]

        result = await geocode_location("Paris, France")

    assert "lat" in result
    assert "lng" in result
    assert result["lat"] == pytest.approx(48.8566)
    assert result["lng"] == pytest.approx(2.3522)


# ===========================================================================
# Extra: POST /plan — firestore save raises -> 500
# ===========================================================================


@pytest.mark.asyncio
async def test_plan_firestore_error_returns_500():
    """When save_itinerary raises, the endpoint must return 500."""
    with patch(
        "services.gemini_service.generate_itinerary",
        new=AsyncMock(return_value=FAKE_ITINERARY_DATA),
    ), patch(
        "services.firestore_service.save_itinerary",
        new=AsyncMock(side_effect=RuntimeError("Firestore unavailable")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/plan", json=PLAN_REQUEST_PAYLOAD)

    assert response.status_code == 500
