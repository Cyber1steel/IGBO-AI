// Thin fetch wrapper for the FastAPI backend. Centralizing this here means
// Phase 3+ (auth, real endpoints) only touches this file, not every page.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// No request may hang forever — every fetch through this module races
// against this timeout. A hung request becomes a clear, catchable error
// instead of a page stuck on "Loading…" indefinitely.
const REQUEST_TIMEOUT_MS = 12_000;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export class ApiTimeoutError extends Error {
  constructor(path: string) {
    super(`Request to ${path} timed out after ${REQUEST_TIMEOUT_MS / 1000}s`);
  }
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // response wasn't JSON — fall through to a generic message
  }
  return "Something went wrong. Please try again.";
}

// The one place an actual network request is made. Every other helper in
// this file (authFetch, publicFetch, sendTutorMessage, checkHealth) goes
// through this, so the timeout and error handling can't be bypassed by
// forgetting to add it somewhere new.
async function apiFetch(path: string, init: RequestInit = {}, timeoutMs = REQUEST_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiTimeoutError(path);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export interface TutorMessage {
  role: "learner" | "tutor";
  content: string;
}

export interface TutorReply {
  conversation_id: string;
  message: string;
  provider: string; // e.g. "mock" or "natlas" — surfaced so the UI never claims to be N-ATLaS when it isn't
  correction: string | null;
  explanation: string | null;
  suggested_exercise: string | null;
  language_level: string | null;
}

// The AI tutor call gets a longer timeout than everything else — a real
// inference server can legitimately take longer than a normal API call,
// and the backend's own provider-call timeout is 25s (see app/api/ai.py) —
// this must be at least that long or we'd time out client-side first and
// hide the backend's own clean timeout error.
const TUTOR_TIMEOUT_MS = 30_000;

export async function sendTutorMessage(
  accessToken: string,
  message: string,
  conversationId?: string,
  lessonId?: string
): Promise<TutorReply> {
  const res = await apiFetch(
    "/api/ai/tutor",
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify({ message, conversation_id: conversationId, lesson_id: lessonId }),
    },
    TUTOR_TIMEOUT_MS
  );

  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res));
  }

  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await apiFetch("/api/health");
    return res.ok;
  } catch {
    return false;
  }
}

// --- Auth --------------------------------------------------------------
// The refresh token lives only in an httpOnly cookie (never touched by JS);
// every request here sends `credentials: "include"` so the browser attaches
// it automatically. The access token is short-lived and kept in memory by
// AuthContext — never written to localStorage.

export interface AuthUser {
  id: string;
  email: string;
  is_verified: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: AuthUser;
}

export interface LearnerProfile {
  display_name: string;
  current_level: string;
  learning_goal: string | null;
  daily_goal_minutes: number;
  onboarding_completed: boolean;
  current_streak: number;
  longest_streak: number;
  total_xp: number;
}

async function authFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const res = await apiFetch(path, { ...init, credentials: "include" });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res));
  }
  return res;
}

