# Igbo AI — Backend

FastAPI, Python 3.12.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

- `GET /api/health` → `{"status": "ok", "ai_provider": "mock"}`
- `POST /api/ai/tutor` → `{"history": [...], "message": "Ndewo"}` → tutor reply

## Structure

- `app/main.py` — FastAPI app, CORS, router registration
- `app/core/config.py` — env-driven settings (never hardcode secrets)
- `app/core/db.py` — SQLAlchemy async engine setup only; models/migrations land in Phase 3
- `app/ai/` — the AI provider abstraction:
  - `base.py` — `AIProvider` interface every provider implements
  - `mock_provider.py` — **active by default.** Canned, clearly-labeled responses
  - `natlas_provider.py` — stub for the real N-ATLaS integration (Phase 5). Raises
    `NotImplementedError` until then — it never pretends to be N-ATLaS
  - `factory.py` — the one place that picks which provider is active,
    via the `AI_PROVIDER` env var (`mock` | `natlas`)
- `app/api/` — routers (`health`, `ai`)
- `app/schemas/` — Pydantic request/response models

## Switching providers later (Phase 5)

Once a real N-ATLaS endpoint exists: implement `NATLaSProvider.generate_tutor_reply`,
set `AI_PROVIDER=natlas` in `.env`. Nothing else in the app changes — routers,
schemas, and the frontend all talk to the `AIProvider` interface, not a
specific implementation.
