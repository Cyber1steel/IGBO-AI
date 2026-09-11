"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import { getMyVocabulary, VocabularyProgress } from "@/lib/api";

// Words below this mastery threshold are surfaced for review. This is a
// simple proxy, not the final spaced-repetition scheduler — the ReviewItem
// scheduling model (interval/ease/next_review_at) lands in a later phase.
const REVIEW_THRESHOLD = 70;

export default function ReviewPage() {
  const { accessToken } = useAuth();
  const [words, setWords] = useState<VocabularyProgress[] | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    getMyVocabulary(accessToken)
      .then(setWords)
      .catch(() => {});
  }, [accessToken]);

  const dueForReview = (words ?? [])
    .filter((w) => w.mastery_score < REVIEW_THRESHOLD)
    .sort((a, b) => a.mastery_score - b.mastery_score);

  return (
    <div>
      <SectionHeader
        title="Review"
        description="Words you've been exposed to but haven't mastered yet."
      />

      {!words && <p className="text-ink-soft">Loading…</p>}

      {words && dueForReview.length === 0 && (
        <Card className="text-center text-ink-soft py-10">
          Nothing due for review right now — nice work.
        </Card>
      )}

      <div className="space-y-3">
        {dueForReview.map((w) => (
          <Card key={w.vocabulary.id} className="flex items-center justify-between gap-4">
            <div>
              <p className="font-display text-lg text-ink">{w.vocabulary.igbo_text}</p>
              <p className="text-sm text-ink-soft">{w.vocabulary.english_text}</p>
            </div>
            <Badge tone={w.mastery_score < 40 ? "terracotta" : "neutral"}>
              {Math.round(w.mastery_score)}% mastered
            </Badge>
          </Card>
        ))}
      </div>
    </div>
  );
}
