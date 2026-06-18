import { useEffect, useRef, useState } from "react";
import { ArrowUp, ChevronDown, Loader2 } from "lucide-react";
import { MeshOrb } from "@/components/ui/mesh-orb";
import type { ChatMessage, SourceMessage, Topic, UserKey } from "@/lib/mock-data";

interface Props {
  activeUser: UserKey;
  onUserChange: (u: UserKey) => void;
  messages: ChatMessage[];
  onSend: (text: string) => void;
  activeTopic: Topic | null;
  onSelectTopic: (t: Topic | null) => void;
  topics: Topic[];
  totalMessages: number;
  isLoading?: boolean;
  backendReady?: boolean;
}

function confidenceColor(c?: number) {
  if (c === undefined) return "#525252";
  if (c >= 0.8) return "#10B981";
  if (c >= 0.5) return "#F59E0B";
  return "#EF4444";
}

export function ChatArea({
  activeUser,
  onUserChange,
  messages,
  onSend,
  activeTopic,
  onSelectTopic,
  topics,
  totalMessages,
  isLoading = false,
  backendReady = false,
}: Props) {
  const [input, setInput] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [timelineOpen, setTimelineOpen] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, isLoading]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const t = input.trim();
    if (!t || isLoading) return;
    onSend(t);
    setInput("");
  }

  return (
    <section className="flex min-w-0 flex-1 flex-col" style={{ background: "transparent" }}>
      {/* Header */}
      <header
        className="flex items-center justify-between border-b px-6 py-3"
        style={{ borderColor: "rgba(255,255,255,0.08)", background: "rgba(6,6,10,0.28)", backdropFilter: "blur(14px)" }}
      >
        <div className="flex items-center gap-3">
          <div className="readable-muted text-xs font-medium tracking-tight">
            KaStack RAG
          </div>
          {backendReady ? (
            <span className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium"
              style={{ background: "rgba(16,185,129,0.12)", color: "#10B981", border: "1px solid rgba(16,185,129,0.25)" }}>
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: "#10B981", animation: "pulse 2s infinite" }} />
              Online
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium"
              style={{ background: "rgba(245,158,11,0.12)", color: "#F59E0B", border: "1px solid rgba(245,158,11,0.25)" }}>
              Connecting…
            </span>
          )}
        </div>

        <div
          className="inline-flex items-center rounded-full border p-0.5"
          style={{ borderColor: "rgba(255,255,255,0.12)", background: "rgba(12,12,16,0.72)", backdropFilter: "blur(14px)" }}
          role="tablist"
        >
          {(["user1", "user2"] as UserKey[]).map((u) => {
            const isActive = activeUser === u;
            return (
              <button
                key={u}
                role="tab"
                aria-selected={isActive}
                onClick={() => onUserChange(u)}
                className="rounded-full px-4 py-1 text-xs font-medium transition-colors duration-150"
                style={{
                  background: isActive ? "#F5F5F5" : "transparent",
                  color: isActive ? "#0A0A0A" : "#DADDE5",
                }}
              >
                {u === "user1" ? "User 1" : "User 2"}
              </button>
            );
          })}
        </div>

        <div className="readable-muted text-xs">
          <span className="readable-text">{totalMessages.toLocaleString()}</span> messages
        </div>
      </header>

      {/* Topic timeline */}
      <div className="border-b" style={{ borderColor: "rgba(255,255,255,0.08)", background: "rgba(6,6,10,0.18)", backdropFilter: "blur(10px)" }}>
        <div className="flex items-center justify-between px-6 py-2">
          <button
            onClick={() => setTimelineOpen((v) => !v)}
            className="readable-muted flex items-center gap-1 text-[11px] uppercase tracking-wider"
          >
            Topics
            <ChevronDown
              size={12}
              style={{ transform: timelineOpen ? "rotate(0)" : "rotate(-90deg)", transition: "transform 150ms" }}
            />
          </button>
          {activeTopic && (
            <button
              onClick={() => onSelectTopic(null)}
              className="readable-text text-[11px] transition-colors"
            >
              Clear filter
            </button>
          )}
        </div>
        {timelineOpen && (
          <div className="flex gap-2 overflow-x-auto px-6 pb-3">
            {topics.length === 0 ? (
              <div className="readable-muted text-[11px]">Loading topics…</div>
            ) : (
              topics.map((t) => {
                const isActive = activeTopic?.id === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => onSelectTopic(isActive ? null : t)}
                    className="glass-pill shrink-0 rounded-full px-3 py-1 text-xs transition-colors duration-150"
                    style={{
                      background: isActive ? "rgba(37,99,235,0.82)" : undefined,
                      borderColor: isActive ? "rgba(96,165,250,0.72)" : undefined,
                      color: isActive ? "#FFFFFF" : "#E2E5EC",
                    }}
                  >
                    {t.title}{" "}
                    <span style={{ color: isActive ? "rgba(255,255,255,0.82)" : "#B7BBC6" }}>
                      · {t.messageCount}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 && !isLoading ? (
          <div className="glass mx-auto max-w-2xl rounded-2xl px-6 py-5 text-center">
            <div className="readable-text text-sm font-medium">
              Ask a question about these {totalMessages.toLocaleString()} messages.
            </div>
            <div className="readable-muted mt-2 text-xs">
              Try: "What jobs does User 1 mention?" or "How do they talk about moving cities?"
            </div>
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-6">
            {messages.map((m) => (
              <MessageRow
                key={m.id}
                message={m}
                expanded={!!expanded[m.id]}
                onToggle={() => setExpanded((s) => ({ ...s, [m.id]: !s[m.id] }))}
                onSend={onSend}
                totalMessages={totalMessages}
              />
            ))}
            {isLoading && (
              <div className="flex max-w-[88%] flex-col gap-2">
                <div className="glass rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2 text-[10px] readable-muted">
                    <MeshOrb size={14} />
                    <span className="readable-text" style={{ fontWeight: 600 }}>KaStack</span>
                    <span>·</span>
                    <span>Thinking…</span>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin" style={{ color: "#2563EB" }} />
                    <span className="readable-muted text-[13px]">
                      Searching through conversations and generating an answer…
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 pb-6">
        <form
          onSubmit={submit}
          className="glass-strong mx-auto flex max-w-3xl items-center gap-2 rounded-2xl px-3"
          onFocus={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.18)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)")}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isLoading ? "Waiting for response…" : "Ask about these conversations..."}
            autoComplete="off"
            spellCheck={false}
            disabled={isLoading}
            className="flex-1 bg-transparent py-3 text-sm outline-none placeholder:text-[#B7BBC6] disabled:opacity-50"
            style={{ color: "#F7F7FA", background: "transparent" }}
            id="chat-input"
          />
          <button
            type="submit"
            aria-label="Send"
            disabled={!input.trim() || isLoading}
            className="grid h-8 w-8 place-items-center rounded-md transition-colors disabled:opacity-40"
            style={{ background: "#2563EB", color: "#F5F5F5" }}
          >
            {isLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <ArrowUp size={16} />
            )}
          </button>
        </form>
      </div>
    </section>
  );
}

function MessageRow({
  message,
  expanded,
  onToggle,
  onSend,
  totalMessages,
}: {
  message: ChatMessage;
  expanded: boolean;
  onToggle: () => void;
  onSend: (t: string) => void;
  totalMessages: number;
}) {
  if (message.role === "user") {
    return (
      <div className="flex flex-col items-end">
        <div className="readable-muted text-[10px]">
          {message.time}
        </div>
        <div className="glass max-w-[85%] rounded-2xl px-4 py-2 text-right text-sm readable-text">
          {message.text}
        </div>
      </div>
    );
  }

  if (message.is_job_query) {
    return (
      <div className="flex max-w-[88%] flex-col gap-3">
        <div className="glass rounded-2xl p-5 border" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
          <div className="flex items-center gap-2 text-[10px] readable-muted mb-3">
            <MeshOrb size={14} />
            <span className="readable-text" style={{ fontWeight: 600 }}>KaStack</span>
            <span>·</span>
            <span>{message.time}</span>
          </div>
          <div className="readable-text text-[13px] leading-relaxed whitespace-pre-wrap">
            {message.text}
          </div>
          
          {message.jobsFound && message.jobsFound.length > 0 && (
            <div className="border-t pt-4 mt-4" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
              <button
                onClick={onToggle}
                className="flex items-center gap-2 text-[12px] readable-muted transition-colors"
                onMouseEnter={e => e.currentTarget.style.color = "#FFF"}
                onMouseLeave={e => e.currentTarget.style.color = ""}
              >
                <span className="text-lg">{expanded ? "▾" : "▸"}</span> 
                View source messages &rarr;
              </button>
              
              {expanded && (
                <div className="mt-4 flex flex-col gap-2">
                  {message.jobsFound.map((j, i) => (
                    <SourceCard 
                      key={`${j.msg_id}-${i}`} 
                      source={{ 
                        id: String(j.msg_id), 
                        user: j.sender as "User 1" | "User 2", 
                        day: j.day, 
                        text: j.text, 
                        similarity: 1.0 
                      }} 
                      hideScore={true}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (message.no_results) {
    const bestMatch = message.sources?.[0]?.similarity ?? 0;
    const bestMatchPct = Math.round(bestMatch * 100);
    return (
      <div className="flex max-w-[88%] flex-col gap-3">
        <div className="glass rounded-2xl p-5 border" style={{ borderColor: "rgba(239, 68, 68, 0.2)", background: "rgba(239, 68, 68, 0.05)" }}>
          <div className="flex items-center gap-2 mb-2 font-semibold text-[14px]" style={{ color: "#F87171" }}>
            <span className="text-lg">⚠️</span> No relevant information found
          </div>
          <div className="readable-text text-[13px] leading-relaxed mb-4">
            I searched through all <strong>{totalMessages.toLocaleString()}</strong> messages but couldn't find a strong enough match to confidently answer your question. 
            The closest match had a similarity score of only <strong>{bestMatchPct}%</strong> (minimum 30% required).
          </div>
          
          <div className="flex flex-wrap gap-2">
            <div className="text-[11px] readable-muted w-full uppercase font-semibold tracking-wider mb-1">Suggested Queries</div>
            {["Jobs", "Locations", "Personality", "Topics"].map(q => (
              <button 
                key={q} 
                onClick={() => onSend(`What ${q.toLowerCase()} do they mention?`)}
                className="glass-pill px-3 py-1.5 rounded-full text-[12px] transition-colors"
                style={{ color: "#93C5FD", background: "rgba(255,255,255,0.05)" }}
                onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.1)"}
                onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="glass rounded-2xl p-4 border" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
            <button
              onClick={onToggle}
              className="flex items-center gap-2 text-[12px] readable-muted transition-colors"
              onMouseEnter={e => e.currentTarget.style.color = "#FFF"}
              onMouseLeave={e => e.currentTarget.style.color = ""}
            >
              <span className="text-lg">{expanded ? "▾" : "▸"}</span> 
              What the system found instead ({message.sources.length} items)
            </button>
            
            {expanded && (
              <div className="mt-3">
                <div className="text-[11px] readable-muted mb-3 italic">
                  Note: These contain overlapping words but do not answer your question directly.
                </div>
                <div className="flex flex-wrap gap-2">
                  {message.sources.map((s) => (
                    <SourceCard key={s.id} source={s} highlightLowScore />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  const dot = confidenceColor(message.confidence);
  const conf = message.confidence !== undefined ? Math.round(message.confidence * 100) : null;
  return (
    <div className="flex max-w-[88%] flex-col gap-2">
      <div
        className="glass rounded-2xl px-4 py-3"
      >
        <div className="flex items-center gap-2 text-[10px] readable-muted">
          <MeshOrb size={14} />
          <span className="readable-text" style={{ fontWeight: 600 }}>KaStack</span>
          <span
            className="inline-block h-1.5 w-1.5 rounded-full"
            style={{ background: dot }}
            aria-hidden
            title="Retrieval confidence"
          />
          <span>·</span>
          <span>{message.time}</span>
          {conf !== null && (
            <span
              className="ml-auto rounded-full px-1.5 py-0.5 font-mono text-[10px]"
              style={{ background: "#171717", color: dot, border: `1px solid ${dot}33` }}
              title="Retrieval confidence"
            >
              {conf}%
            </span>
          )}
        </div>
        <div className="readable-text mt-2 text-[14px] leading-relaxed">
          {message.text}
        </div>
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 border-t pt-2" style={{ borderColor: "rgba(255,255,255,0.1)" }}>
            <button
              onClick={onToggle}
              className="text-[12px] transition-colors"
              style={{ color: "#60A5FA" }}
            >
              {message.sources.length} sources {expanded ? "↑" : "→"}
            </button>
            {expanded && (
              <div className="mt-2 flex flex-wrap gap-2">
                {message.sources.map((s) => (
                  <SourceCard key={s.id} source={s} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function SourceCard({ source, highlightLowScore = false, hideScore = false }: { source: SourceMessage, highlightLowScore?: boolean, hideScore?: boolean }) {
  const pct = source.similarity * 100;
  let colorScore = "";
  if (highlightLowScore) {
    if (pct < 15) colorScore = "#F87171"; // red-400
    else if (pct < 30) colorScore = "#FBBF24"; // yellow-400
  }

  return (
    <div
      className="glass flex w-[260px] flex-col gap-1 rounded-xl p-3 transition-colors"
    >
      <div className="readable-muted flex items-center justify-between text-[11px]">
        <span>
          [{source.user} · Day {source.day}]
        </span>
        {!hideScore && (
          <span className="font-mono" style={{ color: colorScore }}>{source.similarity.toFixed(2)}</span>
        )}
      </div>
      <div className="readable-text line-clamp-3 text-[13px]">
        {source.text}
      </div>
    </div>
  );
}
