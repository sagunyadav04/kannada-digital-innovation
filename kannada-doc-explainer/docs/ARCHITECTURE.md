# Architecture

```mermaid
flowchart LR
  U[User: photo / PDF] --> FE[Web UI<br/>HTML + JS]
  FE -->|POST /api/process| API[FastAPI]
  API --> L[Loader<br/>Pillow / pdf2image]
  L --> G{Gemini key?}
  G -->|yes| LLM[Gemini vision<br/>OCR + explain + translate]
  G -->|no / error| T[Tesseract kan+eng]
  LLM --> R[Rules layer<br/>digits, dates, amounts,<br/>doc type, glossary]
  T --> R
  R --> API
  API -->|text + explanation JSON| FE
  API -.optional save.-> DB[(SQLite<br/>library + search)]
  FE --> TTS[Browser speech<br/>kn-IN read aloud]
```

Key design decisions
- Two engines behind one endpoint: AI for quality, Tesseract so the product never fully fails.
- The rules layer runs on every result, so dates, amounts and the glossary are deterministic and testable.
- Privacy by default: nothing is stored unless the user opts in.
