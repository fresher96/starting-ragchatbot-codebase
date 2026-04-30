# Plan: Clickable Citation Links

## Context
The chat UI shows source citations as plain text after each answer. Lesson links are already stored in ChromaDB's `course_catalog` collection (inside `lessons_json`) but are never surfaced to the frontend. The goal is to make each source a clickable link that opens the lesson video in a new tab, with no raw URL text visible.

---

## Changes

### 1. `backend/app.py`
Add a `SourceItem` Pydantic model and update `QueryResponse.sources` from `List[str]` to `List[SourceItem]`.

```python
class SourceItem(BaseModel):
    label: str
    url: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    session_id: str
```

### 2. `backend/search_tools.py` — `_format_results()`
After building the `source` label string, call the existing vector store helpers to look up the link:

```python
# Reuse existing helpers in vector_store.py (no changes needed there):
#   get_lesson_link(course_title, lesson_number) -> Optional[str]
#   get_course_link(course_title)               -> Optional[str]

if lesson_num is not None:
    url = self.store.get_lesson_link(course_title, lesson_num)
else:
    url = self.store.get_course_link(course_title)

sources.append({"label": source, "url": url})
```

Change `self.last_sources` to store dicts instead of strings. `reset_sources` stays unchanged (`= []`).

### 3. `frontend/script.js` — `addMessage()`
Replace the `sources.join(', ')` line with link-aware rendering:

```javascript
const sourceHtml = sources.map(s => {
    if (s.url) {
        return `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(s.label)}</a>`;
    }
    return escapeHtml(s.label);
}).join(', ');
// use sourceHtml in the sources-content div instead of sources.join(', ')
```

---

## Critical Files
| File | Change |
|------|--------|
| `backend/app.py` | Add `SourceItem` model; update `QueryResponse.sources` type |
| `backend/search_tools.py` | `_format_results()` — lookup link per result, store dicts in `last_sources` |
| `backend/vector_store.py` | No changes — reuse `get_lesson_link()` and `get_course_link()` |
| `frontend/script.js` | `addMessage()` — render `<a>` tags for sources that have a URL |

---

## Verification
1. Start the server: `cd backend && uv run uvicorn app:app --reload --port 1234`
2. Open the app and ask a question that triggers a course content search
3. Expand "Sources" — each citation should be a clickable hyperlink (label text only, no visible URL)
4. Click a link — opens the lesson video in a new tab
5. If a source has no link stored, it falls back to plain text without errors