export async function register(
  email: string,
  password: string,
  displayName: string
): Promise<AuthResponse> {
  const res = await authFetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
  return res.json();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await authFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

export async function logout(): Promise<void> {
  await authFetch("/auth/logout", { method: "POST" });
}

// Silently exchange the httpOnly refresh cookie for a new access token.
// Used on page load so a refresh doesn't force a re-login. Returns null
// (rather than throwing) when there's no valid session — that's the normal
// "not logged in yet" case, not an error.
export async function refreshSession(): Promise<AuthResponse | null> {
  try {
    const res = await authFetch("/auth/refresh", { method: "POST" });
    return res.json();
  } catch {
    return null;
  }
}

export async function getMyProfile(accessToken: string): Promise<LearnerProfile> {
  const res = await authFetch("/learners/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.json();
}

export async function updateMyProfile(
  accessToken: string,
  updates: Partial<Pick<LearnerProfile, "display_name" | "learning_goal" | "daily_goal_minutes" | "onboarding_completed">>
): Promise<LearnerProfile> {
  const res = await authFetch("/learners/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(updates),
  });
  return res.json();
}

export async function pingActivity(accessToken: string): Promise<LearnerProfile> {
  const res = await authFetch("/learners/me/activity-ping", {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.json();
}

// --- Curriculum ----------------------------------------------------------
// Curriculum content is public (not learner-specific); progress/attempts
// below require a token.

export interface LevelSummary {
  id: string;
  code: string;
  name: string;
  order: number;
}

export interface UnitSummary {
  id: string;
  title: string;
  description: string | null;
  order: number;
  lesson_count: number;
}

export interface LevelDetail extends LevelSummary {
  units: UnitSummary[];
}

export interface LessonSummary {
  id: string;
  title: string;
  order: number;
}

export interface UnitDetail extends UnitSummary {
  lessons: LessonSummary[];
}

export interface VocabularyItem {
  id: string;
  igbo_text: string;
  english_text: string;
  part_of_speech: string | null;
  example_sentence: string | null;
  category: string | null;
  difficulty: number;
  audio_url: string | null;
  is_verified: boolean;
}

export interface ExercisePublic {
  id: string;
  exercise_type: string;
  prompt: string;
  content: Record<string, unknown>;
  difficulty: number;
  order: number;
}

export interface LessonDetail {
  id: string;
  title: string;
  order: number;
  content: string | null;
  examples: { igbo: string; english: string }[];
  unit_id: string;
  objectives: { description: string; order: number }[];
  vocabulary: VocabularyItem[];
  exercises: ExercisePublic[];
}

export interface LessonProgress {
  lesson_id: string;
  status: "not_started" | "in_progress" | "completed";
  started_at: string | null;
  completed_at: string | null;
  score: number | null;
  attempts: number;
}

export interface ExerciseAttemptResult {
  is_correct: boolean;
  correct_answer: string | null;
  explanation: string | null;
  attempt_number: number;
}

export interface VocabularyProgress {
  vocabulary: VocabularyItem;
  exposures_count: number;
  correct_count: number;
  incorrect_count: number;
  mastery_score: number;
  last_reviewed_at: string | null;
}

async function publicFetch(path: string): Promise<Response> {
  const res = await apiFetch(path);
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res;
}

export async function getLevels(): Promise<LevelSummary[]> {
  return (await publicFetch("/curriculum/levels")).json();
}

export async function getLevelDetail(levelId: string): Promise<LevelDetail> {
  return (await publicFetch(`/curriculum/levels/${levelId}`)).json();
}

export async function getUnitDetail(unitId: string): Promise<UnitDetail> {
  return (await publicFetch(`/curriculum/units/${unitId}`)).json();
}

export async function getLessonDetail(lessonId: string): Promise<LessonDetail> {
  return (await publicFetch(`/curriculum/lessons/${lessonId}`)).json();
}

export async function startLesson(accessToken: string, lessonId: string): Promise<LessonProgress> {
  const res = await authFetch(`/lessons/${lessonId}/start`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.json();
}

export async function completeLesson(accessToken: string, lessonId: string): Promise<LessonProgress> {
  const res = await authFetch(`/lessons/${lessonId}/complete`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.json();
}

export async function getLessonProgress(accessToken: string, lessonId: string): Promise<LessonProgress> {
  const res = await authFetch(`/lessons/${lessonId}/progress`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.json();
}

export async function attemptExercise(
  accessToken: string,
  exerciseId: string,
  answer: string
): Promise<ExerciseAttemptResult> {
  const res = await authFetch(`/exercises/${exerciseId}/attempt`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ answer }),
  });
  return res.json();
}

export async function getMyVocabulary(accessToken: string): Promise<VocabularyProgress[]> {
  const res = await authFetch("/vocabulary/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.json();
}
