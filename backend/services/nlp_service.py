"""Natural Language Processing service using Google Cloud Natural Language API v2."""

import asyncio
from typing import Any

from google.cloud import language_v2

# Module-level client — created once and reused across all calls.
_nlp_client: language_v2.LanguageServiceAsyncClient = (
    language_v2.LanguageServiceAsyncClient()
)


async def analyze_sentiment(text: str) -> dict[str, Any]:
    """Analyse the overall sentiment of a piece of text.

    Args:
        text: The plain-text content to analyse.

    Returns:
        Dict with keys:
          - score (float): Sentiment score in [-1.0, 1.0].
          - magnitude (float): Strength of sentiment (non-negative).
          - label (str): Human-readable label — ``positive``, ``negative``,
            or ``neutral``.

    Raises:
        RuntimeError: If the API call fails for any reason.
    """
    try:
        document = language_v2.Document(
            content=text,
            type_=language_v2.Document.Type.PLAIN_TEXT,
        )
        response = await _nlp_client.analyze_sentiment(
            request={"document": document}
        )
        score: float = response.document_sentiment.score
        magnitude: float = response.document_sentiment.magnitude

        if score >= 0.25:
            label = "positive"
        elif score <= -0.25:
            label = "negative"
        else:
            label = "neutral"

        return {"score": score, "magnitude": magnitude, "label": label}
    except Exception as exc:
        raise RuntimeError(f"Sentiment analysis failed: {exc}") from exc


async def extract_entities(text: str) -> list[dict[str, Any]]:
    """Extract named entities from a piece of text.

    Args:
        text: The plain-text content to analyse.

    Returns:
        List of entity dicts, each with keys:
          - name (str): The entity surface form.
          - type (str): Entity type label (e.g. LOCATION, PERSON, EVENT).
          - salience (float): Importance score in [0.0, 1.0].

    Raises:
        RuntimeError: If the API call fails for any reason.
    """
    try:
        document = language_v2.Document(
            content=text,
            type_=language_v2.Document.Type.PLAIN_TEXT,
        )
        response = await _nlp_client.analyze_entities(
            request={"document": document}
        )
        entities: list[dict[str, Any]] = [
            {
                "name": entity.name,
                "type": language_v2.Entity.Type(entity.type_).name,
                "salience": entity.salience,
            }
            for entity in response.entities
        ]
        return entities
    except Exception as exc:
        raise RuntimeError(f"Entity extraction failed: {exc}") from exc
