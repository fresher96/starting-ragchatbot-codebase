# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

**Do not run `bash run.sh` — the user always starts the app themselves.**

The start command (for reference only):
```bash
cd backend && uv run uvicorn app:app --reload --port 1234
```

The app serves at `http://localhost:1234`. FastAPI serves the frontend as static files from `../frontend` — there is no separate dev server.

To add a Python dependency:
```bash
uv add <package>
```

## Architecture

This is a RAG chatbot where a single FastAPI process (`backend/app.py`) both runs the API and serves the frontend as static files from `../frontend`.

**Request flow:**
1. User types a question → `frontend/script.js` POSTs to `/api/query`
2. `RAGSystem.query()` (`rag_system.py`) builds a prompt and calls `AIGenerator.generate_response()`
3. Claude decides whether to invoke the `search_course_content` tool (defined in `search_tools.py`)
4. If tool is called: `CourseSearchTool.execute()` queries ChromaDB via `VectorStore.search()`; results are returned to Claude for synthesis
5. Final answer + sources returned to frontend

**Key components:**
- `backend/config.py` — all tunable values in one place: model name, chunk size/overlap, max results, max history, ChromaDB path
- `backend/ai_generator.py` — wraps the Anthropic SDK; uses prompt caching (`cache_control: ephemeral`) on the system prompt and tool definitions; max 2 API calls per user turn (first call may trigger tool use, second call synthesizes the result)
- `backend/vector_store.py` — ChromaDB wrapper; persistent store at `backend/chroma_db/`; uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings
- `backend/document_processor.py` — parses `.txt` course files into `Course`/`Lesson`/`CourseChunk` models; chunks by sentence boundaries
- `backend/session_manager.py` — in-memory conversation history keyed by session ID; `MAX_HISTORY=2` exchanges kept
- `backend/search_tools.py` — `Tool` ABC + `CourseSearchTool` + `ToolManager`; tracks sources from the last search for citation display in the UI

**Session lifecycle:** `currentSessionId` in `script.js` starts as `null`; the backend creates a session on the first query and returns its ID; the frontend stores it for subsequent turns. Calling `createNewSession()` in JS resets `currentSessionId = null` — no backend call needed.

## Course Document Format

Course documents live in `docs/` as `.txt` files. Expected format:
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: Introduction
Lesson Link: <url>
<content...>

Lesson 1: Topic Name
Lesson Link: <url>
<content...>
```

Documents are loaded on startup (`add_course_folder` skips already-indexed courses by title). To force a full re-index, call `add_course_folder(..., clear_existing=True)`.

## Model & Config

The active model is set in `backend/config.py`:
```python
ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
```

Change it there to switch models across the whole system.
