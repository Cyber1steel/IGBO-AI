import Link from "next/link";
import { ArrowRight, CheckCircle2, Circle, Lock, Flame } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { learner, todayPath, units } from "@/lib/mock-data";

export default function DashboardPage() {
  return (
    <div>
      {/* Hero */}
      <div className="rounded-3xl bg-indigo-deep text-paper px-6 py-8 lg:px-10 lg:py-10 mb-8 relative overflow-hidden">
        <UliPattern />
        <div className="relative flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div>
            <p className="text-gold text-sm font-medium mb-2">
              {learner.level} · {learner.xp} XP
            </p>
            <h1 className="font-display text-3xl lg:text-4xl mb-2">
              Ndewo, {learner.name}
            </h1>
            <p className="text-paper/70 max-w-md">
              Today&apos;s path picks up right where you left off — greetings and
              introductions.
            </p>
            <Button className="mt-5" icon={<ArrowRight size={17} />}>
              Continue learning
            </Button>
          </div>
          <div className="flex items-center gap-4">
            <ProgressRing
              value={(learner.todayMinutesDone / learner.todayGoalMinutes) * 100}
              size={110}
              label={`${learner.todayMinutesDone}/${learner.todayGoalMinutes}`}
              sublabel="min today"
            />
          </div>
        </div>
      </div>

      {/* Today's path */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-xl">Today&apos;s learning</h2>
          <span className="flex items-center gap-1.5 text-sm font-semibold text-terracotta">
            <Flame size={16} />
            {learner.streak}-day streak
          </span>
        </div>
        <Card className="p-0 overflow-hidden">
          {todayPath.map((step, i) => (
            <div
              key={step.id}
              className="flex items-center gap-4 px-5 py-4 border-b last:border-b-0 border-line"
            >
              {step.status === "current" ? (
                <Circle size={22} className="text-gold shrink-0" fill="var(--color-gold)" />
              ) : (
                <Circle size={22} className="text-line shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-ink">{step.title}</p>
                <p className="text-sm text-ink-soft">{step.subtitle}</p>
              </div>
              {step.status === "current" && (
                <Button size="sm" variant="secondary">
                  Start
                </Button>
              )}
              <span className="hidden sm:inline text-xs text-ink-soft/60 tabular-nums">
                {i + 1} / {todayPath.length}
              </span>
            </div>
          ))}
        </Card>
      </section>

      {/* Curriculum units */}
      <section>
        <h2 className="font-display text-xl mb-4">Your curriculum</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {units.map((unit) => (
            <Link
              key={unit.id}
              href={unit.status === "locked" ? "#" : "/learn"}
              className={unit.status === "locked" ? "pointer-events-none" : ""}
            >
              <Card className="h-full hover:border-indigo/30 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-ink">{unit.title}</h3>
                  {unit.status === "complete" && (
                    <CheckCircle2 size={18} className="text-palm shrink-0" />
                  )}
                  {unit.status === "locked" && (
                    <Lock size={16} className="text-ink-soft/40 shrink-0" />
                  )}
                </div>
                <p className="text-sm text-ink-soft mb-4">{unit.description}</p>
                <div className="flex items-center gap-3">
                  <ProgressBar
                    value={(unit.lessonsDone / unit.lessonsTotal) * 100}
                    tone={unit.status === "complete" ? "palm" : "indigo"}
                  />
                  <span className="text-xs text-ink-soft shrink-0 tabular-nums">
                    {unit.lessonsDone}/{unit.lessonsTotal}
                  </span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

// Subtle Uli-art-inspired line motif — used once, in the hero only.
function UliPattern() {
  return (
    <svg
      className="absolute right-0 top-0 h-full w-64 opacity-[0.12] pointer-events-none"
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M20 180 Q60 20 100 180 T180 180" stroke="var(--color-gold)" strokeWidth="2" />
      <circle cx="150" cy="40" r="18" stroke="var(--color-gold)" strokeWidth="2" />
      <path d="M0 100 Q100 60 200 100" stroke="var(--color-gold)" strokeWidth="1.5" />
    </svg>
  );
}
