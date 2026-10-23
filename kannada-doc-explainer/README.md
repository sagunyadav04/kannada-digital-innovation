# Kannada Document Explainer

**Kannada Technology Challenge – Problem Statement 05: Kannada Text Digitization**

Many people who live in Karnataka cannot read Kannada, yet electricity bills, land records (RTC/Pahani), rental agreements and government notices arrive in it. This app turns a photo or PDF of a Kannada document into **searchable digital text** and **explains it in plain English**: what the document is, what you need to do, the key dates and amounts, and the meaning of the Kannada words in it.

Live demo: `<your deployed URL here>`

## Features
- Upload or photograph a Kannada document (JPG, PNG, WebP, PDF).
- Text extraction: Gemini vision (handles phone photos and handwriting) with an **offline Tesseract (kan+eng) fallback**, so it still works without an API key.
- Plain-English explanation: document type, summary, action items, key facts, full English translation (AI mode).
- Rule-based layer that always runs: Kannada digit conversion (೧೨೩ → 123), date and amount extraction, document-type detection, and a Kannada→English glossary of ~45 official-document terms.
- Words in the glossary highlight where they appear in the original text.
- Find-in-document, copy, download as .txt, and read aloud (browser Kannada voice, if installed).
- Optional private library: save documents and search them in Kannada or English. Documents are saved only if you tick the box, and are tied to a random ID kept in your browser.

## Tech stack
FastAPI (Python 3.11) · Tesseract OCR + pdf2image/Poppler · Google Gemini (optional) · SQLite · plain HTML/CSS/JS frontend · Docker.

## Run locally
```bash
git clone <this repo> && cd kannada-doc-explainer
cp .env.example .env            # optionally add GEMINI_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# for offline OCR (Ubuntu/Debian):
sudo apt install tesseract-ocr tesseract-ocr-kan poppler-utils
uvicorn app.main:app --reload   # open http://localhost:8000
```
Or with Docker: `docker build -t kde . && docker run -p 8000:8000 --env-file .env kde`

Tests: `pytest`

## Deploy
See [docs/DEPLOY.md](docs/DEPLOY.md). No login is needed, so there are no test credentials.

## Limits and honesty
OCR can misread blurry photos; the UI tells users to verify important numbers. The explanation is a reading aid, not legal advice.

## Docs
[Architecture](docs/ARCHITECTURE.md) · [PPT content](docs/PPT_CONTENT.md) · [Video script](docs/VIDEO_SCRIPT.md)
