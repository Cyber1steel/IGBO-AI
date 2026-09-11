"use client";

import { useState } from "react";
import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { ExercisePublic, ExerciseAttemptResult } from "@/lib/api";

export function ExerciseStep({
  exercise,
  onSubmit,
}: {
  exercise: ExercisePublic;
  onSubmit: (answer: string) => Promise<ExerciseAttemptResult>;
}) {
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<ExerciseAttemptResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const options = Array.isArray(exercise.content.options)
    ? (exercise.content.options as string[])
    : null;

  async function handleSubmit(chosenAnswer: string) {
    if (!chosenAnswer.trim() || submitting || result) return;
    setSubmitting(true);
    setAnswer(chosenAnswer);
    try {
      setResult(await onSubmit(chosenAnswer));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <p className="text-lg font-medium text-ink mb-5">{exercise.prompt}</p>

      {options ? (
        <div className="grid sm:grid-cols-2 gap-2.5">
          {options.map((opt) => {
            const isChosen = answer === opt;
            const showCorrect = result && isChosen && result.is_correct;
            const showWrong = result && isChosen && !result.is_correct;
            return (
              <button
                key={opt}
                disabled={!!result}
                onClick={() => handleSubmit(opt)}
                className={`flex items-center justify-between rounded-xl border px-4 py-3 text-left font-medium transition-colors ${
                  showCorrect
                    ? "border-palm bg-palm/10 text-palm"
                    : showWrong
                    ? "border-terracotta bg-terracotta/10 text-terracotta"
                    : "border-line bg-white/60 hover:border-indigo/40"
                } ${result && !isChosen ? "opacity-50" : ""}`}
              >
                {opt}
                {showCorrect && <Check size={17} />}
                {showWrong && <X size={17} />}
              </button>
            );
          })}
        </div>
      ) : (
        <div className="flex gap-2">
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit(answer)}
            disabled={!!result}
            placeholder="Type your answer…"
            className="flex-1 rounded-xl border border-line bg-white/70 px-4 py-2.5 outline-none focus-visible:border-indigo disabled:opacity-60"
          />
          {!result && (
            <Button onClick={() => handleSubmit(answer)} disabled={submitting || !answer.trim()}>
              Check
            </Button>
          )}
        </div>
      )}

      {result && (
        <div
          className={`mt-4 rounded-xl px-4 py-3 text-sm ${
            result.is_correct ? "bg-palm/10 text-palm" : "bg-terracotta/10 text-terracotta"
          }`}
        >
          <p className="font-semibold mb-1">{result.is_correct ? "Correct!" : "Not quite."}</p>
          {!result.is_correct && result.correct_answer && (
            <p>
              Correct answer: <span className="font-medium">{result.correct_answer}</span>
            </p>
          )}
          {result.explanation && <p className="mt-1 text-ink-soft">{result.explanation}</p>}
        </div>
      )}
    </div>
  );
}
