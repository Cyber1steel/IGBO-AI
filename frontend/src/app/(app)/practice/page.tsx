import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { practiceExercises } from "@/lib/mock-data";
import { ChevronRight } from "lucide-react";

export default function PracticePage() {
  return (
    <div>
      <SectionHeader
        eyebrow="Unit 2 · People & Family"
        title="Practice"
        description="Four short exercises. Mistakes get explained, not just marked wrong."
      />
      <div className="space-y-3">
        {practiceExercises.map((ex, i) => (
          <Card key={ex.id} className="flex items-center gap-4">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-sand text-sm font-semibold text-ink-soft">
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <Badge tone="indigo">{ex.type}</Badge>
              <p className="mt-2 text-ink font-medium">{ex.prompt}</p>
            </div>
            <ChevronRight size={18} className="text-ink-soft/50 shrink-0" />
          </Card>
        ))}
      </div>
      <Button className="mt-6 w-full sm:w-auto">Start practice</Button>
    </div>
  );
}
