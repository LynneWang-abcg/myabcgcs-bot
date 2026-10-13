from dataclasses import dataclass
from html import unescape
from typing import Any

import httpx


MYMEMORY_URL = "https://api.mymemory.translated.net/get"


@dataclass(frozen=True)
class TranslationResult:
    text: str
    source_language: str


async def translate_to_simplified_chinese(
    text: str,
    *,
    client: Any | None = None,
    email: str | None = None,
) -> TranslationResult:
    params = {
        "q": text,
        "langpair": "auto|zh-CN",
    }
    if email:
        params["de"] = email

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient()

    try:
        response = await client.get(MYMEMORY_URL, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
    finally:
        if owns_client:
            await client.aclose()

    translated = payload.get("responseData", {}).get("translatedText")
    if not translated:
        raise RuntimeError("Translation service did not return translated text.")

    detected = payload.get("responseData", {}).get("detectedLanguage") or "auto"
    return TranslationResult(text=unescape(translated), source_language=detected)
