import { Send } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { Markdown } from "./Markdown";

export type ChatMessage = { role: "user" | "assistant"; content: string };

type Props = {
  title: string;
  messages: ChatMessage[];
  onSend: (text: string) => Promise<void>;
  disabled?: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  placeholder?: string;
};

export function ChatPanel({
  title,
  messages,
  onSend,
  disabled,
  collapsed,
  onToggleCollapse,
  placeholder = "Ask a question — I'll guide you with hints and questions…",
}: Props) {
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const t = input.trim();
    if (!t || sending || disabled) return;
    setSending(true);
    setInput("");
    try {
      await onSend(t);
    } finally {
      setSending(false);
    }
  }

  if (collapsed) {
    return (
      <div className="flex h-full min-h-0 flex-col border-l border-sage/20 bg-white/90 p-3 shadow-inner">
        <button
          type="button"
          onClick={onToggleCollapse}
          className="rounded-lg bg-sage/10 px-3 py-2 text-left text-sm font-medium text-sageDark hover:bg-sage/20"
        >
          Open tutor chat
        </button>
      </div>
    );
  }

  return (
    <aside
      className="flex h-full min-h-0 flex-col border-l border-sage/20 bg-white/95 shadow-inner"
      aria-label="Socratic tutor chat"
    >
      <div className="flex items-center justify-between border-b border-sage/15 px-4 py-3">
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="rounded-md px-2 py-1 text-sm text-sageDark underline-offset-2 hover:underline"
          >
            Hide
          </button>
        )}
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-3" role="log" aria-live="polite">
        {messages.length === 0 && (
          <p className="text-base text-slate-600">Ask anything about this lesson — I will not give away answers, but I will help you think.</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "ml-4 rounded-2xl rounded-br-sm bg-skySoft px-4 py-3 text-ink"
                : "mr-4 rounded-2xl rounded-bl-sm bg-cream px-4 py-3 text-ink ring-1 ring-sage/15"
            }
          >
            {m.role === "assistant" ? <Markdown>{m.content}</Markdown> : <p className="whitespace-pre-wrap text-lg leading-relaxed">{m.content}</p>}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <form onSubmit={handleSubmit} className="border-t border-sage/15 p-3">
        <label htmlFor="chat-input" className="sr-only">
          Message to tutor
        </label>
        <div className="flex gap-2">
          <textarea
            id="chat-input"
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            className="min-h-[3rem] flex-1 resize-y rounded-xl border border-sage/25 bg-white px-3 py-2 text-lg text-ink placeholder:text-slate-400 focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/30"
            disabled={sending || disabled}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={sending || disabled || !input.trim()}
            className="self-end rounded-xl bg-sage px-4 py-3 font-medium text-white shadow-sm transition hover:bg-sageDark focus:outline-none focus:ring-2 focus:ring-sage disabled:opacity-50"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" aria-hidden />
          </button>
        </div>
      </form>
    </aside>
  );
}
