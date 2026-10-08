"""Readable Streamlit presentation for a stored FabSight report."""
from __future__ import annotations

import json
from typing import Any

import streamlit as st


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _percent(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "Not available"


def _label(value: Any) -> str:
    return str(value).replace("_", " ").title() if value not in (None, "") else "Not available"


def _bullets(values: Any, empty: str = "No items reported.") -> None:
    items = _items(values)
    if not items:
        st.caption(empty)
        return
    for item in items:
        if isinstance(item, dict):
            text = item.get("statement") or item.get("answer") or item.get("feature") or json.dumps(item, default=str)
        else:
            text = str(item)
        st.markdown(f"- {text}")


def render_report(record: dict[str, Any]) -> None:
    """Render the report for a non-technical interview audience."""
    report = record.get("report", record)
    approval = report.get("approval_status") or record.get("approval_status", "AI_GENERATED")
    summary = report.get("case_summary") or {}
    process = report.get("process_findings") or {}
    vision = report.get("vision_findings") or {}
    rca = report.get("simulated_rca_result") or {}
    equipment = report.get("equipment_context") or {}
    grounded = report.get("grounded_explanation") or {}

    st.header(report.get("title", "FabSight Investigation Report"))
    st.caption(
        f"Investigation {report.get('investigation_id', record.get('investigation_id', 'Not available'))} · "
        f"Case {report.get('case_id', 'Not available')} · Generated {report.get('generated_at', record.get('generated_at', 'Not available'))}"
    )

    if approval == "APPROVED":
        st.success("Engineer review: Approved")
    elif approval == "REJECTED":
        st.error("Engineer review: Rejected — hypotheses must not be treated as accepted findings.")
    else:
        st.warning("AI-generated draft: Engineer approval has not been recorded.")

    columns = st.columns(4)
    columns[0].metric("Process risk", _label(process.get("risk_level")))
    columns[1].metric("Agent confidence", _label(report.get("confidence")))
    columns[2].metric("Process step", _label(summary.get("process_step")))
    columns[3].metric("Evidence status", _label(summary.get("evidence_status")))

    st.subheader("Executive summary")
    answer = grounded.get("answer") if isinstance(grounded, dict) else None
    if answer:
        st.write(answer)
    elif report.get("investigation_hypotheses"):
        st.write("The investigation produced evidence-based hypotheses for engineering review; no physical root cause is claimed as confirmed.")
    else:
        st.write("The investigation completed with the evidence available in this educational simulation.")

    st.subheader("Evidence findings")
    process_col, vision_col = st.columns(2)
    with process_col:
        with st.container(border=True):
            st.markdown("#### Process model")
            st.write(f"**Prediction:** {_label(process.get('prediction'))}")
            st.write(f"**Failure probability:** {_percent(process.get('failure_probability'))}")
            features = process.get("top_anonymous_features") or []
            if features: st.write("**Top anonymous features:** " + ", ".join(map(str, features)))
            st.caption("SECOM variables are anonymous; feature importance does not establish physical causation.")
    with vision_col:
        with st.container(border=True):
            st.markdown("#### Wafer-map model")
            st.write(f"**Predicted pattern:** {_label(vision.get('defect_class'))}")
            st.write(f"**Model confidence:** {_percent(vision.get('confidence'))}")
            st.write(f"**Confidence level:** {_label(vision.get('confidence_level'))}")
            st.caption("The wafer record is linked synthetically for this educational demonstration.")

    rca_col, equipment_col = st.columns(2)
    with rca_col:
        with st.container(border=True):
            st.markdown("#### Simulated root-cause analysis")
            if rca:
                st.write(f"**Predicted cause:** {_label(rca.get('predicted_cause'))}")
                st.write(f"**Confidence:** {_percent(rca.get('confidence'))}")
                st.write(f"**Severity:** {_label(rca.get('severity'))}")
            else:
                st.caption("No simulated RCA result was available.")
            st.caption("This result comes from synthetic telemetry and is a hypothesis, not a confirmed physical cause.")
    with equipment_col:
        with st.container(border=True):
            st.markdown("#### Equipment context")
            st.write(f"**Tool:** {equipment.get('tool_id', 'Not available')}")
            st.write(f"**Status:** {_label(equipment.get('tool_status'))}")
            st.write(f"**Recent alarms:** {equipment.get('recent_alarm_count', 'Not available')}")
            st.write(f"**Days since maintenance:** {equipment.get('maintenance_days_ago', 'Not available')}")

    st.subheader("Investigation hypotheses")
    hypotheses = _items(report.get("investigation_hypotheses"))
    if not hypotheses:
        st.caption("No hypotheses were produced.")
    for number, hypothesis in enumerate(hypotheses, 1):
        hypothesis = hypothesis if isinstance(hypothesis, dict) else {"statement": str(hypothesis)}
        with st.container(border=True):
            st.markdown(f"**{number}. {hypothesis.get('statement', 'Unnamed hypothesis')}**")
            st.caption(f"Status: {_label(hypothesis.get('status'))} · Confidence: {_label(hypothesis.get('confidence'))}")
            support = hypothesis.get("supporting_evidence")
            if support:
                st.write("Supporting evidence")
                _bullets(support)

    st.subheader("Recommended next investigation steps")
    next_steps = []
    if isinstance(grounded, dict):
        next_steps.extend(_items(grounded.get("investigation_areas")))
        next_steps.extend(_items(grounded.get("additional_evidence")))
    next_steps.extend(_items(report.get("additional_data_needed")))
    _bullets(list(dict.fromkeys(map(str, next_steps))), "No additional investigation steps were recorded.")

    references = _items(report.get("relevant_technical_references"))
    if references:
        st.subheader("Technical references")
        st.dataframe(references, use_container_width=True, hide_index=True)

    st.subheader("Limitations and uncertainty")
    _bullets(report.get("limitations"))
    conflicts = report.get("evidence_conflicts") or []
    if conflicts:
        st.warning("Evidence conflicts were detected.")
        _bullets(conflicts)

    feedback = _items(report.get("human_feedback"))
    if feedback:
        st.subheader("Human review")
        for item in feedback:
            if isinstance(item, dict):
                st.write(f"**{_label(item.get('action'))}** — {item.get('comment') or 'No reviewer comment.'}")
                st.caption(f"Reviewer role: {_label(item.get('author_role'))}")

    with st.expander("Technical details and raw report data"):
        st.write(f"Tool calls: {report.get('tool_calls', 'Not available')} · Agent iterations: {report.get('iteration_count', 'Not available')}")
        st.write("Provenance")
        st.json(report.get("provenance") or {})
        st.json(record)
        st.download_button(
            "Download report JSON",
            data=json.dumps(record, indent=2, default=str),
            file_name=f"{report.get('investigation_id', 'fabsight-investigation')}-report.json",
            mime="application/json",
        )
