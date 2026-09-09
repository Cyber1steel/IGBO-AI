// Thin fetch wrapper for the FastAPI backend. Centralizing this here means
// Phase 3+ (auth, real endpoints) only touches this file, not every page.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
