import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { reviewQueue } from "@/lib/mock-data";
import { RotateCcw } from "lucide-react";

export default function ReviewPage() {
  return (
    <div>
      <SectionHeader
        title="Review"
        description="Spaced repetition brings words and phrases back right before you'd forget them."
        action={
          <Button size="sm" icon={<RotateCcw size={15} />}>
            Review all ({reviewQueue.length})
          </Button>
        }
      />
      <div className="space-y-3">
        {reviewQueue.map((item) => (
          <Card key={item.id} className="flex items-center justify-between gap-4">
            <div>
              <p className="font-display text-lg text-ink">{item.igbo}</p>
              <p className="text-sm text-ink-soft">{item.english}</p>
            </div>
            <Badge tone={item.dueIn === "Today" ? "terracotta" : "neutral"}>
              {item.dueIn}
            </Badge>
          </Card>
        ))}
      </div>
    </div>
  );
}
