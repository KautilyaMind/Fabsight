# FabSight v1.0 Architecture

FabSight is a synthetic educational process-intelligence environment. It does not reproduce the data, recipes, equipment configurations, control limits, or operations of any real semiconductor manufacturing company.

```text
Engineer → Streamlit UI → FastAPI → InvestigationService
                                      ↓
                                LangGraph agent
       ProcessPredictor ─┐            │
       WaferPredictor ───┼→ evidence review → grounded RAG
       RCAPredictor ─────┤            │
       Equipment context ┤       human interrupt
       KnowledgeRetriever┘            │
                                 engineer feedback
                                      ↓
                              approved/rejected report
```

```text
SQLite application database
├── investigations
├── human_feedback
├── audit_events
└── reports (immutable revisions)

LangGraph SQLite checkpointer
└── graph state, pending interrupt, and resume position
```

HTTP routes call service methods; they do not contain model or reasoning logic. The service owns stable investigation IDs, case loading, graph commands, persistence, and sanitized errors. Application-level service construction reuses its database and checkpoint connections. Existing predictors and the local vector store remain behind tool wrappers.

Evidence lineage:

| Evidence | Origin | Meaning |
|---|---|---|
| Process measurements | Public dataset | Anonymous process variables |
| ProcessPredictor | MODEL_OUTPUT | Statistical PASS/FAIL risk |
| Wafer maps | Public dataset | Spatial patterns |
| WaferPredictor | MODEL_OUTPUT | Visual classification |
| Fab metadata | SYNTHETIC | Simulated lots, tools, events |
| Named telemetry | SYNTHETIC_TELEMETRY | Interpretable simulation signals |
| RCAPredictor | MODEL_OUTPUT | Simulated fault classification |
| Technical documents | PUBLIC_REFERENCE / USER_PROVIDED | RAG context |
| Engineer feedback | HUMAN_PROVIDED | Review context, never silent replacement |
| Hypothesis | DERIVED | Agent interpretation requiring review |

`SYNTHETIC_GROUND_TRUTH` is evaluation-only. It never enters normal graph state, prompts, reports, or API responses.
