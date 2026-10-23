# Video script (voice-over, ~4:30). Screen-record at 1080p; practise once.

**0:00-0:45 Problem and requirements**
"The challenge: Kannada Text Digitization. Build a solution that converts Kannada text from images, scans or handwriting into searchable digital text, and makes it easier to understand. I picked a real pain point: people who live in Karnataka but can't read Kannada, and get bills, land records and notices in it."

**0:45-1:30 Existing system and gaps**
"Today they use Google Lens or a plain OCR tool. Those give raw or translated words, but don't tell you what the document is, what the deadline is, or what to do. Kannada OCR is also often inaccurate."

**1:30-3:30 Live demo** (have a sample electricity bill photo ready)
1. Drop the photo. Show the loading state.
2. Left pane: extracted Kannada text. Search a word. 
3. Right pane: document type, summary, what to do, key facts.
4. Hover a glossary word: it highlights in the original text.
5. Full translation tab; Read aloud; download .txt.
6. Tick Save, open My library, search a Kannada word.
"If the AI is unavailable, it falls back to Tesseract and the rules layer, so it still extracts text, dates, amounts and the glossary."

**3:30-4:30 Tech stack and architecture**
Walk the diagram: UI → FastAPI → Gemini vision or Tesseract → rules layer → JSON → UI; SQLite for the optional library; Docker on Render.

**4:30-5:00 Conclusion**
"A photo becomes plain English and a to-do list in seconds. Next: more document types, more languages, and a WhatsApp bot. Thank you."
