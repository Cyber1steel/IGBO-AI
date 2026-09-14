# Igbo AI

An AI-powered Igbo language-learning product — not a chatbot, an AI Igbo
teacher. Takes a learner from zero Igbo to practical, confident fluency
through structured lessons, exercises, spaced repetition, and conversation
practice, ultimately powered by **N-ATLaS** (Nigeria's open-source
multilingual LLM).

See `PHASE1_RESEARCH.md` for the N-ATLaS findings and architecture decisions
this project is built around.

## Repo layout

```
frontend/   Next.js + TypeScript + Tailwind — the learner-facing app
backend/    FastAPI + PostgreSQL — API, auth, AI provider abstraction
```

## Quick start

See `backend/README.md` for full PostgreSQL/Alembic setup. Short version,
two terminals:

```bash
# Terminal 1 — backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000 — you'll land on the marketing page; register an
account to reach the dashboard (learner pages are auth-protected).

## Current phase

**Phase 6 complete**: the AI tutor now has a dedicated orchestration layer
(`app/services/tutor_orchestrator.py`) separating context-building,
provider calls, and persistence from the API route. Learner context now
includes the current unit, a lightweight application-computed
`performance_signal` ("struggling"/"developing"/"comfortable", derived from
recent exercise correctness — never invented by the model), and the
learner's own weakest vocabulary. The response contract grew hint/example/
follow_up_question/learning_action fields. Conversations resume correctly
after leaving and returning (`GET /api/ai/conversation`), and learning
events use canonical names (`exercise_correct`/`exercise_incorrect`,
`tutor_message_sent`, `tutor_correction_given`, `vocabulary_encountered`).
N-ATLaS's system prompt now encodes the language policy, structured
correction behavior, and adaptive tone — still unverified against a live
model (no hosted API, no local GPU), same honest limitation as Phase 5.

Full 12-phase roadmap lives in `PHASE1_RESEARCH.md`.

Full 12-phase roadmap lives in `PHASE1_RESEARCH.md`.

## Principles carried through every phase

- N-ATLaS is the language-generation engine only — curriculum, grading,
  mastery tracking, and spaced repetition are deterministic app logic, not
  AI decisions.
- Igbo content must be verifiable — no confidently-invented vocabulary,
  grammar, or proverbs. Verified knowledge takes priority over raw model
  output (RAG-backed validation lands in later phases).
- The mock AI provider is never presented to the learner as N-ATLaS.
- Ownership is structural: learner-scoped API routes never accept a
  user-supplied ID — they only ever resolve "your own" data from the
  authenticated token.
