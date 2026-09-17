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
  - `gemini_provider.py` — a real, capable general-purpose LLM (Google
    Gemini, official `google-genai` SDK, free tier). Actually understands
    and responds to what the learner writes. See "Using a real AI provider"
    below
  - `groq_provider.py` — a Groq chat-completions provider using the official
    `groq` Python SDK and the same tutor contract
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

### `AI_PROVIDER=gemini` — Google Gemini

A real, general-purpose LLM: Google Gemini, via the official `google-genai`
SDK (not the deprecated `google-generativeai` package). Chosen specifically
because it has a genuinely free tier with no credit card required — see
[Google's current free-tier limits](https://ai.google.dev/gemini-api/docs/rate-limits)
(Flash-class models, a handful of requests/minute; fine for development).
It genuinely reads and responds to the learner's message, understands
English/Igbo/mixed input, and uses Gemini's structured-output mode
(`response_schema`, not prompt-engineered JSON) to reliably return
message + optional correction/explanation/hint/example/follow_up_question.

1. Get a free key at https://aistudio.google.com/apikey (Google account, no billing needed).
2. Set `AI_PROVIDER=gemini` and `GEMINI_API_KEY=<your key>` in `.env`.
3. Restart the backend.

The default model (`GEMINI_MODEL=gemini-2.5-flash`) is set from Google's
docs at the time this was written — model availability shifts, so if it
ever 404s for your key, check the
[current model list](https://ai.google.dev/gemini-api/docs/models) and set
`GEMINI_MODEL` accordingly; no code changes needed. Free-tier requests are
also rate-limited (expect 429s if you send messages faster than a few per
minute) — the app surfaces this as a clean "try again shortly" error, not a
crash, and does not auto-retry (retrying against a free quota can burn it
faster).

If you'd rather use a different vendor (OpenAI, Anthropic, etc.), only
`gemini_provider.py` needs replacing — `factory.py`, the orchestrator, and
the frontend don't know or care which general-purpose LLM is behind
`AI_PROVIDER=gemini` (the legacy `AI_PROVIDER=general` alias remains supported).

Like every provider, this never blocks the app from starting — with no key
set, `/api/ai/tutor` just returns a clean 503 instead of crashing.

### `AI_PROVIDER=groq` — Groq

Groq uses the official `groq` Python SDK and the same Tutor Orchestrator,
context, history, prompt, and response contract as Gemini. Set:

```text
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

The model ID follows the current official `groq-python` README example. The
provider disables the SDK's automatic retries so rate-limit errors are not
silently retried and amplified. Missing keys, invalid keys, unavailable
models, rate limits, timeouts, connection failures, and malformed responses
return clean provider errors; there is no fallback to MockAIProvider.

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
