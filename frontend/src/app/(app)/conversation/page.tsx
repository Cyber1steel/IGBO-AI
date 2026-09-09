"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { sendTutorMessage, TutorMessage } from "@/lib/api";

const OPENING: TutorMessage = {
  role: "tutor",
  content: "Ndewo! Let's practice a short conversation. Try greeting me in Igbo.",
};

export default function ConversationPage() {
  const [messages, setMessages] = useState<TutorMessage[]>([OPENING]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    const nextHistory = [...messages, { role: "learner" as const, content: text }];
    setMessages(nextHistory);
    setInput("");
    setSending(true);

    try {
      const reply = await sendTutorMessage(messages, text);
      setMessages([...nextHistory, { role: "tutor", content: reply.message }]);
    } catch {
      // Backend not running yet in Phase 2 — fall back locally so the UI stays usable.
      setMessages([
        ...nextHistory,
        {
          role: "tutor",
          content:
            "(Backend not reachable — this is a placeholder reply. Start the FastAPI server to talk to the mock tutor.)",
        },
      ]);
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
          Mock tutor — N-ATLaS connects in Phase 5
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "learner" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-[15px] ${
                  m.role === "learner"
                    ? "bg-indigo text-paper rounded-br-sm"
                    : "bg-sand text-ink rounded-bl-sm"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
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
