"""Generate one grounded investigation-oriented case explanation."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from fabsight.config import INTEGRATED_CASE_DIR  # noqa: E402
from fabsight.integration.io import load_cases  # noqa: E402
from fabsight.knowledge import KnowledgeRetriever  # noqa: E402
from fabsight.rag import LLMConfigurationError, RAGChain  # noqa: E402

def main() -> int:
    parser = argparse.ArgumentParser(description="Explain one synthetic FabSight case.")
    parser.add_argument("--case", required=True, dest="case_id")
    args = parser.parse_args()
    try:
        case = next((c for c in load_cases(INTEGRATED_CASE_DIR / "cases.jsonl") if c.case_id == args.case_id), None)
        if case is None: raise ValueError(f"Case not found: {args.case_id}")
        response = RAGChain(KnowledgeRetriever()).explain_case(case)
    except LLMConfigurationError as exc:
        print(f"Knowledge retrieval succeeded.\n\n{exc}", file=sys.stderr); return 2
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"FabSight case RAG failed.\n\n{exc}", file=sys.stderr); return 1
    print(f"FabSight Case Explanation\n\nCASE SUMMARY\nCase: {response.case_id}\n\nOBSERVATIONS")
    for x in response.observations or []: print(f"- {x}")
    print(f"\nRETRIEVED TECHNICAL CONTEXT\n{response.answer}\n\nPOSSIBLE INVESTIGATION AREAS")
    for x in response.investigation_areas or []: print(f"- {x}")
    print("\nEVIDENCE LIMITATIONS")
    for x in response.limitations: print(f"- {x}")
    print("\nADDITIONAL DATA THAT MAY HELP")
    for x in response.additional_evidence or []: print(f"- {x}")
    print("\nSOURCES")
    for s in response.sources: print(f"[{s.citation_id}] {s.source_file}" + (f", page {s.page}" if s.page is not None else ""))
    if response.guardrail_flags: print("\nGUARDRAIL FLAGS\n" + "\n".join(f"- {x}" for x in response.guardrail_flags))
    return 0
if __name__ == "__main__": raise SystemExit(main())
