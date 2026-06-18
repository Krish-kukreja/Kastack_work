import type { ChatMessage, Persona, Topic, UserKey } from "@/lib/mock-data";
import { SourceCard } from "./ChatArea";

type Tab = "topics" | "persona" | "sources";

interface Props {
  activeUser: UserKey;
  activeTopic: Topic | null;
  onSelectTopic: (t: Topic | null) => void;
  lastAssistant: ChatMessage | null;
  onOpenPersona: () => void;
  tab: Tab;
  onTabChange: (t: Tab) => void;
  personas: Record<UserKey, Persona>;
  topics: Topic[];
  totalConversations: number;
  totalMessages: number;
  isLoading?: boolean;
}

export function ContextPanel({
  activeUser,
  activeTopic,
  onSelectTopic,
  lastAssistant,
  onOpenPersona,
  tab,
  onTabChange,
  personas,
  topics,
  totalConversations,
  totalMessages,
  isLoading = false,
}: Props) {
  const persona = personas[activeUser];

  return (
    <aside
      className="glass hidden w-[320px] shrink-0 flex-col border-l md:flex"
      style={{ borderColor: "rgba(255,255,255,0.12)" }}
    >
      <div className="flex items-center gap-4 border-b px-4" style={{ borderColor: "rgba(255,255,255,0.1)" }}>
        {(["topics", "persona", "sources"] as Tab[]).map((t) => {
          const active = tab === t;
          return (
            <button
              key={t}
              onClick={() => onTabChange(t)}
              className="relative py-3 text-[13px] font-medium capitalize transition-colors"
              style={{
                color: active ? "#FFFFFF" : "#AEB4C0",
              }}
            >
              {t}
              {active && (
                <span
                  className="absolute inset-x-0 -bottom-px h-0.5"
                  style={{ background: "#2563EB" }}
                />
              )}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {tab === "topics" && (
          <TopicsTab activeTopic={activeTopic} onSelectTopic={onSelectTopic} topics={topics} isLoading={isLoading} />
        )}
        {tab === "persona" && (
          <PersonaTab persona={persona} totalConversations={totalConversations} onOpenFull={onOpenPersona} isLoading={isLoading} />
        )}
        {tab === "sources" && <SourcesTab lastAssistant={lastAssistant} />}
      </div>

      {tab === "persona" && (
        <div className="border-t p-4" style={{ borderColor: "rgba(255,255,255,0.1)" }}>
          <div className="readable-muted mb-2 text-[11px]">
            Aggregate across {totalConversations.toLocaleString()} conversations · {persona.stats.messagesAnalyzed.toLocaleString()} messages
          </div>
          <button
            onClick={onOpenPersona}
            className="w-full rounded-md border px-4 py-2 text-[13px] transition-colors"
            style={{ borderColor: "rgba(255,255,255,0.12)", color: "#F5F5F5", background: "rgba(14,14,18,0.7)", backdropFilter: "blur(12px)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(14,14,18,0.7)")}
          >
            View full profile →
          </button>
        </div>
      )}
    </aside>
  );
}

function TopicsTab({
  activeTopic,
  onSelectTopic,
  topics,
  isLoading,
}: {
  activeTopic: Topic | null;
  onSelectTopic: (t: Topic | null) => void;
  topics: Topic[];
  isLoading: boolean;
}) {
  return (
    <div>
      <div className="readable-muted mb-3 text-[12px]">
        {isLoading
          ? "Loading topics from backend…"
          : activeTopic
            ? "Filtering by topic. Click again or 'Clear' to reset."
            : `${topics.length} topics detected. Click one to filter messages.`}
      </div>
      <div className="flex flex-col gap-2">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="shimmer h-20 rounded-xl" />
          ))
        ) : (
          topics.map((t) => {
            const isActive = activeTopic?.id === t.id;
            return (
              <button
                key={t.id}
                onClick={() => onSelectTopic(isActive ? null : t)}
                className="glass rounded-xl p-4 text-left transition-colors"
                style={{
                  borderColor: isActive ? "rgba(96,165,250,0.8)" : undefined,
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="readable-text text-[14px] font-semibold">
                    {t.title}
                  </div>
                  <div className="readable-muted font-mono text-[12px]">
                    {t.similarity > 0 ? t.similarity.toFixed(2) : ""}
                  </div>
                </div>
                <div className="readable-muted mt-1 text-[12px]">
                  {t.messageCount.toLocaleString()} messages
                </div>
              </button>
            );
          })
        )}
        {activeTopic && (
          <button
            onClick={() => onSelectTopic(null)}
            className="self-start text-[12px]"
            style={{ color: "#2563EB" }}
          >
            Clear filter
          </button>
        )}
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="readable-muted mb-2 text-[11px] font-semibold uppercase"
      style={{ letterSpacing: "0.05em" }}
    >
      {children}
    </div>
  );
}

function PersonaTab({ persona, totalConversations, onOpenFull: _, isLoading }: { persona: Persona; totalConversations: number; onOpenFull: () => void; isLoading: boolean }) {
  const { stats, activeTraits, habits, facts } = persona;

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="shimmer h-14 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="readable-text text-[14px] font-semibold">
          {persona.label}
        </div>
        <div className="readable-muted text-[12px]">
          Aggregate across {totalConversations.toLocaleString()} conversations
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Stat n={stats.messagesAnalyzed.toLocaleString()} label="Messages analyzed" />
        <Stat n={String(stats.avgLength)} label="Avg length (chars)" />
        <Stat n={`${stats.emojiRate}%`} label="Emoji rate" />
        <Stat n={`${stats.questionRate}%`} label="Question rate" />
      </div>

      <div>
        <SectionLabel>Traits</SectionLabel>
        <ul className="flex flex-col gap-1">
          {activeTraits.length > 0 ? (
            activeTraits.map((t) => (
              <li key={t} className="readable-text text-[14px]">
                • {traitDescription(t)}
              </li>
            ))
          ) : (
            <li className="readable-muted text-[13px]">No strong traits detected</li>
          )}
        </ul>
      </div>

      <div className="rounded-xl border p-4" style={{ borderColor: "rgba(245,158,11,0.2)", background: "rgba(245,158,11,0.05)" }}>
        <div className="mb-2 text-[13px] font-semibold" style={{ color: "#F59E0B" }}>
          ⚠️ Aggregate Profile
        </div>
        <div className="readable-muted text-[12px] leading-relaxed">
          This is an aggregate profile across 11,000 anonymized conversations. Each conversation features different individuals. Personal facts (jobs, locations, ages, relationships, pets) cannot be attributed to one person and are not shown.
        </div>
      </div>

      <div>
        <SectionLabel>Habits</SectionLabel>
        <ul className="readable-text flex flex-col gap-1 text-[14px]">
          {habits.filter((h) => h.active).length > 0 ? (
            habits.filter((h) => h.active).map((h) => (
              <li key={h.text}>• {h.text}</li>
            ))
          ) : (
            <li className="readable-muted">No distinct habits detected</li>
          )}
        </ul>
      </div>
    </div>
  );
}

function Stat({ n, label }: { n: string; label: string }) {
  return (
    <div className="glass rounded-xl p-3">
      <div className="readable-text text-[20px] font-semibold">
        {n}
      </div>
      <div className="readable-muted text-[11px]">
        {label}
      </div>
    </div>
  );
}

function traitDescription(t: string): string {
  const map: Record<string, string> = {
    Funny: "Tends toward humor and jokes",
    Expressive: "Uses emoji and emphatic language",
    Curious: "Asks follow-up questions frequently",
    Enthusiastic: "High-energy responses",
    Intense: "Detailed, focused replies",
    Formal: "Uses complete sentences and punctuation",
    Casual: "Lowercase, abbreviations, slang",
  };
  return map[t] ?? t;
}

function SourcesTab({ lastAssistant }: { lastAssistant: ChatMessage | null }) {
  if (!lastAssistant || !lastAssistant.sources || lastAssistant.sources.length === 0) {
    return (
      <div className="glass readable-muted rounded-xl p-4 text-[13px]">
        Ask a question to see retrieved sources.
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {lastAssistant.sources.map((s) => (
        <SourceCard key={s.id} source={s} />
      ))}
    </div>
  );
}
