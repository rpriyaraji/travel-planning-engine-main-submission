"""Translation service using Google Cloud Translation API v2 (Basic)."""

import asyncio

from google.cloud import translate_v2 as translate

from core.secrets import get_secret


def _get_client() -> translate.Client:
    """Instantiate a Translation v2 client using the secret API key.

    Returns:
        An authenticated google.cloud.translate_v2.Client instance.

    Raises:
        RuntimeError: If the API key cannot be fetched.
    """
    api_key: str = get_secret("TRANSLATION_API_KEY")
    return translate.Client(client_options={"api_key": api_key})


async def detect_language(text: str) -> str:
    """Detect the language of the provided text.

    Args:
        text: The text whose language should be detected.

    Returns:
        BCP-47 language code string (e.g. ``"en"``, ``"fr"``, ``"ja"``).

    Raises:
        RuntimeError: If the API call fails for any reason.
    """
    try:
        client: translate.Client = _get_client()
        result: dict = await asyncio.to_thread(client.detect_language, text)
        language_code: str = result["language"]
        return language_code
    except Exception as exc:
        raise RuntimeError(f"Language detection failed for text '{text[:50]}...': {exc}") from exc


async def translate_text(
    text: str,
    target_language: str = "en",
) -> str:
    """Translate text into the specified target language.

    Args:
        text: The source text to translate.
        target_language: BCP-47 code of the target language (default: ``"en"``).

    Returns:
        The translated text as a plain string.

    Raises:
        RuntimeError: If the API call fails for any reason.
    """
    try:
        client: translate.Client = _get_client()
        result: dict = await asyncio.to_thread(
            client.translate,
            text,
            target_language=target_language,
        )
        translated: str = result["translatedText"]
        return translated
    except Exception as exc:
        raise RuntimeError(
            f"Translation to '{target_language}' failed for text '{text[:50]}...': {exc}"
        ) from exc
