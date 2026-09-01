"""Offline tests for the v0.8 LangGraph investigation agent."""
from __future__ import annotations
import json,sys
from dataclasses import replace
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT_ROOT/"src"))
from langgraph.graph.state import CompiledStateGraph  # noqa: E402
from fabsight.agents.evidence import review_evidence  # noqa: E402
from fabsight.agents.evaluation import evaluate_agent_states  # noqa: E402
from fabsight.agents.graph import InvestigationAgent,build_investigation_graph  # noqa: E402
from fabsight.agents.planner import InvestigationPlanner,deterministic_plan  # noqa: E402
from fabsight.agents.tools import AgentTools  # noqa: E402
from fabsight.rag.llm_client import LLMClient  # noqa: E402
from test_knowledge_retrieval import _case  # noqa: E402

class Retriever:
    def search(self,query,top_k=5):
        from fabsight.knowledge.retriever import RetrievalResult
        return [RetrievalResult("c1","Edge variation should be investigated.","edge.md",3,.9,"PUBLIC_REFERENCE",{"topics":["edge_ring"]})]
class Tools(AgentTools):
    def __init__(self,fail=""): super().__init__(Retriever()); self.fail=fail
    def analyze_wafer(self,case,*a,**k):
        if self.fail=="vision": raise RuntimeError("vision unavailable")
        return super().analyze_wafer(case,*a,**k)
    def retrieve_knowledge(self,case,top_k=5):
        if self.fail=="knowledge": raise RuntimeError("knowledge unavailable")
        return super().retrieve_knowledge(case,top_k)
    def grounded_explanation(self,case): return {"answer":"Grounded context [S1].","sources":[{"citation_id":"S1","source_file":"edge.md"}],"limitations":["No cause confirmed."]}
class BadLLM(LLMClient):
    model_name="bad"; calls=0
    def generate(self,*a,**k): self.calls+=1; return "not json"
def run(case=None,tools=None,max_iterations=6,planner_llm=None): return InvestigationAgent(tools or Tools(),planner_llm,max_iterations=max_iterations).investigate(case or _case())
def test_state_graph_compiles(): assert isinstance(build_investigation_graph(Tools()),CompiledStateGraph)
def test_initial_state_and_nodes_update_with_provenance():
    state=run(); assert state["case_id"]=="CASE-00001" and state["provenance"]["dataset_linkage"]=="SYNTHETIC"
    assert state["process_evidence"]["risk_level"]=="HIGH" and state["vision_evidence"]["defect_class"]=="EDGE_RING"
    assert state["equipment_evidence"]["provenance"]=="SYNTHETIC" and state["knowledge_evidence"]
def test_conditional_routing_and_no_repeat_calls():
    state=run(); names=[x["tool_name"] for x in state["tool_history"]]
    assert names[:4]==["analyze_process","analyze_vision","get_equipment_context","retrieve_knowledge"]
    assert all(names.count(x)==1 for x in names)
    assert "review_evidence" in state["trace"] and state["evidence_sufficient"]
def test_tool_wrappers_return_structured_existing_outputs():
    tools=Tools(); case=_case()
    assert tools.analyze_process(case)["top_features"]==["feature_001"]
    assert tools.analyze_wafer(case)["confidence_level"]=="HIGH"
    assert tools.get_equipment_context(case)["provenance"]=="SYNTHETIC"
    assert tools.retrieve_knowledge(case)[0]["source_file"]=="edge.md"
def test_malformed_planner_retries_then_falls_back():
    llm=BadLLM(); state=run(planner_llm=llm)
    assert llm.calls>=2 and any("fallback" in x.lower() for x in state["errors"]) and state["final_report"]
def test_tool_failure_degrades_and_finalizes():
    state=run(tools=Tools("vision")); assert state["vision_evidence"] is None and state["final_report"]
    assert any("vision" in x.lower() for x in state["errors"]) and "analyze_vision" in state["attempted_tools"]
def test_knowledge_failure_degrades_and_finalizes():
    state=run(tools=Tools("knowledge")); assert not state["knowledge_evidence"] and state["final_report"]
    assert any("reference" in x.lower() for x in state["final_report"]["limitations"])
def test_conflicting_evidence_is_preserved():
    case=_case(); low=replace(case.process_evidence,prediction="PASS",failure_probability=.1,risk_level="LOW")
    state=run(replace(case,process_evidence=low)); assert state["evidence_conflicts"] and "conflict" in state["evidence_conflicts"][0].lower()
def test_bounded_loop_stops():
    state=run(max_iterations=2); assert state["iteration_count"]==2 and state["final_report"]
    assert any("iteration limit" in x.lower() for x in state["final_report"]["limitations"])
def test_final_report_schema_and_hypothesis_labels():
    report=run()["final_report"]
    for key in ("case_summary","process_findings","vision_findings","equipment_context","investigation_hypotheses","limitations","provenance"): assert key in report
    assert report["investigation_hypotheses"][0]["status"]=="HYPOTHESIS"
    assert "physical root cause is confirmed" in " ".join(report["limitations"]).lower()
def test_agent_evaluation_metrics_are_bounded(tmp_path):
    good=run(); failed=run(tools=Tools("vision"))
    report=evaluate_agent_states([("normal",good),("vision failure",failed)],tmp_path)
    assert report["successful_completion_rate"]==1.0 and report["tool_failure_recovery_rate"]==1.0
    assert report["maximum_iteration_violations"]==0 and (tmp_path/"agent_evaluation.json").is_file()
