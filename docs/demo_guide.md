# FabSight v1.0 Demo

1. Start the API and UI using the commands in `deployment.md`.
2. Open `http://localhost:8501` and read the educational-data disclaimer.
3. Select a case in Case Explorer and inspect evidence and provenance.
4. Create an investigation and run it.
5. Inspect the actual graph trace and specialist tools called.
6. Observe the persisted human-review interrupt.
7. Approve, reject, add evidence, or request bounded reanalysis.
8. Resume and inspect the structured report, citations, limitations, and approval label.
9. Open the audit trail.
10. Stop both applications, restart them, and reopen the same investigation ID to demonstrate SQLite checkpoint and history persistence.

The UI never fakes completed graph nodes. `AI_GENERATED`, `APPROVED`, and `REJECTED` are shown as distinct states.
