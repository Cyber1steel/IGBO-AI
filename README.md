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

**Phase 4 complete**: full curriculum & lesson engine. Levels → units →
lessons → objectives/content/examples → exercises → vocabulary, all
database-backed and browsable (Learn section). A working lesson flow
(Introduction → Learn → Examples → Practice → Completion) with
server-side, non-AI exercise grading, idempotent XP awarding, and simple
vocabulary-exposure tracking. Vocabulary, Review, Practice, Dashboard, and
Progress pages all pull real learner data. Conversation page is still on
the mock AI provider (expected — N-ATLaS integration is Phase 5).

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
