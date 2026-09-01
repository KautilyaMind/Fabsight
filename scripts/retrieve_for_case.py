"""Retrieve potentially relevant references for one saved ManufacturingCase."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.config import INTEGRATED_CASE_DIR  # noqa: E402
from fabsight.integration.io import load_cases  # noqa: E402
from fabsight.knowledge import KnowledgeRetriever, build_case_query  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieve references for one FabSight case.")
    parser.add_argument("--case", required=True, dest="case_id")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    try:
        cases = load_cases(INTEGRATED_CASE_DIR / "cases.jsonl")
        case = next((item for item in cases if item.case_id == args.case_id), None)
        if case is None:
            raise ValueError(f"Case not found: {args.case_id}")
        query = build_case_query(case)
        results = KnowledgeRetriever().search(query, top_k=args.top_k)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"FabSight case retrieval failed.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight Case Knowledge Retrieval\n")
    print(f"Case: {case.case_id}\n")
    print("Case evidence:")
    print(f"  Process risk: {case.process_evidence.risk_level}")
    print(f"  Wafer pattern: {case.vision_evidence.defect_class}")
    print(f"  Step: {case.fab_context.process_step}")
    print(f"  Evidence status: {case.evidence_status}\n")
    print(f"Generated retrieval query:\n{query}\n")
    print("Relevant technical references:")
    for number, result in enumerate(results, start=1):
        page = f", page {result.page}" if result.page is not None else ""
        print(
            f"\n{number}. {result.source_file}{page} "
            f"[{result.source_type}, score={result.similarity_score:.4f}]"
        )
        print(result.text)
    print("\nThese passages may support investigation; they do not confirm a case-specific cause.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
