# Phase 1 — Document Upload UI

**Status**: Complete  
**Location**: `doc-upload-ui/` (Vite + React, no component library)

## What was built
A standalone React frontend for selecting documents to upload into the knowledge base.

## Key files
| File | Purpose |
|------|---------|
| `src/App.jsx` | All upload logic and UI |
| `src/App.css` | Dark-themed component styles |
| `src/index.css` | Minimal global reset |

## Features
- Drag-and-drop zone with visual drag state
- Click-to-browse via hidden `<input type="file">`
- Accepted formats: `.md`, `.txt`, `.html`, `.htm`, `.pdf`
- File type validation — rejects unsupported types with inline error
- Duplicate filename detection
- File list: icon (by type), name, size, extension
- Per-file remove + "Clear all"
- "Upload N documents" button — **stub only, no backend wired**

## What's intentionally missing
- No actual upload/HTTP call — the button is a placeholder
- No backend, no file storage, no parsing

## Next step
Phase 2 will add a FastAPI backend. The upload button should POST files to an endpoint (e.g. `POST /documents`) and the UI should show upload progress/status.
