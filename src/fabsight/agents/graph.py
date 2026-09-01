"""Actual LangGraph StateGraph for one investigation run."""
from __future__ import annotations
from typing import Any, Callable
from langgraph.graph import END, START, StateGraph
from fabsight.agents.nodes import AgentNodes
from fabsight.agents.planner import InvestigationPlanner
from fabsight.agents.router import ACTION_TO_NODE, route_plan, route_review
from fabsight.agents.state import InvestigationState
from fabsight.agents.tools import AgentTools
from fabsight.config import MAX_INVESTIGATION_ITERATIONS
from fabsight.integration.case_schema import ManufacturingCase
from fabsight.rag.llm_client import LLMClient

def build_investigation_graph(tools:AgentTools|None=None,planner_llm:LLMClient|None=None,final_synthesizer:Callable[[Any],dict[str,Any]]|None=None):
    nodes=AgentNodes(tools or AgentTools(),InvestigationPlanner(planner_llm),final_synthesizer)
    graph=StateGraph(InvestigationState)
    for name,fn in (("load_case",nodes.load_case),("plan_investigation",nodes.plan_investigation),("analyze_process",nodes.analyze_process),("analyze_vision",nodes.analyze_vision),("check_equipment",nodes.check_equipment),("retrieve_knowledge",nodes.retrieve_knowledge),("review_evidence",nodes.review_evidence),("generate_final_report",nodes.generate_final_report)): graph.add_node(name,fn)
    graph.add_edge(START,"load_case"); graph.add_edge("load_case","plan_investigation")
    graph.add_conditional_edges("plan_investigation",route_plan,{node:node for node in ACTION_TO_NODE.values()})
    for node in ("analyze_process","analyze_vision","check_equipment","retrieve_knowledge"): graph.add_edge(node,"plan_investigation")
    graph.add_conditional_edges("review_evidence",route_review,{"plan_investigation":"plan_investigation","generate_final_report":"generate_final_report"})
    graph.add_edge("generate_final_report",END)
    return graph.compile()

class InvestigationAgent:
    def __init__(self,tools:AgentTools|None=None,planner_llm:LLMClient|None=None,final_synthesizer:Callable[[Any],dict[str,Any]]|None=None,max_iterations:int=MAX_INVESTIGATION_ITERATIONS):
        self.graph=build_investigation_graph(tools,planner_llm,final_synthesizer); self.max_iterations=max_iterations
    def investigate(self,case:ManufacturingCase)->InvestigationState:
        initial:InvestigationState={"case_id":case.case_id,"case_data":case,"tool_history":[],"observations":[],"trace":[],"errors":[],"max_iterations":self.max_iterations}
        return self.graph.invoke(initial,{"recursion_limit":max(25,self.max_iterations*5)})
