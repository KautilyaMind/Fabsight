"""Cloud deployment contract for FabSight v1.1."""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from api.main import app  # noqa: E402
from fabsight.services.health import startup_status  # noqa: E402
from scripts.run_api import api_port  # noqa: E402


def test_api_port_uses_host_environment(monkeypatch):
    monkeypatch.setenv("PORT", "9123")
    assert api_port() == 9123
    monkeypatch.setenv("PORT", "invalid")
    try:
        api_port()
    except ValueError as exc:
        assert "integer" in str(exc)
    else:
        raise AssertionError("Invalid cloud port must be rejected.")


def test_deployment_bundle_is_complete():
    required = [
        "data/integrated/cases/cases.jsonl",
        "data/knowledge/processed/chunks.jsonl",
        "data/knowledge/processed/index_metadata.json",
        "data/knowledge/processed/knowledge.index",
        "models/process/selected_model.joblib",
        "models/vision/wafer_cnn.pt",
        "models/rca/rca_model.joblib",
    ]
    assert all((ROOT / item).is_file() for item in required)
    health = startup_status()
    for subsystem in ("synthetic_cases", "process_model", "vision_model", "rca_model", "knowledge_retrieval"):
        assert health["subsystems"][subsystem] == "READY"


def test_streamlit_cloud_uses_direct_service_and_complete_dependency_set():
    requirements = (ROOT / "app" / "requirements.txt").read_text(encoding="utf-8").lower()
    ui = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    assert "create_cloud_service" in ui and "@st.cache_resource" in ui
    assert "FABSIGHT_API_URL" not in ui and "requests.get" not in ui and "requests.post" not in ui
    for runtime in ("torch", "sentence-transformers", "faiss", "langgraph", "langgraph-checkpoint-postgres", "psycopg", "streamlit"):
        assert runtime in requirements
    assert "fastapi" not in requirements


def test_cloud_profile_has_postgres_implementation_and_instructions():
    store = (ROOT / "src" / "fabsight" / "database" / "postgres_store.py").read_text(encoding="utf-8")
    checkpoint = (ROOT / "src" / "fabsight" / "agents" / "persistence.py").read_text(encoding="utf-8")
    instructions = (ROOT / "docs" / "streamlit_cloud.md").read_text(encoding="utf-8")
    assert "ConnectionPool" in store
    assert "PostgresSaver" in checkpoint
    assert "DATABASE_URL" in instructions and "app/streamlit_app.py" in instructions


def test_postgres_reads_configure_dictionary_rows_on_cursor(monkeypatch):
    from fabsight.database.postgres_store import PostgresInvestigationStore

    marker = object()
    rows_module = types.ModuleType("psycopg.rows")
    rows_module.dict_row = marker
    monkeypatch.setitem(sys.modules, "psycopg.rows", rows_module)

    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def execute(self, query, params): self.executed = (query, params)
        def fetchall(self): return [{"investigation_id": "INV-000001"}]
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def cursor(self, row_factory=None):
            assert row_factory is marker
            return Cursor()
    class Pool:
        def connection(self): return Connection()

    store = PostgresInvestigationStore.__new__(PostgresInvestigationStore)
    store.pool = Pool()
    assert store._rows("SELECT * FROM investigations", ()) == [{"investigation_id": "INV-000001"}]


def test_container_uses_api_dependency_set_and_excludes_training_data():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    api_requirements = (ROOT / "requirements-api.txt").read_text(encoding="utf-8").lower()
    assert "requirements-api.txt" in dockerfile
    assert "fastapi" in api_requirements and "langgraph" in api_requirements
    assert "pytest" not in api_requirements and "matplotlib" not in api_requirements
    for path in ("data/raw/**", "data/processed/**", "models/embeddings/**"):
        assert path in ignored


def test_public_versions_are_v1_1():
    assert app.version == "1.1.0"
    assert startup_status()["version"] == "1.1"
