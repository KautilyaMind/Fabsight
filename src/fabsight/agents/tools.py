"""Explicit adapters around existing specialist capabilities."""
from __future__ import annotations
from typing import Any
from fabsight.integration.case_schema import ManufacturingCase
from fabsight.knowledge.query_builder import build_case_query
from fabsight.knowledge.retriever import KnowledgeRetriever
from fabsight.rag.rag_chain import RAGChain

class AgentTools:
    def __init__(self, retriever: KnowledgeRetriever | None = None, rag_chain: RAGChain | None = None, rca_predictor: Any | None = None) -> None:
        self.retriever=retriever
        self.rag_chain=rag_chain
        self.rca_predictor=rca_predictor
    def analyze_process(self, case: ManufacturingCase, sample: Any | None = None, predictor: Any | None = None) -> dict[str, Any]:
        if sample is not None:
            if predictor is None:
                from fabsight.modeling import ProcessPredictor
                predictor=ProcessPredictor()
            return predictor.predict(sample)
        p=case.process_evidence
        return {"prediction":p.prediction,"failure_probability":p.failure_probability,"risk_level":p.risk_level,"top_features":p.top_anonymous_features,"provenance":{"data":p.data_source_type,"prediction":p.prediction_source_type}}
    def analyze_wafer(self, case: ManufacturingCase, wafer_map: Any | None = None, predictor: Any | None = None) -> dict[str, Any]:
        if wafer_map is not None:
            if predictor is None:
                from fabsight.vision import WaferPredictor
                predictor=WaferPredictor()
            return predictor.predict(wafer_map)
        v=case.vision_evidence
        return {"defect_class":v.defect_class,"confidence":v.confidence,"confidence_level":v.confidence_level,"top_predictions":v.top_predictions,"provenance":{"data":v.data_source_type,"prediction":v.prediction_source_type}}
    def analyze_telemetry(self,case:ManufacturingCase)->dict[str,Any]:
        evidence=case.telemetry_evidence
        if evidence is None: raise ValueError("Synthetic telemetry is not attached to this case.")
        if evidence.rca_prediction is None: raise ValueError("RCA prediction is not attached to this telemetry evidence.")
        forbidden={"ground_truth_cause","scenario","ground_truth_provenance"}&set(evidence.rca_prediction)
        if forbidden: raise ValueError("Ground-truth fields are forbidden in agent telemetry evidence.")
        return {"run_id":evidence.run_id,"trend_summary":evidence.trend_summary or {},"rca_prediction":evidence.rca_prediction,"source_type":"SYNTHETIC_TELEMETRY","prediction_source_type":"MODEL_OUTPUT","simulation_only":True}
    def get_equipment_context(self, case: ManufacturingCase) -> dict[str, Any]:
        e=case.equipment_context
        severities=[str(a.get("severity","UNKNOWN")) for a in e.recent_alarms]
        return {"tool_id":e.tool_id,"tool_status":e.tool_status,"recent_alarm_count":e.recent_alarm_count,"recent_alarm_severities":severities,"recent_alarms":e.recent_alarms,"maintenance_days_ago":e.maintenance_days_ago,"recent_maintenance":e.recent_maintenance,"process_event_id":case.fab_context.process_event_id,"lot_id":case.fab_context.lot_id,"provenance":"SYNTHETIC"}
    def retrieve_knowledge(self, case: ManufacturingCase, top_k: int = 5) -> list[dict[str, Any]]:
        if self.retriever is None: self.retriever=KnowledgeRetriever()
        return [r.to_dict() for r in self.retriever.search(build_case_query(case),top_k=top_k)]
    def grounded_explanation(self, case: ManufacturingCase) -> dict[str, Any]:
        if self.rag_chain is None:
            if self.retriever is None: self.retriever=KnowledgeRetriever()
            self.rag_chain=RAGChain(self.retriever)
        return self.rag_chain.explain_case(case).to_dict()
