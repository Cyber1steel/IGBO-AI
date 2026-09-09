import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { learner } from "@/lib/mock-data";

export default function ProfilePage() {
  return (
    <div>
      <SectionHeader title="Profile" description="Your account and learning preferences." />

      <Card className="flex items-center gap-4 mb-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo text-paper font-display text-xl">
          {learner.name[0]}
        </div>
        <div>
          <p className="font-semibold text-ink text-lg">{learner.name}</p>
          <Badge tone="gold">{learner.level}</Badge>
        </div>
      </Card>

      <Card>
        <h3 className="font-semibold mb-3">Preferences</h3>
        <div className="divide-y divide-line">
          <Row label="Daily goal" value={`${learner.todayGoalMinutes} minutes`} />
          <Row label="Dialect focus" value="Central (Owerri)" />
          <Row label="Notifications" value="Daily reminder at 6:00 PM" />
        </div>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-3">
      <span className="text-ink-soft text-sm">{label}</span>
      <span className="text-ink font-medium text-sm">{value}</span>
    </div>
  );
}
