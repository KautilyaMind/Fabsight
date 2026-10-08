# Streamlit Cloud deployment

This branch is a single-service deployment profile. Streamlit calls the FabSight application service directly, while PostgreSQL stores application records and LangGraph checkpoints. The `master` branch remains the full FastAPI + Streamlit architecture.

## 1. Create a free PostgreSQL database

Create a Neon project and copy its pooled PostgreSQL connection string. Keep SSL enabled in the connection string.

## 2. Configure Streamlit Community Cloud

Create an app from the `streamlit-cloud` branch and use `app/streamlit_app.py` as the entrypoint. Under **Advanced settings → Secrets**, add:

```toml
DATABASE_URL = "postgresql://user:password@host/database?sslmode=require"
GOOGLE_API_KEY = "your-key"
```

Do not commit these values. The UI never displays them.

## 3. Deploy and verify

Wait for the first dependency installation and model load. Open **System Information** and confirm the packaged cases, models, retrieval index, application database, and checkpoint database show `READY`. Then create a case investigation, run it, complete Human Review, and open the final report and audit trail.

The sentence-transformer, PyTorch model, and FAISS index are intentionally retained for a faithful portfolio demonstration. They are cached with the application service, so Streamlit reruns do not reload them. If Community Cloud later exceeds its resource allowance, optimize the model profile based on measured logs rather than removing these capabilities preemptively.
