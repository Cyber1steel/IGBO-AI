import { getLevels, getLevelDetail, getUnitDetail, getLessonProgress } from "@/lib/api";

export interface ContinueLesson {
  lessonId: string;
  lessonTitle: string;
  unitTitle: string;
}

// Walks the curriculum (levels -> units -> lessons, in order) and returns
// the first lesson that isn't completed yet. Simple and linear — matches
// the small seed curriculum; a real "next lesson" recommendation engine is
// a later-phase concern (see Phase 1 architecture: that's adaptive
// learning, not this).
export async function findContinueLesson(accessToken: string | null): Promise<ContinueLesson | null> {
  const levels = await getLevels();
  for (const level of levels) {
    const levelDetail = await getLevelDetail(level.id);
    for (const unitSummary of levelDetail.units) {
      const unit = await getUnitDetail(unitSummary.id);
      for (const lesson of unit.lessons) {
        if (!accessToken) {
          return { lessonId: lesson.id, lessonTitle: lesson.title, unitTitle: unit.title };
        }
        const progress = await getLessonProgress(accessToken, lesson.id);
        if (progress.status !== "completed") {
          return { lessonId: lesson.id, lessonTitle: lesson.title, unitTitle: unit.title };
        }
      }
    }
  }
  return null;
}

export interface ProgressSummary {
  lessonsCompleted: number;
  lessonsTotal: number;
}

// Same linear curriculum walk as findContinueLesson, but tallies completed
// vs total lessons instead of stopping at the first incomplete one.
export async function getProgressSummary(accessToken: string): Promise<ProgressSummary> {
  const levels = await getLevels();
  let completed = 0;
  let total = 0;
  for (const level of levels) {
    const levelDetail = await getLevelDetail(level.id);
    for (const unitSummary of levelDetail.units) {
      const unit = await getUnitDetail(unitSummary.id);
      for (const lesson of unit.lessons) {
        total += 1;
        const progress = await getLessonProgress(accessToken, lesson.id);
        if (progress.status === "completed") completed += 1;
      }
    }
  }
  return { lessonsCompleted: completed, lessonsTotal: total };
}
