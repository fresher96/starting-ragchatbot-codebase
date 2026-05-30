"""
Shared test fixtures and import-time patching for the RAG chatbot test suite.

Two module-level side effects in app.py must be neutralised before import:
  1. RAGSystem(config) -- connects to ChromaDB and loads a sentence-transformer model.
  2. DevStaticFiles(directory="../frontend") -- reads a frontend directory that does
     not exist in the test environment.

Strategy
--------
a. Stub the heaviest external packages (chromadb, sentence_transformers, anthropic)
   in sys.modules before any backend module is imported.  MagicMock stand-ins
   satisfy all attribute/call patterns these packages expose at import time.

b. Use unittest.mock.patch to replace RAGSystem with a callable that returns a
   configurable MagicMock instance, and to make StaticFiles.__init__ a no-op so
   the missing frontend directory is never checked.

Both patches are active only for the duration of `import app`; they are stopped
immediately afterwards.  The module-level `rag_system` variable in app.py is then
replaced with the shared mock so test-driven return values take effect.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# 1. Ensure backend/ is importable regardless of where pytest is invoked from
# ---------------------------------------------------------------------------
_backend_dir = os.path.join(os.path.dirname(__file__), "..")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ---------------------------------------------------------------------------
# 2. Stub heavy external dependencies before any backend module is imported
# ---------------------------------------------------------------------------
for _mod_name in ("chromadb", "chromadb.config", "sentence_transformers", "anthropic"):
    sys.modules.setdefault(_mod_name, MagicMock())

# ---------------------------------------------------------------------------
# 3. Import testing utilities (safe now that heavy deps are stubbed)
# ---------------------------------------------------------------------------
import pytest
import fastapi.staticfiles
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# 4. Build the shared mock RAGSystem instance
# ---------------------------------------------------------------------------
_mock_rag = MagicMock()
_mock_rag.session_manager.create_session.return_value = "session_test"
_mock_rag.query.return_value = ("This is a test answer.", [])
_mock_rag.get_course_analytics.return_value = {
    "total_courses": 2,
    "course_titles": ["Python Basics", "Advanced Python"],
}

# ---------------------------------------------------------------------------
# 5. Import app with patches active
#    - patch("rag_system.RAGSystem", return_value=_mock_rag): the module-level
#      `rag_system = RAGSystem(config)` call in app.py returns _mock_rag.
#    - patch.object(StaticFiles, "__init__", return_value=None): prevents the
#      DevStaticFiles(directory="../frontend") mount from checking the filesystem.
# ---------------------------------------------------------------------------
with (
    patch("rag_system.RAGSystem", return_value=_mock_rag),
    patch.object(fastapi.staticfiles.StaticFiles, "__init__", return_value=None),
):
    import app as _app_module

# Guarantee the module-level variable is our mock (it already is via the patch,
# but this makes the intent explicit and guards against future refactors).
_app_module.rag_system = _mock_rag


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_rag() -> MagicMock:
    """
    The shared RAGSystem mock.  Reset before each test so that side_effects or
    custom return_values set in one test do not leak into the next.
    """
    _mock_rag.reset_mock()
    # Restore default return values after reset
    _mock_rag.session_manager.create_session.return_value = "session_test"
    _mock_rag.query.return_value = ("This is a test answer.", [])
    _mock_rag.query.side_effect = None
    _mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Python Basics", "Advanced Python"],
    }
    _mock_rag.get_course_analytics.side_effect = None
    return _mock_rag


@pytest.fixture
def client(mock_rag) -> TestClient:
    """
    FastAPI TestClient backed by the real app with all heavy dependencies mocked.
    The mock_rag fixture is declared as a dependency so it is reset before each
    test that requests this fixture.
    """
    return TestClient(_app_module.app)
