"""Run the v0.7 RAG evaluation (uses configured LLM quota)."""
from __future__ import annotations
import json, sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from fabsight.knowledge import KnowledgeRetriever  # noqa: E402
from fabsight.rag import RAGChain  # noqa: E402
from fabsight.rag.evaluation import evaluate_rag  # noqa: E402
if __name__ == "__main__": print(json.dumps(evaluate_rag(RAGChain(KnowledgeRetriever())), indent=2))
