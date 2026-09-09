// Thin fetch wrapper for the FastAPI backend. Centralizing this here means
// Phase 3+ (auth, real endpoints) only touches this file, not every page.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
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

export interface TutorMessage {
  role: "learner" | "tutor";
  content: string;
}

export interface TutorReply {
  message: string;
  provider: string; // e.g. "mock" or "n-atlas" — surfaced so the UI never claims to be N-ATLaS when it isn't
}

export async function sendTutorMessage(
  history: TutorMessage[],
  message: string
): Promise<TutorReply> {
  const res = await fetch(`${API_BASE_URL}/api/ai/tutor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ history, message }),
  });

  if (!res.ok) {
    throw new Error(`Tutor request failed: ${res.status}`);
  }

  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
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
  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, credentials: "include" });
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
