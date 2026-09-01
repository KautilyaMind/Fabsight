"""Ask one grounded general technical question."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from fabsight.knowledge import KnowledgeRetriever  # noqa: E402
from fabsight.rag import LLMConfigurationError, RAGChain  # noqa: E402

def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the FabSight grounded knowledge assistant.")
    parser.add_argument("--question", required=True)
    args = parser.parse_args()
    try:
        response = RAGChain(KnowledgeRetriever()).ask(args.question)
    except LLMConfigurationError as exc:
        print(f"Knowledge retrieval succeeded.\n\n{exc}", file=sys.stderr); return 2
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"FabSight RAG failed.\n\n{exc}", file=sys.stderr); return 1
    print("FabSight Knowledge Assistant\n")
    print(f"Question:\n{args.question}\n\nAnswer:\n{response.answer}\n")
    print("Sources:")
    for s in response.sources:
        page = f", page {s.page}" if s.page is not None else ""
        print(f"[{s.citation_id}] {s.source_file}{page} ({s.source_type})")
    print("\nLimitations:")
    for item in response.limitations: print(f"- {item}")
    if response.guardrail_flags: print("\nGuardrail flags: " + ", ".join(response.guardrail_flags))
    return 0
if __name__ == "__main__": raise SystemExit(main())
