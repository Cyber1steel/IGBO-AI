"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Lock, CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import { getLevels, LevelSummary } from "@/lib/api";

export default function LearnPage() {
  const { profile } = useAuth();
  const [levels, setLevels] = useState<LevelSummary[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getLevels()
      .then(setLevels)
      .catch(() => setError(true));
  }, []);

  const currentLevelCode = profile?.current_level ?? "absolute_beginner";
  const currentLevelOrder = levels?.find((l) => l.code === currentLevelCode)?.order ?? 1;

  return (
    <div>
      <SectionHeader title="Learn" description="Work through levels in order — each one builds on the last." />

      {error && (
        <Card className="text-center text-ink-soft py-10">
          Couldn&apos;t load the curriculum right now. Try refreshing.
        </Card>
      )}

      {!error && !levels && <p className="text-ink-soft">Loading levels…</p>}

      {levels && (
        <div className="space-y-3">
          {levels.map((level, i) => {
            const isCurrent = level.code === currentLevelCode;
            const isPast = level.order < currentLevelOrder;
            const isLocked = level.order > currentLevelOrder;

            const content = (
              <Card
                className={`flex items-center gap-4 transition-colors ${
                  isLocked ? "opacity-50" : "hover:border-indigo/30"
                }`}
              >
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-sand font-display text-lg">
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-ink text-lg">{level.name}</h3>
                    {isPast && <CheckCircle2 size={16} className="text-palm shrink-0" />}
                    {isLocked && <Lock size={14} className="text-ink-soft/40 shrink-0" />}
                  </div>
                  {isCurrent && <p className="text-sm text-terracotta font-medium">You are here</p>}
                </div>
              </Card>
            );

            return isLocked ? (
              <div key={level.id}>{content}</div>
            ) : (
              <Link key={level.id} href={`/learn/${level.id}`}>
                {content}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
