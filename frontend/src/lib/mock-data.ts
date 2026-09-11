// Learner identity (name, level, XP, streak) and curriculum content (Learn,
// Practice, Vocabulary, Review) now come from the real backend — see
// auth-context.tsx and lib/api.ts. The one thing still mock here is
// aggregate progress stats (Progress page), since Phase 4 doesn't build an
// aggregate-stats endpoint yet.

export const progressStats = {
  wordsLearned: 84,
  lessonsCompleted: 7,
  accuracy: 88,
  minutesThisWeek: [10, 15, 0, 20, 12, 18, 8],
};
