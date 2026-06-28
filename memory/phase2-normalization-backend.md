# Phase 2 — Document Normalization Backend

**Status**: Complete  
**Location**: `backend/` (FastAPI + Python)

## What was built
A FastAPI backend that receives uploaded files and normalizes them to plain text.

## Key files
| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, CORS, `POST /documents` endpoint |
| `backend/normalizer.py` | Type-specific text extraction logic |
| `backend/requirements.txt` | Python dependencies |

## Endpoint
`POST /documents` — multipart form upload, returns JSON:
```json
{
  "documents": [
    { "filename": "report.pdf", "char_count": 4200, "word_count": 700, "text": "..." }
  ]
}
```

## Normalization strategy per type
| Extension | Library | Approach |
|-----------|---------|----------|
| `.txt` | built-in | Decode UTF-8, strip whitespace |
| `.md` | `markdown` + `beautifulsoup4` | Convert MD → HTML → strip tags |
| `.html` / `.htm` | `beautifulsoup4` + `lxml` | Strip `<script>`, `<style>`, `<head>` then `get_text()` |
| `.pdf` | `pdfplumber` | Extract text per page, join with double newline |

## CORS
Allows `http://localhost:5173` (Vite dev server). Needs updating when deploying.

## Frontend wiring (in phase 1's App.jsx)
- Upload button POSTs to `http://localhost:8000/documents`
- Shows loading state during processing
- Displays normalized text preview (first 400 chars), word count, char count per file
- Clears file list on success

## How to run
```bash
cd backend
pip3 install -r requirements.txt
python3 -m uvicorn main:app --port 8000
```

## What's next (Phase 3)
Chunking the normalized text and generating embeddings. Decisions needed:
- Chunk size / overlap strategy
- Embedding model choice
- Vector store selection (hybrid = dense + BM25)
