# Local and Docker deployment

## Local

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/run_api.py
python scripts/run_ui.py
```

Configure secrets only in `.env`. Never bake them into an image. The API listens on port 8000 and Streamlit on 8501.

## Docker

```powershell
docker compose up --build
```

Compose mounts the SQLite database, vector index, model directory, and reports so they survive restarts. It has no external database or orchestration requirement.

Startup health checks report each subsystem as ready, missing, or not configured. Missing LLM credentials leave exploration, persisted history, model inference, and retrieval available where their artifacts exist; generation explains its unavailable state.

Uploads are not exposed in v1.0. Existing document ingestion validates supported types and paths. Retrieved text remains untrusted, LLM output cannot execute shell commands, request bodies are validated, exceptions are sanitized, and logs contain identifiers/status rather than secrets.
