"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Flame } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { useAuth } from "@/lib/auth-context";
import { pingActivity, getLevels, getLevelDetail, LevelDetail } from "@/lib/api";
import { formatLevel } from "@/lib/format-level";
import { findContinueLesson, ContinueLesson } from "@/lib/curriculum-nav";

export default function DashboardPage() {
  const router = useRouter();
  const { profile, accessToken, refreshProfile } = useAuth();
  const [nextLesson, setNextLesson] = useState<ContinueLesson | null | undefined>(undefined);
  const [level, setLevel] = useState<LevelDetail | null>(null);

  // Record today's activity once per visit — drives the real streak count.
  useEffect(() => {
    if (accessToken) {
      pingActivity(accessToken).then(() => refreshProfile()).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken) return;
    findContinueLesson(accessToken).then(setNextLesson).catch(() => setNextLesson(null));
  }, [accessToken]);

  useEffect(() => {
    const levelCode = profile?.current_level ?? "absolute_beginner";
    getLevels()
      .then((levels) => levels.find((l) => l.code === levelCode))
      .then((match) => (match ? getLevelDetail(match.id) : null))
      .then(setLevel)
      .catch(() => {});
  }, [profile?.current_level]);

  return (
    <div>
      {/* Hero */}
      <div className="rounded-3xl bg-indigo-deep text-paper px-6 py-8 lg:px-10 lg:py-10 mb-8 relative overflow-hidden">
        <UliPattern />
        <div className="relative flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div>
            <p className="text-gold text-sm font-medium mb-2">
              {formatLevel(profile?.current_level)} · {profile?.total_xp ?? 0} XP
            </p>
            <h1 className="font-display text-3xl lg:text-4xl mb-2">
              Ndewo, {profile?.display_name ?? "there"}
            </h1>
            <p className="text-paper/70 max-w-md">
              {nextLesson
                ? `Today's path picks up with "${nextLesson.lessonTitle}" in ${nextLesson.unitTitle}.`
                : "You're all caught up on your curriculum right now."}
            </p>
            <Button
              className="mt-5"
              icon={<ArrowRight size={17} />}
              disabled={!nextLesson}
              onClick={() => nextLesson && router.push(`/learn/lesson/${nextLesson.lessonId}`)}
            >
              Continue learning
            </Button>
          </div>
          <div className="flex items-center gap-4">
            <ProgressRing
              value={0}
              size={110}
              label={`0/${profile?.daily_goal_minutes ?? 15}`}
              sublabel="min today"
            />
          </div>
        </div>
      </div>

      <section className="mb-10 flex items-center justify-between">
        <h2 className="font-display text-xl">Keep your streak going</h2>
        <span className="flex items-center gap-1.5 text-sm font-semibold text-terracotta">
          <Flame size={16} />
          {profile?.current_streak ?? 0}-day streak
        </span>
      </section>

      {/* Curriculum units */}
      <section>
        <h2 className="font-display text-xl mb-4">Your curriculum</h2>
        {!level && <p className="text-ink-soft text-sm">Loading…</p>}
        {level && (
          <div className="grid sm:grid-cols-2 gap-4">
            {level.units.map((unit) => (
              <Link key={unit.id} href={`/learn/${level.id}/${unit.id}`}>
                <Card className="h-full hover:border-indigo/30 transition-colors">
                  <h3 className="font-semibold text-ink mb-1.5">{unit.title}</h3>
                  <p className="text-sm text-ink-soft mb-3">{unit.description}</p>
                  <p className="text-xs text-ink-soft">
                    {unit.lesson_count} lesson{unit.lesson_count === 1 ? "" : "s"}
                  </p>
                </Card>
              </Link>
            ))}
          </div>
        )}
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
