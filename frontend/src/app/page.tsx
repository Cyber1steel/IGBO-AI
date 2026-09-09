import Link from "next/link";
import { ArrowRight } from "lucide-react";

const journey = [
  { step: "Learn", detail: "Bite-sized lessons on real Igbo, not word-for-word translation" },
  { step: "Practice", detail: "Exercises with explanations, not just right or wrong" },
  { step: "Converse", detail: "Real exchanges with an AI tutor that corrects gently" },
  { step: "Remember", detail: "Spaced review keeps words and grammar in reach" },
];

export default function Home() {
  return (
    <div className="flex-1 flex flex-col">
      <header className="flex items-center justify-between px-6 py-5 lg:px-12 max-w-6xl mx-auto w-full">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo text-paper font-display text-sm font-bold">
            I
          </span>
          <span className="font-display text-lg">Igbo AI</span>
        </div>
        <Link
          href="/dashboard"
          className="text-sm font-semibold text-indigo hover:text-indigo-deep"
        >
          Open dashboard
        </Link>
      </header>

      <main className="flex-1">
        <section className="relative overflow-hidden bg-indigo-deep text-paper">
          <UliPattern />
          <div className="relative max-w-3xl mx-auto px-6 py-20 lg:py-28 text-center">
            <p className="text-gold font-medium mb-4">An AI Igbo teacher, not a chatbot</p>
            <h1 className="font-display text-4xl lg:text-5xl leading-tight mb-5">
              Learn to speak, read, and think in Igbo
            </h1>
            <p className="text-paper/70 text-lg max-w-xl mx-auto mb-8">
              Structured lessons, real conversation practice, and patient correction —
              built on verified Igbo language knowledge, from your first word to
              practical fluency.
            </p>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-gold text-indigo-deep font-semibold px-6 py-3 hover:bg-gold-soft transition-colors"
            >
              Start learning free
              <ArrowRight size={17} />
            </Link>
          </div>
        </section>

        <section className="max-w-4xl mx-auto px-6 py-16">
          <h2 className="font-display text-2xl text-center mb-10">
            How the journey works
          </h2>
          <div className="grid sm:grid-cols-2 gap-5">
            {journey.map((j) => (
              <div key={j.step} className="rounded-2xl border border-line p-5 bg-white/50">
                <h3 className="font-display text-lg text-indigo mb-1.5">{j.step}</h3>
                <p className="text-ink-soft text-sm">{j.detail}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="text-center text-xs text-ink-soft/60 py-8">
        Igbo AI · Built toward N-ATLaS-powered tutoring
      </footer>
    </div>
  );
}

function UliPattern() {
  return (
    <svg
      className="absolute inset-0 h-full w-full opacity-[0.07] pointer-events-none"
      viewBox="0 0 800 300"
      preserveAspectRatio="xMidYMid slice"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M0 250 Q200 50 400 250 T800 250" stroke="var(--color-gold)" strokeWidth="2" />
      <path d="M0 100 Q200 250 400 100 T800 100" stroke="var(--color-gold)" strokeWidth="1.5" />
      <circle cx="120" cy="60" r="24" stroke="var(--color-gold)" strokeWidth="1.5" />
      <circle cx="680" cy="220" r="30" stroke="var(--color-gold)" strokeWidth="1.5" />
    </svg>
  );
}
