"""Tiny SQLite library so users can save and search their digitized documents."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _db_path():
    return os.getenv("DB_PATH", "data/docs.db")


def _conn():
    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS docs (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            filename TEXT,
            created TEXT,
            engine TEXT,
            doc_type TEXT,
            text TEXT,
            explanation TEXT
        )"""
    )
    return conn


def save(client_id, filename, engine, doc_type, text, explanation):
    doc_id = uuid.uuid4().hex[:12]
    conn = _conn()
    with conn:
        conn.execute(
            "INSERT INTO docs VALUES (?,?,?,?,?,?,?,?)",
            (doc_id, client_id, filename, datetime.now(timezone.utc).isoformat(),
             engine, doc_type, text, json.dumps(explanation, ensure_ascii=False)),
        )
    conn.close()
    return doc_id


def _snippet(text, q, width=60):
    i = text.lower().find(q.lower()) if q else -1
    if i < 0:
        return text[: width * 2].replace("\n", " ")
    return text[max(0, i - width): i + len(q) + width].replace("\n", " ")


def search(client_id, q=""):
    q = (q or "").strip()
    conn = _conn()
    if q:
        rows = conn.execute(
            "SELECT * FROM docs WHERE client_id=? AND (text LIKE ? OR filename LIKE ?) "
            "ORDER BY created DESC LIMIT 50",
            (client_id, f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM docs WHERE client_id=? ORDER BY created DESC LIMIT 50", (client_id,)
        ).fetchall()
    conn.close()
    return [
        {"id": r["id"], "filename": r["filename"], "created": r["created"],
         "doc_type": r["doc_type"], "snippet": _snippet(r["text"], q)}
        for r in rows
    ]


def get(client_id, doc_id):
    conn = _conn()
    r = conn.execute("SELECT * FROM docs WHERE id=? AND client_id=?", (doc_id, client_id)).fetchone()
    conn.close()
    if not r:
        return None
    return {"id": r["id"], "filename": r["filename"], "engine": r["engine"],
            "text": r["text"], "explanation": json.loads(r["explanation"])}


def delete(client_id, doc_id):
    conn = _conn()
    with conn:
        conn.execute("DELETE FROM docs WHERE id=? AND client_id=?", (doc_id, client_id))
    conn.close()
