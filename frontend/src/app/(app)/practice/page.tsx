"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Dumbbell } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import { findContinueLesson, ContinueLesson } from "@/lib/curriculum-nav";

export default function PracticePage() {
  const router = useRouter();
  const { accessToken } = useAuth();
  const [next, setNext] = useState<ContinueLesson | null | undefined>(undefined);

  useEffect(() => {
    findContinueLesson(accessToken ?? null)
      .then(setNext)
      .catch(() => setNext(null));
  }, [accessToken]);

  return (
    <div>
      <SectionHeader
        title="Practice"
        description="Exercises live inside each lesson — pick up where you left off."
      />

      {next === undefined && <p className="text-ink-soft">Loading…</p>}

      {next === null && (
        <Card className="text-center text-ink-soft py-10">
          You&apos;re all caught up — no lessons left to practice right now.
        </Card>
      )}

      {next && (
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gold/15 text-[#8a6a22]">
            <Dumbbell size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-ink-soft">{next.unitTitle}</p>
            <p className="font-semibold text-ink text-lg">{next.lessonTitle}</p>
          </div>
          <Button onClick={() => router.push(`/learn/lesson/${next.lessonId}`)}>Continue</Button>
        </Card>
      )}
    </div>
  );
}
