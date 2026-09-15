"use client";

import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Send, Sparkles, AlertCircle, BookOpen, RotateCcw } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import {
  sendTutorMessage,
  getLatestConversation,
  getLessonDetail,
  ApiError,
  ApiTimeoutError,
} from "@/lib/api";

interface DisplayMessage {
  role: "learner" | "tutor" | "system";
  content: string;
  correction?: string | null;
  explanation?: string | null;
  hint?: string | null;
  example?: string | null;
  followUpQuestion?: string | null;
}

const OPENING: DisplayMessage = {
  role: "tutor",
  content: "Ndewo! Let's practice a short conversation. Try greeting me in Igbo.",
};

// Never claim to be N-ATLaS (or anything else) unless the backend actually
// says so — this is read straight from the response, never assumed.
function providerLabelFor(provider: string): string {
  if (provider === "natlas") return "N-ATLaS";
  if (provider === "general") return "AI tutor";
  return "Mock tutor — a real AI provider can be configured";
}

export default function ConversationPage() {
  const { accessToken } = useAuth();
  const searchParams = useSearchParams();
  const lessonId = searchParams.get("lessonId") ?? undefined;

  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [providerLabel, setProviderLabel] = useState("Mock tutor — a real AI provider can be configured");
  const [lessonTitle, setLessonTitle] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // Resume the learner's most recent conversation on load, so leaving and
  // coming back preserves history instead of always starting fresh.
  useEffect(() => {
    if (!accessToken) return;
    getLatestConversation(accessToken)
      .then((history) => {
        if (history && history.messages.length > 0) {
          setConversationId(history.conversation_id);
          setMessages(
            history.messages.map((m) => ({ role: m.role, content: m.content }))
          );
        } else {
          setMessages([OPENING]);
        }
      })
      .catch(() => setMessages([OPENING]))
      .finally(() => setLoadingHistory(false));
  }, [accessToken]);

  useEffect(() => {
    if (lessonId) {
      getLessonDetail(lessonId)
        .then((lesson) => setLessonTitle(lesson.title))
        .catch(() => {});
    }
  }, [lessonId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend(overrideText?: string) {
    const text = (overrideText ?? input).trim();
    if (!text || sending || !accessToken) return;

    setLastFailedMessage(null);
    setMessages((prev) => [...prev, { role: "learner", content: text }]);
    setInput("");
    setSending(true);

    try {
      const reply = await sendTutorMessage(accessToken, text, conversationId, lessonId);
      setConversationId(reply.conversation_id);
      setProviderLabel(providerLabelFor(reply.provider));
      setMessages((prev) => [
        ...prev,
        {
          role: "tutor",
          content: reply.message,
          correction: reply.correction,
          explanation: reply.explanation,
          hint: reply.hint,
          example: reply.example,
          followUpQuestion: reply.follow_up_question,
        },
      ]);
    } catch (err) {
      const message =
        err instanceof ApiTimeoutError
          ? "The tutor is taking too long to respond."
          : err instanceof ApiError
          ? err.message
          : "Couldn't reach the tutor. Check your connection.";
      setLastFailedMessage(text);
      setMessages((prev) => [...prev, { role: "system", content: message }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-9rem)] lg:h-[calc(100vh-6rem)]">
      <SectionHeader
        title="Conversation"
        description="Practice real exchanges. The tutor corrects gently and explains why."
      />

      <Card className="flex-1 flex flex-col overflow-hidden p-0">
        <div className="flex items-center justify-between gap-2 border-b border-line px-5 py-3 text-sm text-ink-soft">
          <span className="flex items-center gap-2">
            <Sparkles size={15} className="text-gold" />
            {providerLabel}
          </span>
          {lessonTitle && (
            <span className="flex items-center gap-1.5 text-indigo font-medium">
              <BookOpen size={14} />
              {lessonTitle}
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {loadingHistory && <p className="text-ink-soft text-sm">Loading conversation…</p>}

          {!loadingHistory &&
            messages.map((m, i) => {
              if (m.role === "system") {
                return (
                  <div key={i} className="flex justify-center">
                    <div className="flex items-center gap-2 rounded-xl bg-terracotta/10 text-terracotta px-4 py-2 text-sm">
                      <AlertCircle size={14} />
                      {m.content}
                      {lastFailedMessage && i === messages.length - 1 && (
                        <button
                          onClick={() => handleSend(lastFailedMessage)}
                          className="flex items-center gap-1 font-semibold underline underline-offset-2"
                        >
                          <RotateCcw size={12} />
                          Retry
                        </button>
                      )}
                    </div>
                  </div>
                );
              }
              return (
                <div key={i} className={`flex ${m.role === "learner" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-[15px] ${
                      m.role === "learner"
                        ? "bg-indigo text-paper rounded-br-sm"
                        : "bg-sand text-ink rounded-bl-sm"
                    }`}
                  >
                    {m.content}
                    {m.correction && (
                      <p className="mt-2 text-sm text-terracotta border-t border-terracotta/20 pt-2">
                        Correction: {m.correction}
                      </p>
                    )}
                    {m.explanation && <p className="mt-1 text-sm text-ink-soft">{m.explanation}</p>}
                    {m.hint && (
                      <p className="mt-1 text-sm text-[#8a6a22] bg-gold/10 rounded-lg px-2 py-1">
                        Hint: {m.hint}
                      </p>
                    )}
                    {m.example && <p className="mt-1 text-sm text-ink-soft italic">{m.example}</p>}
                    {m.followUpQuestion && (
                      <p className="mt-1 text-sm font-medium text-indigo">{m.followUpQuestion}</p>
                    )}
                  </div>
                </div>
              );
            })}

          {sending && (
            <div className="flex justify-start">
              <div className="bg-sand text-ink-soft rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm">
                Tutor is typing…
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="border-t border-line p-3 flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type in Igbo or English…"
            disabled={loadingHistory}
            className="flex-1 rounded-full border border-line bg-paper px-4 py-2.5 text-[15px] outline-none focus-visible:border-indigo disabled:opacity-60"
          />
          <button
            onClick={() => handleSend()}
            disabled={sending || loadingHistory || !input.trim()}
            aria-label="Send message"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo text-paper disabled:opacity-40 transition-opacity"
          >
            <Send size={17} />
          </button>
        </div>
      </Card>
    </div>
  );
}
