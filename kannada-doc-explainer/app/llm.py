"""Optional Gemini path: reads the page image directly (best for photos and handwriting)."""
import json
import os

from .ocr import to_jpeg_bytes

PROMPT = """You are helping a person who cannot read Kannada understand an official document.
Look at the attached page image(s) and return ONLY a JSON object with these keys:
- "text": the exact Kannada (and English) text as written, line by line. Do not translate or correct it.
  Mark words you cannot read with [?].
- "doc_type": one of electricity_bill, land_record, rental_agreement, legal_notice, tax, certificate, other
- "summary": 2-3 plain English sentences: what this document is and what it wants from the reader.
- "key_facts": list of {"label": str, "value": str} (names, amounts, dates, account/meter/survey numbers, authority).
- "action_items": list of short English sentences: what the reader must do, and by when.
- "translation_en": a faithful English translation of the full text.
Never invent facts that are not on the page."""


def available() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def analyze(pages) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    parts = [types.Part.from_bytes(data=to_jpeg_bytes(p), mime_type="image/jpeg") for p in pages]
    resp = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=parts + [PROMPT],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    data = json.loads(resp.text)
    if not isinstance(data, dict) or not data.get("text"):
        raise ValueError("Gemini returned no text")
    return data
