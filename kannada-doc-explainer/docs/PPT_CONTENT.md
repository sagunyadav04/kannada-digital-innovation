# PPT content (one section per slide; add 1 title slide)

**1. Problem Statement**
- Kannada Text Digitization: turn Kannada images/scans/handwriting into searchable, understandable text.
- Who: migrants, newcomers, elderly and low-literacy residents facing Kannada bills, land records, rental agreements, notices.
- Why it matters: missed deadlines, penalties, signing things they don't understand.

**2. Existing System**
- Google Lens / Translate: translates words, doesn't say what the document is or what to do; weak on Kannada layout.
- Plain OCR tools: output raw text, often garbled for Kannada, no explanation, no search.
- Asking a neighbour or agent: slow, costs money, privacy risk.

**3. How Our Solution Is Different**
- Digitizes AND explains: doc type, summary, action items, key facts, glossary.
- Works offline-capable (Tesseract fallback) and degrades gracefully.
- Kannada-specific rules: Kannada numerals, Indian amount formats, official-term glossary highlighting source text.
- Searchable private library; read-aloud.

**4. Approach**
- Upload → page images → AI vision reads the page (fallback: preprocessed Tesseract) → rules layer extracts facts → explanation UI.
- Design decision: glossary hover highlights the original word so users learn Kannada while they get help.
- Different from the usual: not "OCR then dump text", but "understand the document and tell me what to do".

**5. Tech Stack & Architecture Diagram**
- FastAPI, Gemini, Tesseract (kan), Pillow/pdf2image, SQLite, vanilla JS, Docker, Render.
- Insert diagram from docs/ARCHITECTURE.md (render the mermaid at mermaid.live and paste the image).

**6. Conclusion**
- Summary: a photo of a Kannada paper becomes plain English and a to-do list in seconds.
- Impact: fewer missed deadlines, more independence for non-Kannada readers.
- Future scope: more doc types, Hindi/Tamil/Telugu explanations, WhatsApp bot, on-device OCR, handwriting benchmarks.
