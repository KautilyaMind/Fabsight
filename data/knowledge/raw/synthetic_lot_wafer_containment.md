# Synthetic Lot and Wafer Containment Playbook

## Purpose and scope

This is a synthetic educational reference for FabSight. It supports investigation reasoning for the OPERATIONS domain without containing proprietary recipes, equipment settings, control limits, product definitions, or confidential manufacturing practices. It is intended to help an analyst organize evidence, identify uncertainty, and decide what qualified human review should examine next.

## Investigation trigger

Use this guide when evidence is concerning enough to pause progression while uncertainty remains. The trigger is a reason to investigate, not a diagnosis. FabSight records may combine public SECOM process observations, public WM-811K-style wafer-map evidence, synthetic fab context, synthetic equipment history, model outputs, and retrieved text. Those records are intentionally independent in origin and linked only for a software demonstration.

## Evidence to assemble

The initial review should record affected lots and wafers, process step, tool, timestamps, evidence strength, downstream exposure, and review owner. Establish a timeline before comparing signals. Record the case ID, lot, wafer, tool, process step, event time, evidence source type, model confidence, and missing fields. Preserve original observations alongside derived summaries so later reviewers can distinguish measurements from interpretations.

Ask whether the evidence repeats across wafers, lots, tools, or time. A single observation can justify follow-up but rarely supports a stable mechanism. Compare suspect material with relevant peers and explain why the comparison is fair. Where model outputs are used, retain probabilities and alternatives rather than only the winning class.

## Interpretation framework

Separate observations, hypotheses, and decisions. An observation describes what a source reports. A hypothesis proposes a possible explanation. A decision such as containment or additional sampling manages risk while uncertainty remains. Agreement between independent evidence can increase investigation priority, but it does not establish physical causality.

Important confounders include containment is a risk-control action rather than proof of causation and should remain proportional. Check data quality, timestamps, measurement coverage, and provenance before interpreting correlations. Anonymous SECOM features must remain anonymous; do not invent sensor names. Synthetic telemetry labels and equipment messages must not be treated as real process specifications.

## Recommended investigation actions

Recommended next steps are to preserve evidence, prevent accidental release, define exit criteria, obtain human approval, and document every decision. Prefer reversible evidence-gathering actions. Any change to a real process, recipe, equipment state, disposition, or control plan requires the appropriate qualified engineer and site authorization outside FabSight.

## Escalation and closure

Escalate when evidence suggests broad impact, repeated high-risk behavior, unresolved conflict, unreliable measurement, or insufficient information for safe disposition. The final report should state confidence, supporting evidence, conflicting evidence, additional data needed, limitations, provenance, and the human reviewer’s decision. Close the synthetic investigation only when the review decision and rationale are recorded in the audit trail.

## Interview demonstration note

In a FabSight demonstration, this document should be retrieved only when its topic is semantically relevant. A good answer cites the document, connects it to the case evidence, and repeats that the material is synthetic educational guidance rather than production instruction.
