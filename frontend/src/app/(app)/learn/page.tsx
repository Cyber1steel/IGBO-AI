import Link from "next/link";
import { CheckCircle2, Lock, PlayCircle } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { units } from "@/lib/mock-data";

export default function LearnPage() {
  return (
    <div>
      <SectionHeader
        title="Learn"
        description="Work through units in order — each one builds on the last."
      />
      <div className="space-y-4">
        {units.map((unit, i) => (
          <Card key={unit.id} className={unit.status === "locked" ? "opacity-60" : ""}>
            <div className="flex items-start gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-sand font-display text-lg">
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-ink text-lg">{unit.title}</h3>
                  {unit.status === "complete" && (
                    <CheckCircle2 size={17} className="text-palm shrink-0" />
                  )}
                  {unit.status === "locked" && (
                    <Lock size={15} className="text-ink-soft/40 shrink-0" />
                  )}
                </div>
                <p className="text-sm text-ink-soft mb-3">{unit.description}</p>
                <div className="flex items-center gap-3 mb-3">
                  <ProgressBar
                    value={(unit.lessonsDone / unit.lessonsTotal) * 100}
                    tone={unit.status === "complete" ? "palm" : "indigo"}
                  />
                  <span className="text-xs text-ink-soft shrink-0 tabular-nums">
                    {unit.lessonsDone}/{unit.lessonsTotal} lessons
                  </span>
                </div>
                {unit.status !== "locked" && (
                  <Link
                    href="/practice"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-indigo hover:text-indigo-deep"
                  >
                    <PlayCircle size={16} />
                    {unit.status === "complete" ? "Review unit" : "Continue"}
                  </Link>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
