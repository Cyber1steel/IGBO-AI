"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { getLevelDetail, LevelDetail } from "@/lib/api";

export default function LevelUnitsPage() {
  const params = useParams<{ levelId: string }>();
  const [level, setLevel] = useState<LevelDetail | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getLevelDetail(params.levelId)
      .then(setLevel)
      .catch(() => setError(true));
  }, [params.levelId]);

  if (error) {
    return <p className="text-ink-soft">Couldn&apos;t load that level. Try going back to Learn.</p>;
  }
  if (!level) {
    return <p className="text-ink-soft">Loading…</p>;
  }

  return (
    <div>
      <SectionHeader eyebrow="Level" title={level.name} description="Units in this level, in order." />

      {level.units.length === 0 && (
        <Card className="text-center text-ink-soft py-10">
          No units published for this level yet — check back soon.
        </Card>
      )}

      <div className="grid sm:grid-cols-2 gap-4">
        {level.units.map((unit, i) => (
          <Link key={unit.id} href={`/learn/${level.id}/${unit.id}`}>
            <Card className="h-full hover:border-indigo/30 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-ink">
                  {i + 1}. {unit.title}
                </h3>
              </div>
              {unit.description && <p className="text-sm text-ink-soft mb-4">{unit.description}</p>}
              <div className="flex items-center gap-3">
                <ProgressBar value={0} />
                <span className="text-xs text-ink-soft shrink-0 tabular-nums">
                  {unit.lesson_count} lesson{unit.lesson_count === 1 ? "" : "s"}
                </span>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
