"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import { getMyVocabulary } from "@/lib/api";
import { getProgressSummary, ProgressSummary } from "@/lib/curriculum-nav";
import { progressStats } from "@/lib/mock-data";

const DAYS = ["M", "T", "W", "T", "F", "S", "S"];

export default function ProgressPage() {
  const { accessToken, profile } = useAuth();
  const [wordsLearned, setWordsLearned] = useState<number | null>(null);
  const [lessons, setLessons] = useState<ProgressSummary | null>(null);
  const maxMinutes = Math.max(...progressStats.minutesThisWeek, 1);

  useEffect(() => {
    if (!accessToken) return;
    getMyVocabulary(accessToken).then((words) => setWordsLearned(words.length)).catch(() => {});
    getProgressSummary(accessToken).then(setLessons).catch(() => {});
  }, [accessToken]);

  return (
    <div>
      <SectionHeader title="Progress" description="How your Igbo is coming along." />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="text-center">
          <p className="font-display text-3xl text-indigo">{wordsLearned ?? "—"}</p>
          <p className="text-sm text-ink-soft mt-1">Words learned</p>
        </Card>
        <Card className="text-center">
          <p className="font-display text-3xl text-indigo">
            {lessons ? `${lessons.lessonsCompleted}/${lessons.lessonsTotal}` : "—"}
          </p>
          <p className="text-sm text-ink-soft mt-1">Lessons done</p>
        </Card>
        <Card className="text-center">
          <p className="font-display text-3xl text-indigo">{profile?.total_xp ?? 0}</p>
          <p className="text-sm text-ink-soft mt-1">Total XP</p>
        </Card>
      </div>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">This week</h3>
          <span className="text-xs text-ink-soft">Illustrative — daily time tracking isn&apos;t built yet</span>
        </div>
        <div className="flex items-end justify-between gap-2 h-32">
          {progressStats.minutesThisWeek.map((minutes, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-2">
              <div className="w-full flex items-end h-24">
                <div
                  className="w-full rounded-md bg-gold"
                  style={{ height: `${(minutes / maxMinutes) * 100}%`, minHeight: minutes ? 4 : 0 }}
                />
              </div>
              <span className="text-xs text-ink-soft">{DAYS[i]}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
