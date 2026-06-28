# Project Overview

## Goal
Build a RAG (Retrieval-Augmented Generation) pipeline with hybrid search over internal documentation.

## Guiding principle
Build in phases — do not implement ahead of the current phase. Each phase should be independently usable before the next starts.

## Tech stack (decided so far)
| Layer | Choice | Status |
|-------|--------|--------|
| Frontend | React + Vite | Phase 1 done |
| Backend | Python / FastAPI | Phase 2 done |
| Parsing | pdfplumber, beautifulsoup4, markdown | Phase 2 done |
| Embeddings | TBD | Not started |
| Vector store | TBD (hybrid = dense + BM25) | Not started |

## Phase roadmap
| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Document upload UI | ✅ Complete |
| 2 | FastAPI backend — normalize uploaded files to plain text | ✅ Complete |
| 3 | Chunking + embedding generation | Not started |
| 4 | Hybrid search (dense + sparse) | Not started |
| 5 | Query / chat UI | Not started |

## Project root
`/Users/jayanthbalu/Documents/personal_projects/AiEngineerProjects/`
