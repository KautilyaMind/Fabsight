# FabSight deployment

FabSight v1.1 deploys as two services. The Streamlit frontend makes server-side HTTP
requests to a separately hosted FastAPI backend.

```text
Browser -> Streamlit Community Cloud -> FastAPI container
                                      -> cases, models, retrieval index
                                      -> SQLite + LangGraph checkpoints
                                      -> Google Gemini API
```

## Local development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/run_api.py
python scripts/run_ui.py
```

The API listens on `PORT` (8000 by default) and Streamlit listens on 8501.

## Docker backend

The repository Dockerfile runs the FastAPI service and honors the `PORT` environment
variable supplied by container platforms. `requirements-api.txt` omits development and
plotting packages, while `.dockerignore` excludes raw datasets, training splits,
reports, databases, and embedding-model caches from the image context.

```powershell
docker build -t fabsight-api .
docker run --rm -p 8000:8000 --env-file .env fabsight-api
```

Required backend environment variables for full LLM operation:

```text
LLM_PROVIDER=google
LLM_MODEL=<available-google-model>
GOOGLE_API_KEY=<secret>
```

Optional storage configuration:

```text
FABSIGHT_DATABASE_DIR=/persistent/fabsight
FAB_DB_PATH=/persistent/fabsight/fabsight.db
CHECKPOINT_DB_PATH=/persistent/fabsight/checkpoints.db
VECTOR_STORE_PATH=/app/data/knowledge/processed
```

Mount a persistent volume at `FABSIGHT_DATABASE_DIR` to preserve investigations,
reports, audit events, and paused LangGraph checkpoints across container replacement.
Without a volume, the portfolio demo works but its history is ephemeral.

The committed deployment bundle contains only generated demo cases, selected trained
models, and the small knowledge index. Raw public datasets, training splits, caches,
and reports remain excluded.

Configure the platform health check as `GET /health`. Before connecting the frontend,
confirm the response reports the cases, models, and knowledge retrieval as `READY`.

## Streamlit Community Cloud

Create an app using:

```text
Repository: KautilyaMind/Fabsight
Branch: master
Main file path: app/streamlit_app.py
```

`app/requirements.txt` intentionally installs only Streamlit and Requests. The ML,
LangGraph, retrieval, database, and API dependencies remain in the backend image.

In **Advanced settings -> Secrets**, add the public HTTPS backend address:

```toml
FABSIGHT_API_URL = "https://your-fabsight-api.example"
```

Root-level Streamlit secrets are exposed as environment variables, which the UI reads.
Do not add the Google API key to Streamlit Cloud; it belongs only on the backend.

## End-to-end verification

1. Open the backend `/health` endpoint and confirm v1.1 readiness.
2. Open the Streamlit app and check **System Information**.
3. Select a case in **Case Explorer** and create an investigation.
4. Run it until the graph pauses at **Human Review**.
5. Approve or reject the draft and verify the final report.
6. Confirm the audit trail includes creation, graph run, review request, feedback, and
   completion.

## Security and operational boundaries

Secrets are supplied by the hosting platforms and are never committed. Retrieved text
is untrusted, LLM output cannot execute shell commands, request bodies are validated,
exceptions are sanitized, and logs contain identifiers/status rather than secrets.
Uploads remain disabled in v1.1. The app is an educational simulation, not a production
semiconductor process-control system.
