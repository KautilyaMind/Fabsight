"""Tests for deterministic synthetic telemetry and leakage-safe RCA."""
from __future__ import annotations
import json,sys
from dataclasses import replace
from pathlib import Path
import pandas as pd
PROJECT_ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT_ROOT/"src"))
from fabsight.agents.graph import InvestigationAgent  # noqa:E402
from fabsight.agents.tools import AgentTools  # noqa:E402
from fabsight.integration.case_schema import ManufacturingCase,TelemetryEvidence  # noqa:E402
from fabsight.rca.feature_engineering import engineer_run_features,feature_columns,split_run_ids  # noqa:E402
from fabsight.rca.rca_predictor import RCAPredictor  # noqa:E402
from fabsight.rag.context_builder import build_rag_context  # noqa:E402
from fabsight.rca.train_rca_model import train_rca_model  # noqa:E402
from fabsight.simulation.telemetry_generator import generate_telemetry  # noqa:E402
from fabsight.simulation.telemetry_schema import BASELINE,SCENARIOS  # noqa:E402
from test_agent_graph import Tools  # noqa:E402
from test_knowledge_retrieval import _case  # noqa:E402

def dataset(count=210): return generate_telemetry(count,8,42)
def test_generation_is_deterministic_and_has_every_scenario():
    a,b=dataset(); c,d=dataset(); pd.testing.assert_frame_equal(a,c); pd.testing.assert_frame_equal(b,d)
    assert set(a.ground_truth_cause)==set(SCENARIOS) and set(a.ground_truth_provenance)=={"SYNTHETIC_GROUND_TRUTH"}
def test_normal_and_fault_signal_rules():
    runs,readings=dataset(); features=engineer_run_features(runs,readings).set_index("run_id")
    by=runs.set_index("run_id")
    normal=features.loc[by[by.scenario=="NORMAL_OPERATION"].index]
    assert abs(normal.chamber_temperature_mean.mean()-BASELINE.chamber_temperature)<1
    thermal=features.loc[by[by.scenario=="THERMAL_DRIFT"].index]; assert thermal.chamber_temperature_slope.mean()>0
    pressure=features.loc[by[by.scenario=="PRESSURE_INSTABILITY"].index]; assert pressure.chamber_pressure_std.mean()>normal.chamber_pressure_std.mean()*2
    rf=features.loc[by[by.scenario=="RF_POWER_INSTABILITY"].index]; assert rf.rf_power_std.mean()>normal.rf_power_std.mean()*2
    degradation=features.loc[by[by.scenario=="TOOL_DEGRADATION"].index]; assert degradation.tool_age_cycles.mean()>normal.tool_age_cycles.mean() and degradation.vibration_slope.mean()>normal.vibration_slope.mean()
def test_run_level_split_has_no_leakage_and_ground_truth_is_not_feature():
    runs,readings=dataset(); features=engineer_run_features(runs,readings); splits=split_run_ids(runs)
    sets=[set(v) for v in splits.values()]; assert not sets[0]&sets[1] and not sets[0]&sets[2] and not sets[1]&sets[2]
    assert not {"scenario","severity","ground_truth_cause","ground_truth_provenance"}&set(feature_columns(features))
def test_model_trains_predicts_reloads_and_probability_valid(tmp_path):
    runs,readings=dataset(); features=engineer_run_features(runs,readings); meta=train_rca_model(runs,features,tmp_path)
    predictor=RCAPredictor(tmp_path); sample=features[features.run_id==meta["splits"]["test"][0]]; result=predictor.predict(sample)
    assert result["predicted_cause"] in SCENARIOS and 0<=result["confidence"]<=1 and result["top_contributors"]
    assert RCAPredictor(tmp_path).predict(sample)["predicted_cause"]==result["predicted_cause"]
def test_manufacturing_case_optional_telemetry_round_trip_and_no_truth():
    prediction={"predicted_cause":"THERMAL_DRIFT","confidence":.88,"top_contributors":[{"feature":"chamber_temperature_slope","importance":.2}]}
    case=replace(_case(),telemetry_evidence=TelemetryEvidence("RUN-00042",rca_prediction=prediction,trend_summary={"chamber_temperature":{"start":60.1,"end":67.2}}))
    restored=ManufacturingCase.from_dict(case.to_dict()); assert restored.telemetry_evidence and restored.telemetry_evidence.run_id=="RUN-00042"
    assert "ground_truth_cause" not in json.dumps(restored.to_dict())
def test_agent_routes_to_telemetry_without_ground_truth():
    prediction={"predicted_cause":"THERMAL_DRIFT","confidence":.88,"top_contributors":[{"feature":"chamber_temperature_slope","importance":.2}]}
    case=replace(_case(),telemetry_evidence=TelemetryEvidence("RUN-00042",rca_prediction=prediction,trend_summary={"chamber_temperature":{"start":60.1,"end":67.2}}))
    tools=Tools(); state=InvestigationAgent(tools,final_synthesizer=lambda c:{"answer":"Synthetic context [S1].","sources":[{"citation_id":"S1"}],"limitations":[]}).investigate(case)
    assert "analyze_telemetry" in state["trace"] and state["rca_evidence"]["rca_prediction"]["predicted_cause"]=="THERMAL_DRIFT"
    assert "ground_truth_cause" not in json.dumps({k:v for k,v in state.items() if k!="case_data"},default=str)
    assert state["final_report"]["simulated_rca_result"]["predicted_cause"]=="THERMAL_DRIFT"
    context=build_rag_context([],case=case).text
    assert "Simulated RCA prediction: THERMAL_DRIFT" in context and "ground_truth_cause" not in context
def test_agent_tool_rejects_ground_truth_leakage():
    bad=replace(_case(),telemetry_evidence=TelemetryEvidence("RUN-X",rca_prediction={"predicted_cause":"NORMAL_OPERATION","confidence":.9,"ground_truth_cause":"NORMAL_OPERATION"}))
    try: AgentTools().analyze_telemetry(bad)
    except ValueError as exc: assert "Ground-truth" in str(exc)
    else: raise AssertionError("Ground truth was accepted by normal inference.")
