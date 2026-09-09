import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { vocabulary } from "@/lib/mock-data";

export default function VocabularyPage() {
  return (
    <div>
      <SectionHeader
        title="Vocabulary"
        description="Every word you've met, with how well you know it."
      />
      <Card className="p-0 overflow-hidden">
        {vocabulary.map((word, i) => (
          <div
            key={word.id}
            className={`flex items-center gap-4 px-5 py-4 ${
              i !== vocabulary.length - 1 ? "border-b border-line" : ""
            }`}
          >
            <div className="w-32 shrink-0">
              <p className="font-display text-lg text-ink">{word.igbo}</p>
              <p className="text-sm text-ink-soft">{word.english}</p>
            </div>
            <ProgressBar
              value={word.mastery}
              tone={word.mastery >= 80 ? "palm" : word.mastery >= 50 ? "gold" : "indigo"}
              className="flex-1"
            />
            <span className="w-10 text-right text-xs text-ink-soft tabular-nums">
              {word.mastery}%
            </span>
          </div>
        ))}
      </Card>
    </div>
  );
}
