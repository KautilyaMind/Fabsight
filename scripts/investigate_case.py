"""Run one state-aware LangGraph case investigation."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT_ROOT/"src"))
from fabsight.agents import InvestigationAgent  # noqa: E402
from fabsight.integration.io import load_cases  # noqa: E402
from fabsight.config import INTEGRATED_CASE_DIR  # noqa: E402

def main()->int:
    parser=argparse.ArgumentParser(description="Investigate one synthetic case with the FabSight LangGraph agent.")
    parser.add_argument("--case",required=True,dest="case_id"); parser.add_argument("--verbose",action="store_true")
    args=parser.parse_args()
    try:
        case=next((c for c in load_cases(INTEGRATED_CASE_DIR/"cases.jsonl") if c.case_id==args.case_id),None)
        if case is None: raise ValueError(f"Case not found: {args.case_id}")
        state=InvestigationAgent().investigate(case)
    except (FileNotFoundError,RuntimeError,ValueError) as exc:
        print(f"FabSight investigation failed.\n\n{exc}",file=sys.stderr); return 1
    print(f"FabSight Investigation Agent\n\nCase loaded: {case.case_id}")
    print("Graph execution trace:\n"+" -> ".join(state["trace"]))
    print("\nTools called:")
    for call in state["tool_history"]: print(f"- {call['tool_name']}: {'success' if call['success'] else 'failed'} - {call['output_summary']}")
    if args.verbose:
        print("\nObservations:"); [print(f"- {x}") for x in state["observations"]]
        if state["errors"]: print("\nErrors:"); [print(f"- {x}") for x in state["errors"]]
    print("\nFinal structured report:\n"+json.dumps(state["final_report"],indent=2,default=str))
    return 0
if __name__=="__main__": raise SystemExit(main())
