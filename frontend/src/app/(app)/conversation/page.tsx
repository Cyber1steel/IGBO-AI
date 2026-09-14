"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { useAuth } from "@/lib/auth-context";
import { sendTutorMessage, ApiError, ApiTimeoutError } from "@/lib/api";

interface DisplayMessage {
  role: "learner" | "tutor" | "system";
  content: string;
  correction?: string | null;
  explanation?: string | null;
}

const OPENING: DisplayMessage = {
  role: "tutor",
  content: "Ndewo! Let's practice a short conversation. Try greeting me in Igbo.",
};

export default function ConversationPage() {
  const { accessToken } = useAuth();
  const [messages, setMessages] = useState<DisplayMessage[]>([OPENING]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [providerLabel, setProviderLabel] = useState("Mock tutor — N-ATLaS available via configuration");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending || !accessToken) return;

    setMessages((prev) => [...prev, { role: "learner", content: text }]);
    setInput("");
    setSending(true);

    try {
      const reply = await sendTutorMessage(accessToken, text, conversationId);
      setConversationId(reply.conversation_id);
      setProviderLabel(
        reply.provider === "natlas" ? "N-ATLaS" : "Mock tutor — N-ATLaS available via configuration"
      );
      setMessages((prev) => [
        ...prev,
        {
          role: "tutor",
          content: reply.message,
          correction: reply.correction,
          explanation: reply.explanation,
        },
      ]);
    } catch (err) {
      const message =
        err instanceof ApiTimeoutError
          ? "The tutor is taking too long to respond. Please try again."
          : err instanceof ApiError
          ? err.message
          : "Couldn't reach the tutor. Check your connection and try again.";
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
        <div className="flex items-center gap-2 border-b border-line px-5 py-3 text-sm text-ink-soft">
          <Sparkles size={15} className="text-gold" />
          {providerLabel}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {messages.map((m, i) => {
            if (m.role === "system") {
              return (
                <div key={i} className="flex justify-center">
                  <div className="flex items-center gap-2 rounded-xl bg-terracotta/10 text-terracotta px-4 py-2 text-sm">
                    <AlertCircle size={14} />
                    {m.content}
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
                </div>
              </div>
            );
          })}
          <div ref={endRef} />
        </div>

        <div className="border-t border-line p-3 flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type in Igbo or English…"
            className="flex-1 rounded-full border border-line bg-paper px-4 py-2.5 text-[15px] outline-none focus-visible:border-indigo"
          />
          <button
            onClick={handleSend}
            disabled={sending || !input.trim()}
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
