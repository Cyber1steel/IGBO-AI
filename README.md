# IGBO-AI

An AI-powered Igbo learning platform designed to take learners from complete beginner to practical, confident fluency through structured lessons, personalized practice, conversation, and adaptive learning.

The long-term goal is to build an AI Igbo teacher powered by **N-ATLaS**, Nigeria's open-source multilingual language model, while keeping curriculum, grading, mastery tracking, and learning progression under the application's control.

See `PHASE1_RESEARCH.md` for the N-ATLaS research findings and architecture decisions behind the project.

## Repo layout

```text
frontend/   Next.js + TypeScript + Tailwind — the learner-facing app
backend/    FastAPI — API, AI provider abstraction, database/auth

cd backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your local environment file
copy .env.example .env

# Start the API
uvicorn app.main:app --reload --port 8000

cd frontend
npm install
npm run dev