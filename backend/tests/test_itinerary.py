"""
Tests for the Travel Planner FastAPI backend.

All Google Cloud clients are mocked so no real network calls are made.
"""

import sys
import os
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — repo root must be on sys.path so that 'backend.*' resolves.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ---------------------------------------------------------------------------
# Stub out heavy Google Cloud libraries BEFORE anything imports them.
# ---------------------------------------------------------------------------

def _make_stub(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


_mock_async_client_instance = MagicMock()
_mock_firestore_mod = _make_stub(
    "google.cloud.firestore",
    AsyncClient=MagicMock(return_value=_mock_async_client_instance),
    AsyncDocumentReference=MagicMock,
)
_mock_secretmanager_mod = _make_stub(
    "google.cloud.secretmanager",
    SecretManagerServiceClient=MagicMock(),
)
_mock_vertexai_mod = _make_stub("vertexai", init=MagicMock())
_mock_gen_model_cls = MagicMock()
_mock_vertexai_gen_mod = _make_stub(
    "vertexai.generative_models",
    GenerativeModel=_mock_gen_model_cls,
)
_mock_lang_async_client = MagicMock()
_mock_lang_mod = _make_stub(
    "google.cloud.language_v2",
    LanguageServiceAsyncClient=MagicMock(return_value=_mock_lang_async_client),
    Document=MagicMock(),
    Entity=MagicMock(),
)
_mock_translate_mod = _make_stub("google.cloud.translate_v2", Client=MagicMock())
_mock_gmaps_mod = _make_stub("googlemaps", Client=MagicMock())

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

sys.modules["google"].cloud = sys.modules["google.cloud"]  # type: ignore[attr-defined]

# Safe to import application modules now.
import httpx
from httpx import AsyncClient, ASGITransport

from backend.main import app  # type: ignore[import]


# ---------------------------------------------------------------------------
# Shared fixtures / payloads
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

async def test_health_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200


async def test_health_returns_correct_body():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "travel-planner"


# ===========================================================================
# 2. POST /plan — success path
# ===========================================================================

async def test_plan_success():
    with patch("backend.services.gemini_service.generate_itinerary",
               new=AsyncMock(return_value=FAKE_ITINERARY_DATA)), \
         patch("backend.services.firestore_service.save_itinerary",
               new=AsyncMock(return_value="doc-abc-123")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/plan", json=PLAN_REQUEST_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["itinerary_id"] == "doc-abc-123"
    assert body["status"] == "success"
    assert "message" in body


async def test_plan_response_shape():
    with patch("backend.services.gemini_service.generate_itinerary",
               new=AsyncMock(return_value=FAKE_ITINERARY_DATA)), \
         patch("backend.services.firestore_service.save_itinerary",
               new=AsyncMock(return_value="some-id")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/plan", json=PLAN_REQUEST_PAYLOAD)

    body = response.json()
    assert set(body.keys()) >= {"itinerary_id", "status", "message"}


# ===========================================================================
# 3. POST /plan — error paths
# ===========================================================================

async def test_plan_gemini_error_returns_500():
    with patch("backend.services.gemini_service.generate_itinerary",
               new=AsyncMock(side_effect=RuntimeError("Vertex AI unavailable"))), \
         patch("backend.services.firestore_service.save_itinerary",
               new=AsyncMock(return_value="will-not-be-called")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/plan", json=PLAN_REQUEST_PAYLOAD)

    assert response.status_code == 500
    assert "Failed to generate itinerary" in response.json()["detail"]


async def test_plan_firestore_error_returns_500():
    with patch("backend.services.gemini_service.generate_itinerary",
               new=AsyncMock(return_value=FAKE_ITINERARY_DATA)), \
         patch("backend.services.firestore_service.save_itinerary",
               new=AsyncMock(side_effect=RuntimeError("Firestore unavailable"))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/plan", json=PLAN_REQUEST_PAYLOAD)

    assert response.status_code == 500


# ===========================================================================
# 4. GET /itineraries/{user_id}
# ===========================================================================

async def test_get_itineraries_success():
    with patch("backend.services.firestore_service.get_itineraries_for_user",
               new=AsyncMock(return_value=[FAKE_SAVED_ITINERARY])):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/itineraries/user-123")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["id"] == "doc-abc-123"


async def test_get_itineraries_list_shape():
    with patch("backend.services.firestore_service.get_itineraries_for_user",
               new=AsyncMock(return_value=[FAKE_SAVED_ITINERARY])):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/itineraries/user-123")

    item = response.json()[0]
    assert set(item.keys()) >= {"id", "user_id", "destination", "days", "created_at"}


async def test_get_itineraries_empty():
    with patch("backend.services.firestore_service.get_itineraries_for_user",
               new=AsyncMock(return_value=[])):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/itineraries/user-no-trips")

    assert response.status_code == 200
    assert response.json() == []


# ===========================================================================
# 5. core/secrets.py
# ===========================================================================

def test_get_secret_returns_decoded_string():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.payload.data = b"super-secret-value"
    mock_client.access_secret_version.return_value = mock_response

    with patch("google.cloud.secretmanager.SecretManagerServiceClient",
               return_value=mock_client):
        from backend.core.secrets import get_secret
        result = get_secret("MY_SECRET", project_id="test-project")

    assert result == "super-secret-value"


def test_get_secret_raises_runtime_error_on_failure():
    mock_client = MagicMock()
    mock_client.access_secret_version.side_effect = Exception("permission denied")

    with patch("google.cloud.secretmanager.SecretManagerServiceClient",
               return_value=mock_client):
        from backend.core.secrets import get_secret
        with pytest.raises(RuntimeError, match="Failed to fetch secret"):
            get_secret("MISSING_SECRET", project_id="test-project")


# ===========================================================================
# 6. services/gemini_service.py
# ===========================================================================

async def test_gemini_generate_itinerary_returns_days():
    import json as _json

    fake_text = _json.dumps(FAKE_ITINERARY_DATA)
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content_async = AsyncMock(
        return_value=MagicMock(text=fake_text)
    )

    with patch("backend.services.gemini_service.vertexai") as mock_vx, \
         patch("backend.services.gemini_service.GenerativeModel",
               return_value=mock_model_instance):
        mock_vx.init = MagicMock()
        from backend.services.gemini_service import generate_itinerary
        result = await generate_itinerary(
            preferences={"destination": "Paris", "duration_days": 3,
                         "interests": ["food"], "budget": "moderate"}
        )

    assert isinstance(result, dict)
    assert "days" in result
    assert len(result["days"]) >= 1


# ===========================================================================
# 7. services/firestore_service.py
# ===========================================================================

async def test_firestore_save_itinerary_returns_string_id():
    mock_doc_ref = MagicMock()
    mock_doc_ref.id = "generated-doc-id"
    mock_doc_ref.set = AsyncMock()

    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection

    with patch("backend.services.firestore_service._db", mock_db):
        from backend.services.firestore_service import save_itinerary
        result = await save_itinerary(user_id="user-456", itinerary=FAKE_ITINERARY_DATA)

    assert isinstance(result, str)
    assert result == "generated-doc-id"


# ===========================================================================
# 8. services/maps_service.py
# ===========================================================================

async def test_maps_geocode_location_returns_lat_lng():
    fake_geocode_result = [{"geometry": {"location": {"lat": 48.8566, "lng": 2.3522}}}]

    mock_gmaps_client = MagicMock()
    mock_gmaps_client.geocode = MagicMock(return_value=fake_geocode_result)

    with patch("backend.core.secrets.get_secret", return_value="fake-api-key"), \
         patch("googlemaps.Client", return_value=mock_gmaps_client):
        from backend.services.maps_service import geocode_location
        result = await geocode_location("Paris, France")

    assert "lat" in result
    assert "lng" in result
    assert result["lat"] == pytest.approx(48.8566)
    assert result["lng"] == pytest.approx(2.3522)


# ===========================================================================
# 9. services/nlp_service.py — sentiment analysis
# ===========================================================================

async def test_nlp_analyze_sentiment_positive():
    mock_sentiment = MagicMock()
    mock_sentiment.score = 0.8
    mock_sentiment.magnitude = 0.9

    mock_response = MagicMock()
    mock_response.document_sentiment = mock_sentiment

    mock_nlp_client = MagicMock()
    mock_nlp_client.analyze_sentiment = AsyncMock(return_value=mock_response)

    with patch("backend.services.nlp_service._nlp_client", mock_nlp_client):
        from backend.services.nlp_service import analyze_sentiment
        result = await analyze_sentiment("I love travelling to Paris!")

    assert result["label"] == "positive"
    assert result["score"] == pytest.approx(0.8)
    assert result["magnitude"] == pytest.approx(0.9)


async def test_nlp_analyze_sentiment_negative():
    mock_sentiment = MagicMock()
    mock_sentiment.score = -0.6
    mock_sentiment.magnitude = 0.7

    mock_response = MagicMock()
    mock_response.document_sentiment = mock_sentiment

    mock_nlp_client = MagicMock()
    mock_nlp_client.analyze_sentiment = AsyncMock(return_value=mock_response)

    with patch("backend.services.nlp_service._nlp_client", mock_nlp_client):
        from backend.services.nlp_service import analyze_sentiment
        result = await analyze_sentiment("Terrible weather ruined my trip.")

    assert result["label"] == "negative"


async def test_nlp_extract_entities_returns_list():
    mock_entity = MagicMock()
    mock_entity.name = "Paris"
    mock_entity.type_ = 2  # LOCATION
    mock_entity.salience = 0.95

    mock_response = MagicMock()
    mock_response.entities = [mock_entity]

    mock_nlp_client = MagicMock()
    mock_nlp_client.analyze_entities = AsyncMock(return_value=mock_response)

    with patch("backend.services.nlp_service._nlp_client", mock_nlp_client), \
         patch("google.cloud.language_v2.Entity.Type") as mock_type:
        mock_type.return_value.name = "LOCATION"
        from backend.services.nlp_service import extract_entities
        result = await extract_entities("I want to visit Paris in France.")

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "Paris"
    assert result[0]["salience"] == pytest.approx(0.95)


# ===========================================================================
# 10. services/translation_service.py
# ===========================================================================

async def test_translation_detect_language():
    mock_translate_client = MagicMock()
    mock_translate_client.detect_language = MagicMock(
        return_value={"language": "fr", "confidence": 0.99}
    )

    with patch("backend.core.secrets.get_secret", return_value="fake-key"), \
         patch("google.cloud.translate_v2.Client", return_value=mock_translate_client):
        from backend.services.translation_service import detect_language
        result = await detect_language("Bonjour le monde")

    assert result == "fr"


async def test_translation_translate_text():
    mock_translate_client = MagicMock()
    mock_translate_client.translate = MagicMock(
        return_value={"translatedText": "Hello world", "detectedSourceLanguage": "fr"}
    )

    with patch("backend.core.secrets.get_secret", return_value="fake-key"), \
         patch("google.cloud.translate_v2.Client", return_value=mock_translate_client):
        from backend.services.translation_service import translate_text
        result = await translate_text("Bonjour le monde", target_language="en")

    assert result == "Hello world"
