"""Google Maps service for geocoding, nearby places, distance matrix, and directions."""

import asyncio
from typing import Any

import googlemaps

from core.secrets import get_secret


def _get_client() -> googlemaps.Client:
    """Instantiate a Google Maps client using the secret API key.

    Returns:
        An authenticated googlemaps.Client instance.

    Raises:
        RuntimeError: If the API key cannot be fetched.
    """
    api_key: str = get_secret("MAPS_API_KEY")
    return googlemaps.Client(key=api_key)


async def geocode_location(address: str) -> dict[str, float]:
    """Convert a human-readable address to geographic coordinates.

    Args:
        address: The address or place name to geocode.

    Returns:
        Dict with keys ``lat`` and ``lng`` (both float).

    Raises:
        ValueError: If no geocoding results are returned.
        RuntimeError: If the API call fails for any reason.
    """
    try:
        client: googlemaps.Client = _get_client()
        results: list[dict[str, Any]] = await asyncio.to_thread(
            client.geocode, address
        )
        if not results:
            raise ValueError(f"No geocoding results found for address: '{address}'")
        location: dict[str, float] = results[0]["geometry"]["location"]
        return {"lat": location["lat"], "lng": location["lng"]}
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Geocoding failed for '{address}': {exc}") from exc


async def get_nearby_places(
    lat: float,
    lng: float,
    place_type: str = "tourist_attraction",
    radius: int = 5000,
) -> list[dict[str, Any]]:
    """Find places of a given type near a set of coordinates.

    Args:
        lat: Latitude of the search centre.
        lng: Longitude of the search centre.
        place_type: Google Places type string (default: tourist_attraction).
        radius: Search radius in metres (default: 5000).

    Returns:
        List of place dicts, each containing at minimum:
        ``name``, ``place_id``, ``vicinity``, ``rating``, ``lat``, ``lng``.

    Raises:
        RuntimeError: If the API call fails for any reason.
    """
    try:
        client: googlemaps.Client = _get_client()
        response: dict[str, Any] = await asyncio.to_thread(
            client.places_nearby,
            location=(lat, lng),
            radius=radius,
            type=place_type,
        )
        results: list[dict[str, Any]] = response.get("results", [])
        places: list[dict[str, Any]] = []
        for place in results:
            geo: dict[str, float] = place.get("geometry", {}).get("location", {})
            places.append(
                {
                    "name": place.get("name", ""),
                    "place_id": place.get("place_id", ""),
                    "vicinity": place.get("vicinity", ""),
                    "rating": place.get("rating"),
                    "lat": geo.get("lat"),
                    "lng": geo.get("lng"),
                }
            )
        return places
    except Exception as exc:
        raise RuntimeError(
            f"Nearby places search failed (lat={lat}, lng={lng}, type={place_type}): {exc}"
        ) from exc


async def get_distance_matrix(
    origins: list[str],
    destinations: list[str],
) -> dict[str, Any]:
    """Calculate travel distances and times between multiple origins and destinations.

    Args:
        origins: List of origin addresses or place names.
        destinations: List of destination addresses or place names.

    Returns:
        The raw Distance Matrix API response dict, including
        ``origin_addresses``, ``destination_addresses``, and ``rows``.

    Raises:
        RuntimeError: If the API call fails for any reason.
    """
    try:
        client: googlemaps.Client = _get_client()
        result: dict[str, Any] = await asyncio.to_thread(
            client.distance_matrix,
            origins,
            destinations,
        )
        return result
    except Exception as exc:
        raise RuntimeError(
            f"Distance matrix request failed (origins={origins}, destinations={destinations}): {exc}"
        ) from exc


async def get_directions(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> dict[str, Any]:
    """Retrieve turn-by-turn directions between two locations.

    Args:
        origin: Starting address or place name.
        destination: Ending address or place name.
        mode: Travel mode — one of ``driving``, ``walking``, ``bicycling``,
            ``transit`` (default: driving).

    Returns:
        Dict with keys ``summary``, ``distance``, ``duration``, and ``steps``
        (list of step dicts with ``instructions`` and ``distance``).

    Raises:
        ValueError: If no directions are returned.
        RuntimeError: If the API call fails for any reason.
    """
    try:
        client: googlemaps.Client = _get_client()
        results: list[dict[str, Any]] = await asyncio.to_thread(
            client.directions,
            origin,
            destination,
            mode=mode,
        )
        if not results:
            raise ValueError(
                f"No directions found from '{origin}' to '{destination}' via {mode}."
            )
        route: dict[str, Any] = results[0]
        leg: dict[str, Any] = route["legs"][0]
        steps: list[dict[str, Any]] = [
            {
                "instructions": step.get("html_instructions", ""),
                "distance": step.get("distance", {}).get("text", ""),
            }
            for step in leg.get("steps", [])
        ]
        return {
            "summary": route.get("summary", ""),
            "distance": leg.get("distance", {}).get("text", ""),
            "duration": leg.get("duration", {}).get("text", ""),
            "steps": steps,
        }
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Directions request failed ('{origin}' -> '{destination}', mode={mode}): {exc}"
        ) from exc
