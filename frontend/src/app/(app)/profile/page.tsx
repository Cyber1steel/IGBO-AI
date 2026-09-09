"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { LogOut } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import { formatLevel } from "@/lib/format-level";
import { updateMyProfile } from "@/lib/api";

export default function ProfilePage() {
  const { user, profile, accessToken, refreshProfile, logout } = useAuth();
  const router = useRouter();
  const [savingGoal, setSavingGoal] = useState(false);

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  async function updateDailyGoal(minutes: number) {
    if (!accessToken) return;
    setSavingGoal(true);
    try {
      await updateMyProfile(accessToken, { daily_goal_minutes: minutes });
      await refreshProfile();
    } finally {
      setSavingGoal(false);
    }
  }

  return (
    <div>
      <SectionHeader
        title="Profile"
        description="Your account and learning preferences."
        action={
          <Button variant="ghost" size="sm" icon={<LogOut size={15} />} onClick={handleLogout}>
            Log out
          </Button>
        }
      />

      <Card className="flex items-center gap-4 mb-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo text-paper font-display text-xl">
          {profile?.display_name?.[0] ?? "?"}
        </div>
        <div>
          <p className="font-semibold text-ink text-lg">{profile?.display_name}</p>
          <p className="text-sm text-ink-soft mb-1">{user?.email}</p>
          <Badge tone="gold">{formatLevel(profile?.current_level)}</Badge>
        </div>
      </Card>

      <Card>
        <h3 className="font-semibold mb-3">Preferences</h3>
        <div className="divide-y divide-line">
          <div className="flex items-center justify-between py-3">
            <span className="text-ink-soft text-sm">Daily goal</span>
            <div className="flex gap-1.5">
              {[10, 15, 20, 30].map((minutes) => (
                <button
                  key={minutes}
                  disabled={savingGoal}
                  onClick={() => updateDailyGoal(minutes)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    profile?.daily_goal_minutes === minutes
                      ? "bg-indigo text-paper"
                      : "bg-sand text-ink-soft hover:text-ink"
                  }`}
                >
                  {minutes}m
                </button>
              ))}
            </div>
          </div>
          <Row label="Current streak" value={`${profile?.current_streak ?? 0} days`} />
          <Row label="Longest streak" value={`${profile?.longest_streak ?? 0} days`} />
          <Row label="Total XP" value={`${profile?.total_xp ?? 0}`} />
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
