# Igbo AI — Frontend

Next.js 16 (App Router) + TypeScript + Tailwind CSS v4.

## Run locally

```bash
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL if backend isn't on :8000
npm run dev
```

Visit http://localhost:3000. The Conversation page expects the backend
running on http://localhost:8000 (see `../backend/README.md`) — without it,
chat falls back to a local placeholder reply so the UI stays usable.

## Structure

- `src/app/` — routes. `(app)/` is the route group for the logged-in learner
  journey (dashboard, learn, practice, conversation, vocabulary, review,
  progress, profile), sharing the `AppShell` layout.
- `src/components/ui/` — reusable primitives (Button, Card, Badge, ProgressBar…)
- `src/components/layout/` — nav rail, mobile tab bar, app shell
- `src/lib/api.ts` — typed client for the FastAPI backend
- `src/lib/mock-data.ts` — placeholder data; replaced by real API calls in Phase 3
- `src/lib/nav-items.ts` — single source of truth for navigation

## Design system

Tokens live in `src/app/globals.css` (`@theme inline` block): an indigo /
gold / terracotta / palm palette, Petrona (display serif) + Manrope (UI
sans), self-hosted via `@fontsource` (not `next/font/google`, so builds
don't depend on reaching Google Fonts at build time).
