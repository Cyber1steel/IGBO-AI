# Igbo AI — Frontend

Next.js 16 (App Router) + TypeScript + Tailwind CSS v4.

## Run locally

```bash
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL if backend isn't on :8000
npm run dev
```

Visit http://localhost:3000. Register/log in to reach the learner app — the
`(app)` route group is auth-protected client-side via `AuthProvider`
(`src/lib/auth-context.tsx`), which silently refreshes the session from the
backend's httpOnly cookie on page load. The Conversation page also expects
the backend running on http://localhost:8000 — without it, chat falls back
to a local placeholder reply so the UI stays usable.

## Structure

- `src/app/` — routes. `login/` and `register/` are public. `(app)/` is the
  route group for the logged-in learner journey (dashboard, learn, practice,
  conversation, vocabulary, review, progress, profile), sharing the
  `AppShell` layout and gated by `AuthProvider`.
- `src/components/ui/` — reusable primitives (Button, Card, Badge, ProgressBar…)
- `src/components/layout/` — nav rail, mobile tab bar, app shell
- `src/components/auth/` — AuthShell, Field (login/register form pieces)
- `src/lib/api.ts` — typed client for the FastAPI backend (auth + tutor)
- `src/lib/auth-context.tsx` — session state, silent refresh, login/register/logout
- `src/lib/mock-data.ts` — curriculum/exercise placeholder data; real learner
  identity (name, level, XP, streak) now comes from the backend
- `src/lib/nav-items.ts` — single source of truth for navigation

## Design system

Tokens live in `src/app/globals.css` (`@theme inline` block): an indigo /
gold / terracotta / palm palette, Petrona (display serif) + Manrope (UI
sans), self-hosted via `@fontsource` (not `next/font/google`, so builds
don't depend on reaching Google Fonts at build time).
