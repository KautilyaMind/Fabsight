"""Run five deterministic v0.8 agent scenarios without live LLM calls."""
from __future__ import annotations
import json,sys
from dataclasses import replace
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT_ROOT/"src"))
from fabsight.agents.evaluation import evaluate_agent_states  # noqa: E402
from fabsight.agents.graph import InvestigationAgent  # noqa: E402
from fabsight.agents.tools import AgentTools  # noqa: E402
from fabsight.config import INTEGRATED_CASE_DIR  # noqa: E402
from fabsight.integration.io import load_cases  # noqa: E402
from fabsight.rag.llm_client import LLMClient  # noqa: E402

def offline_synthesis(case): return {"answer":"Evidence was synthesized from retrieved context [S1].","sources":[{"citation_id":"S1"}],"limitations":["No physical root cause is confirmed."]}
class FailingTools(AgentTools):
    def __init__(self,mode): super().__init__(); self.mode=mode
    def analyze_wafer(self,*args,**kwargs):
        if self.mode=="vision": raise RuntimeError("evaluation vision unavailable")
        return super().analyze_wafer(*args,**kwargs)
    def retrieve_knowledge(self,*args,**kwargs):
        if self.mode=="knowledge": raise RuntimeError("evaluation knowledge unavailable")
        return super().retrieve_knowledge(*args,**kwargs)
class MalformedPlanner(LLMClient):
    model_name="offline-malformed-planner"
    def generate(self,*args,**kwargs): return "malformed"
def main()->int:
    cases=load_cases(INTEGRATED_CASE_DIR/"cases.jsonl"); base=cases[0]
    abnormal=next((c for c in cases if c.process_evidence.risk_level=="HIGH" and c.vision_evidence.defect_class!="NONE"),base)
    visual=replace(base.vision_evidence,defect_class="EDGE_RING",confidence=.92,confidence_level="HIGH")
    low=replace(base.process_evidence,prediction="PASS",failure_probability=.1,risk_level="LOW")
    conflict=replace(base,process_evidence=low,vision_evidence=visual,evidence_status="MIXED")
    scenarios=[
        ("consistent abnormal evidence",InvestigationAgent(final_synthesizer=offline_synthesis).investigate(abnormal)),
        ("conflicting evidence",InvestigationAgent(final_synthesizer=offline_synthesis).investigate(conflict)),
        ("vision tool failure",InvestigationAgent(FailingTools("vision"),final_synthesizer=offline_synthesis).investigate(base)),
        ("knowledge tool failure",InvestigationAgent(FailingTools("knowledge"),final_synthesizer=offline_synthesis).investigate(base)),
        ("malformed planner fallback",InvestigationAgent(planner_llm=MalformedPlanner(),final_synthesizer=offline_synthesis).investigate(base)),
    ]
    print(json.dumps(evaluate_agent_states(scenarios),indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
