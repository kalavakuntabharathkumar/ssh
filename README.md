# Software Service Health & Incident Tracker

A compact operational utility for recording service health states, tracking incidents, and marking failures as recovered.

## Stack
Python, FastAPI, SQLite, SQLAlchemy, Pydantic, Pytest

## Run
```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `/docs` for the interactive API.

## Core behavior
- Record healthy, degraded, unavailable, and recovered states.
- Track incident severity and diagnostic messages.
- Filter incidents by state.
- Recover active incidents through a dedicated maintenance endpoint.
- Summarize service history and currently open incidents.
- Automated tests cover validation, recovery, health, and summaries.
