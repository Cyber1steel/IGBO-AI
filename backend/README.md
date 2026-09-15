# Igbo AI — Backend

FastAPI, Python 3.12, PostgreSQL (SQLAlchemy async + Alembic).

## Run locally

```bash
# 1. PostgreSQL running locally, then create dev + test databases:
psql -c "CREATE USER igboai WITH PASSWORD 'igboai' CREATEDB;"
psql -c "CREATE DATABASE igboai OWNER igboai;"
psql -c "CREATE DATABASE igboai_test OWNER igboai;"
psql -d igboai -c "CREATE EXTENSION IF NOT EXISTS vector;"        # optional, for future RAG

# 2. Python env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # set a real JWT_SECRET_KEY for anything beyond local dev

# 3. Apply migrations, seed a little dev data
alembic upgrade head
python -m app.scripts.seed

# 4. Run
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
# tests run against a real Postgres db (igboai_test), created above
python -m pytest -v
```

20 tests covering registration, password hashing, login, JWT auth,
refresh/logout token lifecycle, and cross-user authorization.

## Key endpoints

- `GET /api/health`
- `POST /api/ai/tutor` — AI tutor (auth required); persists the conversation, see AI provider abstraction below
- `POST /auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh`, `GET /auth/me`
- `GET/PATCH /learners/me`, `POST /learners/me/activity-ping`
- `GET /curriculum/levels(+detail)/units/lessons` (public), `POST /lessons/{id}/start|complete`,
  `POST /exercises/{id}/attempt`, `GET /vocabulary` (public) / `/vocabulary/me`

## Structure

- `app/main.py` — FastAPI app, CORS, error handlers, router registration
- `app/core/config.py` — env-driven settings
- `app/core/db.py` — async SQLAlchemy engine + `get_db` dependency
- `app/core/security.py` — password hashing (bcrypt), JWT access tokens, opaque refresh tokens
- `app/core/deps.py` — `get_current_user` / `get_current_learner_profile` — the only way
  a route gets a user's data, which is what makes cross-user access structurally
  impossible rather than just checked-for
- `app/models/` — SQLAlchemy models (see `PHASE1_RESEARCH.md`'s database section
  in the repo root for the full entity list)
- `alembic/` — migrations (`alembic revision --autogenerate -m "..."`, `alembic upgrade head`)
- `app/scripts/seed.py` — small dev seed dataset, explicitly not the real curriculum
- `app/ai/` — the AI provider abstraction:
  - `base.py` — `AIProvider` interface every provider implements
  - `prompts.py` — the shared tutor system-prompt builder used by every
    real provider, so switching providers changes which model answers, not
    how the tutor behaves
  - `mock_provider.py` — **active by default.** Fixed, clearly-labeled
    responses — does not actually read the learner's message. Useful for
    UI/contract development without needing any API key
  - `general_llm_provider.py` — a real, capable general-purpose LLM
    (Anthropic's Messages API). Actually understands and responds to what
    the learner writes. See "Using a real AI provider" below
  - `natlas_provider.py` — real HTTP client for a self-hosted N-ATLaS
    endpoint (Phase 5)
  - `factory.py` — the one place that picks which provider is active, via `AI_PROVIDER` env var
- `app/api/` — routers (`health`, `ai`, `auth`, `learners`)
- `app/schemas/` — Pydantic request/response models
- `tests/` — pytest + httpx, one Postgres transaction-free schema reset per test

## Auth design notes

- Access tokens: JWT, 15 min TTL, sent as `Authorization: Bearer <token>`, kept
  in memory on the frontend (never localStorage).
- Refresh tokens: random opaque strings, stored **hashed** (SHA-256) in
  `refresh_tokens`, delivered only via an `httpOnly`, `SameSite=Lax` cookie
  scoped to `/auth`. Rotated on every use; revoked on logout.
- Passwords: bcrypt, 72-byte input capped (rejected, not silently truncated).

## Using a real AI provider

`AI_PROVIDER=mock` (default) never reads the learner's actual message — it
picks from a handful of fixed responses. For a tutor that genuinely
understands and responds to what's typed, use one of the two real
providers instead:

### `AI_PROVIDER=general` — recommended for now

A real, general-purpose LLM (currently Anthropic's Messages API — chosen
because `api.anthropic.com` is reachable from this project's dev/sandbox
network setup; swap vendors by editing `_build_payload`/`_parse_response`
in `general_llm_provider.py` if you prefer a different one). It genuinely
reads and responds to the learner's message, understands English/Igbo/
mixed input, and returns structured JSON (message + optional correction/
explanation/hint/example/follow_up_question) that the frontend renders.

1. Get an API key at https://console.anthropic.com/ (this costs money per use).
2. Set `AI_PROVIDER=general` and `GENERAL_LLM_API_KEY=<your key>` in `.env`.
3. Restart the backend.

Like every provider, this never blocks the app from starting — with no key
set, `/api/ai/tutor` just returns a clean 503 instead of crashing.

### `AI_PROVIDER=natlas` — the specialized Igbo model, once self-hosted

`NATLaSProvider` is a real HTTP client, not a stub — it's just never been
run against a live model, because no hosted N-ATLaS API exists and this
project's dev environment has no GPU. To use it:

1. Self-host N-ATLaS (`NCAIR1/N-ATLaS` on Hugging Face) behind an
   OpenAI-compatible chat-completions server — e.g. vLLM's
   `vllm serve NCAIR1/N-ATLaS --api-key ...` (needs a real GPU; see
   `PHASE1_RESEARCH.md` for hardware/licensing notes).
2. Set `AI_PROVIDER=natlas`, `NATLAS_ENDPOINT_URL=http://<your-server>`,
   and `NATLAS_API_KEY` (if your server requires one) in `.env`.
3. Restart the backend.

If your actual inference server's request/response shape differs from
OpenAI's chat-completions format, only `_build_payload`/`_parse_response`
in `app/ai/natlas_provider.py` need to change.
