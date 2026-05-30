"""
API endpoint tests for the RAG chatbot FastAPI application.

Covers:
  POST /api/query   -- query processing with session management and source handling
  GET  /api/courses -- course catalog statistics
"""

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------

class TestQueryEndpoint:

    def test_creates_session_when_none_provided(self, client, mock_rag):
        """Backend creates a new session when the client sends no session_id."""
        mock_rag.session_manager.create_session.return_value = "session_new"
        mock_rag.query.return_value = ("Answer text.", [])

        resp = client.post("/api/query", json={"query": "What is Python?"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "session_new"
        assert data["answer"] == "Answer text."
        assert data["sources"] == []

    def test_uses_provided_session_id(self, client, mock_rag):
        """A caller-supplied session_id is forwarded to rag.query unchanged."""
        mock_rag.query.return_value = ("Follow-up answer.", [])

        resp = client.post(
            "/api/query",
            json={"query": "Tell me more", "session_id": "session_abc"},
        )

        assert resp.status_code == 200
        assert resp.json()["session_id"] == "session_abc"
        mock_rag.query.assert_called_once_with("Tell me more", "session_abc")

    def test_does_not_create_session_when_one_is_provided(self, client, mock_rag):
        """create_session is NOT called when the client already has a session_id."""
        mock_rag.query.return_value = ("Answer.", [])

        client.post(
            "/api/query",
            json={"query": "Hello", "session_id": "session_existing"},
        )

        mock_rag.session_manager.create_session.assert_not_called()

    def test_returns_sources_from_rag_system(self, client, mock_rag):
        """Sources returned by the RAG system appear in the response body."""
        mock_rag.query.return_value = (
            "Decorators wrap a function.",
            [
                {"label": "Python Basics - Lesson 3", "url": "https://example.com/l3"},
                {"label": "Python Basics", "url": None},
            ],
        )

        resp = client.post("/api/query", json={"query": "Explain decorators"})

        assert resp.status_code == 200
        sources = resp.json()["sources"]
        assert len(sources) == 2
        assert sources[0]["label"] == "Python Basics - Lesson 3"
        assert sources[0]["url"] == "https://example.com/l3"
        assert sources[1]["url"] is None

    def test_returns_500_when_rag_raises(self, client, mock_rag):
        """An unhandled exception in the RAG system produces a 500 response."""
        mock_rag.query.side_effect = RuntimeError("ChromaDB unavailable")

        resp = client.post("/api/query", json={"query": "anything"})

        assert resp.status_code == 500

    def test_returns_422_when_query_field_is_missing(self, client):
        """Omitting the required 'query' field triggers Pydantic validation (422)."""
        resp = client.post("/api/query", json={"session_id": "session_1"})

        assert resp.status_code == 422

    def test_returns_422_for_empty_body(self, client):
        """Sending no body at all also fails validation."""
        resp = client.post("/api/query", json={})

        assert resp.status_code == 422

    def test_response_schema_has_required_fields(self, client, mock_rag):
        """Response body contains 'answer' (str), 'sources' (list), 'session_id' (str)."""
        resp = client.post("/api/query", json={"query": "What is recursion?"})

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data.get("answer"), str)
        assert isinstance(data.get("sources"), list)
        assert isinstance(data.get("session_id"), str)


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------

class TestCoursesEndpoint:

    def test_returns_course_statistics(self, client, mock_rag):
        """Returns total_courses count and the list of course titles."""
        resp = client.get("/api/courses")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_courses"] == 2
        assert data["course_titles"] == ["Python Basics", "Advanced Python"]

    def test_returns_500_when_rag_raises(self, client, mock_rag):
        """An exception in get_course_analytics produces a 500 response."""
        mock_rag.get_course_analytics.side_effect = RuntimeError("DB error")

        resp = client.get("/api/courses")

        assert resp.status_code == 500

    def test_response_schema_types(self, client):
        """total_courses is an int and course_titles is a list."""
        resp = client.get("/api/courses")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data.get("total_courses"), int)
        assert isinstance(data.get("course_titles"), list)

    def test_empty_catalog(self, client, mock_rag):
        """An empty course catalog is represented as total_courses=0 and an empty list."""
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        resp = client.get("/api/courses")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_reflects_actual_catalog_contents(self, client, mock_rag):
        """The response faithfully forwards whatever the RAG system reports."""
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": ["Intro to AI", "Deep Learning", "MLOps"],
        }

        resp = client.get("/api/courses")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_courses"] == 3
        assert "Deep Learning" in data["course_titles"]
