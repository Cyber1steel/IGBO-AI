"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import { getMyVocabulary, VocabularyProgress } from "@/lib/api";

export default function VocabularyPage() {
  const { accessToken } = useAuth();
  const [words, setWords] = useState<VocabularyProgress[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    getMyVocabulary(accessToken)
      .then(setWords)
      .catch(() => setError(true));
  }, [accessToken]);

  return (
    <div>
      <SectionHeader
        title="Vocabulary"
        description="Every word you've met, with how well you know it."
      />

      {error && (
        <Card className="text-center text-ink-soft py-10">Couldn&apos;t load your vocabulary right now.</Card>
      )}
      {!error && !words && <p className="text-ink-soft">Loading…</p>}
      {words && words.length === 0 && (
        <Card className="text-center text-ink-soft py-10">
          No words tracked yet — complete a lesson to start building your vocabulary.
        </Card>
      )}

      {words && words.length > 0 && (
        <Card className="p-0 overflow-hidden">
          {words.map((w, i) => (
            <div
              key={w.vocabulary.id}
              className={`flex items-center gap-4 px-5 py-4 ${
                i !== words.length - 1 ? "border-b border-line" : ""
              }`}
            >
              <div className="w-36 shrink-0">
                <p className="font-display text-lg text-ink">{w.vocabulary.igbo_text}</p>
                <p className="text-sm text-ink-soft">{w.vocabulary.english_text}</p>
              </div>
              <ProgressBar
                value={w.mastery_score}
                tone={w.mastery_score >= 80 ? "palm" : w.mastery_score >= 50 ? "gold" : "indigo"}
                className="flex-1"
              />
              <span className="w-10 text-right text-xs text-ink-soft tabular-nums">
                {Math.round(w.mastery_score)}%
              </span>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
