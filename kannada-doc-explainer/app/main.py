import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from . import db, explain, llm, ocr  # noqa: E402

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
        raise HTTPException(413, f"File is larger than {MAX_BYTES // 1048576} MB.")
    if not (data[:4] == b"%PDF" or data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n"
            or data[:4] == b"RIFF"):
        raise HTTPException(415, "Upload a JPG, PNG, WebP or PDF file.")

    try:
        pages = ocr.to_images(data)
    except Exception as e:  # corrupt image, missing poppler, etc.
        log.warning("could not read upload: %s", e)
        raise HTTPException(400, "Could not open this file. Try a clearer photo or a different PDF.")

    engine, ai, text = "tesseract", None, ""
    if llm.available():
        try:
            ai = llm.analyze(pages)
            text, engine = ai["text"], "gemini"
        except Exception as e:
            log.warning("Gemini failed, falling back to Tesseract: %s", e)
    if not text:
        try:
            text = ocr.tesseract_text(pages)
        except Exception as e:
            log.warning("tesseract failed: %s", e)
            raise HTTPException(500, "Text recognition is unavailable on the server.")
    if not text.strip():
        raise HTTPException(422, "No text found. Try a sharper, well-lit photo with the page filling the frame.")

    explanation = explain.merge(explain.analyze(text), ai)
    result = {"text": text, "engine": engine, "explanation": explanation, "id": None}
    if save and x_client_id:
        result["id"] = db.save(x_client_id, file.filename, engine, explanation["doc_type"], text, explanation)
    return result


@app.get("/api/documents")
def list_documents(q: str = "", x_client_id: str = Header(default="")):
    return db.search(x_client_id, q) if x_client_id else []


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str, x_client_id: str = Header(default="")):
    doc = db.get(x_client_id, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    return doc


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, x_client_id: str = Header(default="")):
    db.delete(x_client_id, doc_id)
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
