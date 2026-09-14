"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, PlayCircle, Circle } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import { getUnitDetail, getLessonProgress, UnitDetail, LessonProgress } from "@/lib/api";

export default function UnitLessonsPage() {
  const params = useParams<{ levelId: string; unitId: string }>();
  const { accessToken } = useAuth();
  const [unit, setUnit] = useState<UnitDetail | null>(null);
  const [progressByLesson, setProgressByLesson] = useState<Record<string, LessonProgress>>({});
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    getUnitDetail(params.unitId)
      .then((data) => {
        setUnit(data);
        setError(false);
      })
      .catch(() => setError(true));
  }, [params.unitId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!unit || !accessToken) return;
    Promise.all(unit.lessons.map((l) => getLessonProgress(accessToken, l.id)))
      .then((results) => {
        const map: Record<string, LessonProgress> = {};
        results.forEach((p) => (map[p.lesson_id] = p));
        setProgressByLesson(map);
      })
      .catch(() => {
        // Non-fatal: lesson list still renders without progress badges.
      });
  }, [unit, accessToken]);

  if (error) return <ErrorState message="Couldn't load that unit." onRetry={load} />;
  if (!unit) return <p className="text-ink-soft">Loading…</p>;

  return (
    <div>
      <SectionHeader eyebrow="Unit" title={unit.title} description={unit.description ?? undefined} />

      <div className="space-y-3">
        {unit.lessons.map((lesson, i) => {
          const progress = progressByLesson[lesson.id];
          const status = progress?.status ?? "not_started";
          return (
            <Link key={lesson.id} href={`/learn/lesson/${lesson.id}`}>
              <Card className="flex items-center gap-4 hover:border-indigo/30 transition-colors">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-sand font-display text-lg">
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-ink">{lesson.title}</p>
                  {progress?.score != null && (
                    <p className="text-sm text-ink-soft">Last score: {progress.score}%</p>
                  )}
                </div>
                {status === "completed" && <CheckCircle2 size={20} className="text-palm shrink-0" />}
                {status === "in_progress" && <PlayCircle size={20} className="text-gold shrink-0" />}
                {status === "not_started" && <Circle size={20} className="text-line shrink-0" />}
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
