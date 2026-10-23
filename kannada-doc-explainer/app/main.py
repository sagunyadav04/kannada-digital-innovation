import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing application modules.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db, explain, llm, ocr

log = logging.getLogger("uvicorn.error")

STATIC = Path(__file__).parent / "static"
MAX_BYTES = int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024

app = FastAPI(title="Kannada Document Explainer")


@app.get("/api/health")
def health():
    return {"ok": True, "ai": llm.available()}


@app.post("/api/process")
def process(
    file: UploadFile = File(...),
    save: bool = Form(False),
    x_client_id: str = Header(default=""),
):
    data = file.file.read(MAX_BYTES + 1)

    if len(data) > MAX_BYTES:
        raise HTTPException(
            413,
            f"File is larger than {MAX_BYTES // 1048576} MB."
        )

    if not (
        data[:4] == b"%PDF"
        or data[:3] == b"\xff\xd8\xff"
        or data[:8] == b"\x89PNG\r\n\x1a\n"
        or data[:4] == b"RIFF"
    ):
        raise HTTPException(
            415,
            "Upload a JPG, PNG, WebP or PDF file."
        )

    try:
        pages = ocr.to_images(data)
    except Exception as e:
        log.warning("Could not read upload: %s", e)
        raise HTTPException(
            400,
            "Could not open this file. Try a clearer photo or a different PDF."
        )

    engine, ai, text = "tesseract", None, ""

    # Try Gemini first.
    if llm.available():
        try:
            ai = llm.analyze(pages)
            text = ai["text"]
            engine = "gemini"
        except Exception as e:
            log.exception("Gemini failed; falling back to Tesseract")

    # Use Tesseract if Gemini did not provide text.
    if not text:
        try:
            text = ocr.tesseract_text(pages)
        except Exception as e:
            log.exception("Tesseract OCR failed")
            raise HTTPException(
                status_code=500,
                detail=f"Text recognition failed: {str(e)}"
            )

    # Convert a list of OCR results into one string.
    if isinstance(text, list):
        text = "\n".join(str(item) for item in text)

    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    if not text.strip():
        raise HTTPException(
            422,
            "No text found. Try a sharper, well-lit photo with the page filling the frame."
        )

    explanation = explain.merge(explain.analyze(text), ai)

    result = {
        "text": text,
        "engine": engine,
        "explanation": explanation,
        "id": None,
    }

    if save and x_client_id:
        result["id"] = db.save(
            x_client_id,
            file.filename,
            engine,
            explanation["doc_type"],
            text,
            explanation,
        )

    return result


@app.get("/api/documents")
def list_documents(
    q: str = "",
    x_client_id: str = Header(default=""),
):
    return db.search(x_client_id, q) if x_client_id else []


class SaveBody(BaseModel):
    filename: str = "Document"
    engine: str = "tesseract"
    text: str
    explanation: dict


@app.post("/api/documents")
def save_document(body: SaveBody, x_client_id: str = Header(default="")):
    """Save a document that was already scanned (used when 'Save' is ticked after the scan)."""
    if not x_client_id:
        raise HTTPException(400, "Missing client id.")
    doc_id = db.save(
        x_client_id,
        body.filename,
        body.engine,
        str(body.explanation.get("doc_type", "document")),
        body.text,
        body.explanation,
    )
    return {"id": doc_id}


@app.get("/api/documents/{doc_id}")
def get_document(
    doc_id: str,
    x_client_id: str = Header(default=""),
):
    doc = db.get(x_client_id, doc_id)

    if not doc:
        raise HTTPException(404, "Document not found.")

    return doc


@app.delete("/api/documents/{doc_id}")
def delete_document(
    doc_id: str,
    x_client_id: str = Header(default=""),
):
    db.delete(x_client_id, doc_id)
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")