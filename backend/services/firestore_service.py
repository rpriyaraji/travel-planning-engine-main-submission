"""Firestore service for persisting and retrieving travel itineraries."""

from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

# Async Firestore client — created once at module level.
_db: firestore.AsyncClient = firestore.AsyncClient()

_COLLECTION: str = "itineraries"


async def save_itinerary(user_id: str, itinerary: dict[str, Any]) -> str:
    """Persist a travel itinerary document to Firestore.

    The document is stored in the ``itineraries`` collection. A ``user_id``
    field and a ``created_at`` timestamp are automatically added.

    Args:
        user_id: Unique identifier for the user who owns this itinerary.
        itinerary: Dict containing the itinerary data to store.

    Returns:
        The auto-generated Firestore document ID.

    Raises:
        RuntimeError: If the write operation fails for any reason.
    """
    try:
        doc_ref: firestore.AsyncDocumentReference = _db.collection(_COLLECTION).document()
        payload: dict[str, Any] = {
            **itinerary,
            "user_id": user_id,
            "created_at": datetime.now(tz=timezone.utc),
        }
        await doc_ref.set(payload)
        return doc_ref.id
    except Exception as exc:
        raise RuntimeError(
            f"Failed to save itinerary for user '{user_id}': {exc}"
        ) from exc


async def get_user_itineraries(user_id: str) -> list[dict[str, Any]]:
    """Retrieve all itineraries that belong to a specific user.

    Args:
        user_id: The user whose itineraries should be fetched.

    Returns:
        List of itinerary dicts. Each dict includes a ``id`` key containing
        the Firestore document ID. Returns an empty list if none are found.

    Raises:
        RuntimeError: If the query fails for any reason.
    """
    try:
        query = _db.collection(_COLLECTION).where("user_id", "==", user_id)
        docs = query.stream()
        results: list[dict[str, Any]] = []
        async for doc in docs:
            data: dict[str, Any] = doc.to_dict()
            data["id"] = doc.id
            if "created_at" in data and not isinstance(data["created_at"], str):
                data["created_at"] = str(data["created_at"])
            results.append(data)
        return results
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch itineraries for user '{user_id}': {exc}"
        ) from exc


# Alias used by main.py's lazy import
get_itineraries_for_user = get_user_itineraries


async def get_itinerary(itinerary_id: str) -> dict[str, Any] | None:
    """Retrieve a single itinerary document by its Firestore document ID.

    Args:
        itinerary_id: The Firestore document ID of the itinerary.

    Returns:
        The itinerary dict (including an ``id`` key) if the document exists,
        or ``None`` if it does not.

    Raises:
        RuntimeError: If the read operation fails for any reason.
    """
    try:
        doc_ref: firestore.AsyncDocumentReference = (
            _db.collection(_COLLECTION).document(itinerary_id)
        )
        doc = await doc_ref.get()
        if not doc.exists:
            return None
        data: dict[str, Any] = doc.to_dict()
        data["id"] = doc.id
        if "created_at" in data and not isinstance(data["created_at"], str):
            data["created_at"] = str(data["created_at"])
        return data
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch itinerary '{itinerary_id}': {exc}"
        ) from exc
