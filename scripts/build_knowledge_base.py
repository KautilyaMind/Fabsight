"""Build and sanity-check the local FabSight knowledge index."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.knowledge.build import build_knowledge_base  # noqa: E402
from fabsight.knowledge.evaluation import evaluate_retrieval  # noqa: E402
from fabsight.knowledge.retriever import KnowledgeRetriever  # noqa: E402


def main() -> int:
    try:
        metadata = build_knowledge_base()
        evaluation = evaluate_retrieval(KnowledgeRetriever())
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"FabSight could not build the knowledge base.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight Knowledge Base\n")
    print(f"Documents found: {metadata['documents_found']}")
    print(f"Documents loaded: {metadata['documents_loaded']}")
    print(f"Chunks created: {metadata['chunks_created']}")
    print(f"Embedding model: {metadata['embedding_model']}")
    print(f"Vector store: {metadata['vector_store']}")
    print(
        f"Retrieval sanity hit rate: {evaluation['successful_expected_topic_hits']}/"
        f"{evaluation['evaluation_queries']} ({evaluation['hit_rate']:.1%})"
    )
    print("\nKnowledge base ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
