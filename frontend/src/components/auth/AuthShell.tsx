import Link from "next/link";
import { ReactNode } from "react";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      <div className="lg:w-1/2 bg-indigo-deep text-paper flex flex-col justify-between px-8 py-10 lg:px-14 lg:py-14 relative overflow-hidden">
        <svg
          className="absolute inset-0 h-full w-full opacity-[0.08] pointer-events-none"
          viewBox="0 0 600 800"
          preserveAspectRatio="xMidYMid slice"
          fill="none"
        >
          <path d="M0 650 Q150 450 300 650 T600 650" stroke="var(--color-gold)" strokeWidth="2" />
          <path d="M0 250 Q150 450 300 250 T600 250" stroke="var(--color-gold)" strokeWidth="1.5" />
          <circle cx="100" cy="150" r="26" stroke="var(--color-gold)" strokeWidth="1.5" />
        </svg>
        <Link href="/" className="relative flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gold text-indigo-deep font-display text-lg font-bold">
            I
          </span>
          <span className="font-display text-xl">Igbo AI</span>
        </Link>
        <div className="relative max-w-sm">
          <p className="font-display text-3xl leading-snug mb-3">
            An AI Igbo teacher, from your first word to real fluency.
          </p>
          <p className="text-paper/60">
            Structured lessons, honest correction, and conversation practice —
            grounded in verified Igbo, not guesswork.
          </p>
        </div>
        <p className="relative text-xs text-paper/40">Igbo AI · N-ATLaS-powered tutoring</p>
      </div>

      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <h1 className="font-display text-2xl text-ink mb-1.5">{title}</h1>
          <p className="text-ink-soft mb-8">{subtitle}</p>
          {children}
          <div className="mt-6 text-sm text-ink-soft">{footer}</div>
        </div>
      </div>
    </div>
  );
}
