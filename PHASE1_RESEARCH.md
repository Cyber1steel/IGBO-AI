# Phase 1 — N-ATLaS Research & Architecture (summary)

Full detail was delivered in chat; this is the condensed, durable record.

## N-ATLaS (verified, Sept 2025 sources)

- Model: `NCAIR1/N-ATLaS` on Hugging Face — Llama-3 8B fine-tune, BF16,
  ~8k usable context. Publisher: Awarri Technologies + Nigeria's FMCIDE
  (via NCAIR/NITDA).
- Igbo human-eval: ~3.87/5.0 average (fluency/coherence/relevance/accuracy) —
  usable but not high-precision; must not be trusted as sole source of truth.
- **No hosted inference API.** Self-hosting only (transformers/vLLM etc.),
  needs a GPU (~16GB VRAM in BF16, less if quantized).
- License: "Open-Source Research and Innovation License" — free for
  research/education/prototyping under 1,000 rolling-30-day active users;
  commercial license required beyond that. Attribution required if
  renamed/forked ("Powered by Awarri").
- Known limitations: dialect/accent bias, weak code-switching, no RLHF,
  training partly via machine-translated data (translation-artifact risk
  for idioms/proverbs specifically).

**Implication:** N-ATLaS is real and Igbo-capable but is a self-hosted
generation engine, not a plug-and-play API. Early phases build against a
mock provider; live integration is deferred to Phase 5 once GPU hosting is
in place.

## Architecture (unchanged since Phase 1, load-bearing for every later phase)

```
User → LearnerProfile → Curriculum → Lesson → Exercise → Assessment
     → LearnerPerformance → MasteryModel → AdaptiveLearning → AITutor → N-ATLaS
```

```
User input → Intent/context (app logic) → Learner state (DB)
→ Curriculum context (DB) → Verified Igbo knowledge (curated DB/RAG)
→ RAG retrieval → N-ATLaS (generation only) → Response validation
→ Tutor response → LearningEvent → Learner model update
```

N-ATLaS generates language. It does not decide curriculum, grade exercises,
or own the source of truth for Igbo facts — that's deterministic app logic
plus a curated, verified knowledge base.

## Stack

Next.js + TypeScript + Tailwind (frontend) · FastAPI + Python (backend) ·
PostgreSQL + pgvector for RAG (database) · N-ATLaS (AI, Phase 5+).

## 12-phase roadmap

1. N-ATLaS research + architecture ✅
2. Project foundation + UI ✅
3. Database + authentication ✅ (PostgreSQL, Alembic, JWT auth, ownership-scoped API)
4. Curriculum + lesson engine ✅ (levels/units/lessons/exercises/vocabulary, lesson flow, grading)
5. N-ATLaS integration ✅ (architecture + real HTTP client; no live inference run — no hosted API, no local GPU)
6. AI tutor
7. Exercises + assessment
8. Conversation
9. Adaptive learning + spaced repetition
10. Progress dashboard
11. Speech/pronunciation
12. Testing + optimization + deployment
