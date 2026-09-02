# Human-supervised investigations

FabSight separates AI recommendations from engineer-approved conclusions. A checkpointed investigation transitions through `CREATED → RUNNING → WAITING_FOR_HUMAN → RESUMED → COMPLETED`; failure and cancellation states are also validated.

The review gate categorizes requests as `LOW_CONFIDENCE`, `EVIDENCE_CONFLICT`, `MISSING_EVIDENCE`, `HYPOTHESIS_REVIEW`, or `FINAL_REPORT_APPROVAL`. Demonstration thresholds are centralized and are not production control limits.

The `request_human_review` node calls LangGraph `interrupt()`. Its state and pending node are stored by `SqliteSaver` under the stable investigation ID as `thread_id`. Feedback resumes the same checkpoint with `Command(resume=...)`, so application restart does not lose the investigation.

Engineer actions are `APPROVE`, `REJECT`, `ADD_EVIDENCE`, `REQUEST_REANALYSIS`, and `COMMENT`. Feedback is stored verbatim with role, timestamp, and `HUMAN_PROVIDED` provenance. It is appended; it never overwrites model evidence. Rejected drafts and comments remain in report/audit history.

Reports begin as `DRAFT`/`AI_GENERATED` and become `APPROVED` or `REJECTED` only through recorded feedback. Human approval means the educational report was reviewed; it does not convert simulated evidence into a real production conclusion.
