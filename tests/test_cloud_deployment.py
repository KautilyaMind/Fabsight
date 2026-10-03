"""Cloud deployment contract for FabSight v1.1."""
from __future__ import annotations

import sys
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


def test_streamlit_uses_small_dependency_set():
    requirements = (ROOT / "app" / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "streamlit" in requirements and "requests" in requirements
    for heavyweight in ("torch", "sentence-transformers", "faiss", "langgraph", "fastapi"):
        assert heavyweight not in requirements


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
