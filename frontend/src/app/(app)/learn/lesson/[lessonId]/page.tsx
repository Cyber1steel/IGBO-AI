"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, PartyPopper } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ExerciseStep } from "@/components/lesson/ExerciseStep";
import { useAuth } from "@/lib/auth-context";
import {
  getLessonDetail,
  startLesson,
  completeLesson,
  attemptExercise,
  LessonDetail,
  LessonProgress,
} from "@/lib/api";

type Step = { kind: "intro" | "learn" | "examples" | "completion" } | { kind: "exercise"; index: number };

export default function LessonFlowPage() {
  const params = useParams<{ lessonId: string }>();
  const router = useRouter();
  const { accessToken, refreshProfile } = useAuth();

  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [error, setError] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [completion, setCompletion] = useState<LessonProgress | null>(null);
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    getLessonDetail(params.lessonId)
      .then(setLesson)
      .catch(() => setError(true));
  }, [params.lessonId]);

  useEffect(() => {
    if (accessToken) {
      startLesson(accessToken, params.lessonId).catch(() => {});
    }
  }, [accessToken, params.lessonId]);

  if (error) return <p className="text-ink-soft">Couldn&apos;t load this lesson.</p>;
  if (!lesson) return <p className="text-ink-soft">Loading…</p>;

  const steps: Step[] = [
    { kind: "intro" },
    { kind: "learn" },
    { kind: "examples" },
    ...lesson.exercises.map((_, index) => ({ kind: "exercise" as const, index })),
    { kind: "completion" },
  ];
  const step = steps[stepIndex];
  const nextStepIsCompletion = stepIndex === steps.length - 2;

  async function handleFinish() {
    if (!accessToken) return;
    setCompleting(true);
    try {
      const result = await completeLesson(accessToken, params.lessonId);
      setCompletion(result);
      await refreshProfile();
      setStepIndex(steps.length - 1);
    } finally {
      setCompleting(false);
    }
  }

  function goNext() {
    if (nextStepIsCompletion) {
      handleFinish();
    } else {
      setStepIndex(stepIndex + 1);
    }
  }

  return (
    <div className="max-w-2xl">
      <Link href={`/learn`} className="inline-flex items-center gap-1.5 text-sm text-ink-soft hover:text-ink mb-4">
        <ArrowLeft size={15} />
        Back to Learn
      </Link>

      {step.kind !== "completion" && (
        <p className="text-sm text-ink-soft mb-2">
          Step {stepIndex + 1} of {steps.length - 1}
        </p>
      )}

      <Card className="p-7">
        {step.kind === "intro" && (
          <div>
            <h1 className="font-display text-2xl mb-3">{lesson.title}</h1>
            <p className="text-ink-soft mb-4">Here&apos;s what you&apos;ll be able to do by the end:</p>
            <ul className="space-y-2 mb-6">
              {lesson.objectives.map((o) => (
                <li key={o.order} className="flex items-start gap-2 text-ink">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-gold shrink-0" />
                  {o.description}
                </li>
              ))}
            </ul>
            <Button onClick={() => setStepIndex(1)} icon={<ArrowRight size={16} />}>
              Start lesson
            </Button>
          </div>
        )}

        {step.kind === "learn" && (
          <div>
            <h2 className="font-display text-xl mb-3">Learn</h2>
            <p className="text-ink leading-relaxed whitespace-pre-line mb-6">{lesson.content}</p>
            <Button onClick={() => setStepIndex(2)} icon={<ArrowRight size={16} />}>
              See examples
            </Button>
          </div>
        )}

        {step.kind === "examples" && (
          <div>
            <h2 className="font-display text-xl mb-4">Examples</h2>
            <div className="space-y-3 mb-6">
              {lesson.examples.map((ex, i) => (
                <div key={i} className="rounded-xl bg-sand/60 px-4 py-3">
                  <p className="font-display text-lg text-indigo">{ex.igbo}</p>
                  <p className="text-sm text-ink-soft">{ex.english}</p>
                </div>
              ))}
            </div>
            <Button onClick={goNext} icon={<ArrowRight size={16} />}>
              Practice
            </Button>
          </div>
        )}

        {step.kind === "exercise" && (
          <div>
            <h2 className="font-display text-xl mb-4">Practice</h2>
            <ExerciseStep
              key={lesson.exercises[step.index].id}
              exercise={lesson.exercises[step.index]}
              onSubmit={(answer) => attemptExercise(accessToken!, lesson.exercises[step.index].id, answer)}
            />
            <div className="mt-6">
              {nextStepIsCompletion ? (
                <Button onClick={handleFinish} disabled={completing} icon={<PartyPopper size={16} />}>
                  {completing ? "Finishing…" : "Finish lesson"}
                </Button>
              ) : (
                <Button onClick={goNext} icon={<ArrowRight size={16} />}>
                  Next
                </Button>
              )}
            </div>
          </div>
        )}

        {step.kind === "completion" && (
          <div className="text-center py-4">
            <PartyPopper size={36} className="text-gold mx-auto mb-3" />
            <h2 className="font-display text-2xl mb-2">Lesson complete!</h2>
            <p className="text-ink-soft mb-5">
              Score: <span className="font-semibold text-ink">{completion?.score ?? "—"}%</span> · +20 XP
            </p>
            <Button onClick={() => router.push("/learn")}>Back to Learn</Button>
          </div>
        )}
      </Card>
    </div>
  );
}
