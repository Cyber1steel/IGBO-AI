// Static mock data powering the Phase 2 UI shell.
// Phase 3 replaces this with real API calls to the FastAPI backend.

export const learner = {
  name: "Ada",
  level: "Beginner",
  xp: 340,
  streak: 6,
  todayGoalMinutes: 15,
  todayMinutesDone: 8,
};

export const todayPath = [
  { id: "lesson", title: "Lesson", subtitle: "Greetings & introductions", status: "current" as const },
  { id: "practice", title: "Practice", subtitle: "4 exercises", status: "upcoming" as const },
  { id: "review", title: "Review", subtitle: "12 words due", status: "upcoming" as const },
];

export const units = [
  {
    id: "u1",
    title: "First Words",
    description: "Greetings, courtesy, and introducing yourself",
    lessonsDone: 5,
    lessonsTotal: 5,
    status: "complete" as const,
  },
  {
    id: "u2",
    title: "People & Family",
    description: "Talking about people, pronouns, and family terms",
    lessonsDone: 2,
    lessonsTotal: 6,
    status: "current" as const,
  },
  {
    id: "u3",
    title: "Everyday Actions",
    description: "Common verbs and simple present-tense sentences",
    lessonsDone: 0,
    lessonsTotal: 7,
    status: "locked" as const,
  },
  {
    id: "u4",
    title: "Numbers & Time",
    description: "Counting, days of the week, and telling time",
    lessonsDone: 0,
    lessonsTotal: 5,
    status: "locked" as const,
  },
];

export const practiceExercises = [
  { id: "e1", type: "Multiple choice", prompt: "How do you say “Good morning” in Igbo?" },
  { id: "e2", type: "Fill in the blank", prompt: "Aha ___ bụ Ada. (My name is Ada.)" },
  { id: "e3", type: "Translation", prompt: "Translate: “Kedu ka ị mere?”" },
  { id: "e4", type: "Listening", prompt: "Match the audio to the correct greeting." },
];

export const vocabulary = [
  { id: "v1", igbo: "Ndewo", english: "Hello", mastery: 90 },
  { id: "v2", igbo: "Daalụ", english: "Thank you", mastery: 75 },
  { id: "v3", igbo: "Kedu", english: "How are you", mastery: 60 },
  { id: "v4", igbo: "Aha m bụ", english: "My name is", mastery: 40 },
  { id: "v5", igbo: "Biko", english: "Please", mastery: 85 },
  { id: "v6", igbo: "Nnọọ", english: "Welcome", mastery: 55 },
];

export const reviewQueue = [
  { id: "r1", igbo: "Kedu ka ị mere?", english: "How are you doing?", dueIn: "Today" },
  { id: "r2", igbo: "Ọ dị mma", english: "It is fine / good", dueIn: "Today" },
  { id: "r3", igbo: "Nne", english: "Mother", dueIn: "Tomorrow" },
];

export const progressStats = {
  wordsLearned: 84,
  lessonsCompleted: 7,
  accuracy: 88,
  minutesThisWeek: [10, 15, 0, 20, 12, 18, 8],
};
