import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { progressStats } from "@/lib/mock-data";

const DAYS = ["M", "T", "W", "T", "F", "S", "S"];

export default function ProgressPage() {
  const maxMinutes = Math.max(...progressStats.minutesThisWeek, 1);

  return (
    <div>
      <SectionHeader title="Progress" description="How your Igbo is coming along." />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="text-center">
          <p className="font-display text-3xl text-indigo">{progressStats.wordsLearned}</p>
          <p className="text-sm text-ink-soft mt-1">Words learned</p>
        </Card>
        <Card className="text-center">
          <p className="font-display text-3xl text-indigo">{progressStats.lessonsCompleted}</p>
          <p className="text-sm text-ink-soft mt-1">Lessons done</p>
        </Card>
        <Card className="text-center">
          <p className="font-display text-3xl text-indigo">{progressStats.accuracy}%</p>
          <p className="text-sm text-ink-soft mt-1">Accuracy</p>
        </Card>
      </div>

      <Card>
        <h3 className="font-semibold mb-4">This week</h3>
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
