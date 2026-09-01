"""Search local technical references and print cited passages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.knowledge import KnowledgeRetriever  # noqa: E402


def print_results(query: str, results: list) -> None:
    print("FabSight Knowledge Search\n")
    print(f"Query:\n{query}\n")
    for number, result in enumerate(results, start=1):
        print(f"Result {number}")
        print("--------")
        print(f"Source: {result.source_file}")
        if result.page is not None:
            print(f"Page: {result.page}")
        print(f"Source type: {result.source_type}")
        print(f"Similarity score: {result.similarity_score:.4f}\n")
        print(result.text)
        print()
    print("Similarity scores are ranking values, not correctness probabilities.")
    print("Retrieved passages are potentially relevant context, not case conclusions.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the local FabSight knowledge base.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    try:
        results = KnowledgeRetriever().search(args.query, top_k=args.top_k)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"FabSight knowledge search failed.\n\n{exc}", file=sys.stderr)
        return 1
    print_results(args.query, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
