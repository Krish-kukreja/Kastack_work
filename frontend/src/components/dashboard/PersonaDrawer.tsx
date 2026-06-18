import { useEffect } from "react";
import {
  X,
  Briefcase,
  MapPin,
  CalendarDays,
  Heart,
  Cat,
} from "lucide-react";
import type { Persona, UserKey } from "@/lib/mock-data";

interface Props {
  open: boolean;
  user: UserKey;
  onClose: () => void;
  personas: Record<UserKey, Persona>;
  totalConversations: number;
}

export function PersonaDrawer({ open, user, onClose, personas, totalConversations }: Props) {
  const persona = personas[user];

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  function download(kind: "json" | "md") {
    let content = "";
    let mime = "text/plain";
    let filename = `${user}-persona.${kind === "md" ? "md" : "json"}`;
    if (kind === "json") {
      content = JSON.stringify(persona, null, 2);
      mime = "application/json";
    } else {
      const lines = [
        `# ${persona.label}`,
        `Aggregate across ${totalConversations.toLocaleString()} conversations`,
        ``,
        `## Stats`,
        `- Messages analyzed: ${persona.stats.messagesAnalyzed}`,
        `- Avg length: ${persona.stats.avgLength}`,
        `- Emoji rate: ${persona.stats.emojiRate}%`,
        `- Question rate: ${persona.stats.questionRate}%`,
        `- Caps rate: ${persona.stats.capsRate}%`,
        ``,
        `## Active traits`,
        ...persona.activeTraits.map((t) => `- ${t}`),
        ``,
        `## Habits`,
        ...persona.habits.filter((h) => h.active).map((h) => `- ${h.text}`),
      ];
      content = lines.join("\n");
      mime = "text/markdown";
    }
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div
      className="fixed inset-0 z-40"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div className="absolute inset-0" style={{ background: "rgba(0,0,0,0.42)", backdropFilter: "blur(6px)" }} />
      <aside
        onClick={(e) => e.stopPropagation()}
        className="glass-strong absolute right-0 top-0 flex h-full w-[420px] flex-col border-l"
      >
        <header
          className="flex items-center justify-between border-b px-5 py-4"
          style={{ borderColor: "rgba(255,255,255,0.1)" }}
        >
          <div>
            <div className="readable-text text-[15px] font-semibold">
              {persona.label}
            </div>
            <div className="readable-muted text-[12px]">
              Aggregate persona across {totalConversations.toLocaleString()} conversations
            </div>
          </div>
          <button
            onClick={onClose}
            className="grid h-8 w-8 place-items-center rounded-md"
            style={{ color: "#E2E5EC" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-5">
          <Section title="Communication style">
            <Bar label="Avg length" value={persona.stats.avgLength} max={100} suffix=" chars" />
            <Bar label="Emoji rate" value={persona.stats.emojiRate} max={50} suffix="%" />
            <Bar label="Question rate" value={persona.stats.questionRate} max={50} suffix="%" />
            <Bar label="Caps usage" value={persona.stats.capsRate} max={50} suffix="%" />
          </Section>

          <Section title="Personality traits">
            <div className="grid grid-cols-2 gap-2">
              {persona.traits.map((t) => {
                const active = persona.activeTraits.includes(t);
                return (
                  <span
                    key={t}
                    className="rounded-full border px-3 py-1 text-center text-[12px]"
                    style={{
                      background: active ? "rgba(37,99,235,0.86)" : "rgba(16,16,22,0.76)",
                      borderColor: active ? "rgba(96,165,250,0.72)" : "rgba(255,255,255,0.12)",
                      color: active ? "#FFFFFF" : "#D4D7E0",
                    }}
                  >
                    {t}
                  </span>
                );
              })}
            </div>
          </Section>

          <Section title="Habits">
            <div className="readable-muted mb-2 text-[11px]">
              Detected from message content patterns
            </div>
            <ul className="flex flex-col gap-1.5">
              {persona.habits.length > 0 ? (
                persona.habits.map((h) => (
                  <li key={h.text} className="flex items-center gap-2 text-[13px]">
                    <span
                      className="grid h-4 w-4 place-items-center rounded text-[10px]"
                      style={{
                        background: h.active ? "#2563EB" : "transparent",
                        border: h.active ? "none" : "1px solid rgba(255,255,255,0.14)",
                        color: h.active ? "#F5F5F5" : "#AEB4C0",
                      }}
                    >
                      {h.active ? "✓" : "×"}
                    </span>
                    <span style={{ color: h.active ? "#F0F2F7" : "#AEB4C0" }}>{h.text}</span>
                  </li>
                ))
              ) : (
                <li className="readable-muted text-[13px]">No habits detected</li>
              )}
            </ul>
          </Section>

          <div className="mb-6 rounded-xl border p-4" style={{ borderColor: "rgba(245,158,11,0.2)", background: "rgba(245,158,11,0.05)" }}>
            <div className="mb-2 text-[13px] font-semibold" style={{ color: "#F59E0B" }}>
              ⚠️ Aggregate Profile
            </div>
            <div className="readable-muted text-[13px] leading-relaxed">
              This is an aggregate profile across 11,000 anonymized conversations. Each conversation features different individuals. Personal facts (jobs, locations, ages, relationships, pets) cannot be attributed to one person and are not shown.
            </div>
          </div>

          <Section title="Top expressions">
            <div className="grid grid-cols-5 gap-2">
              {persona.topEmojis.length > 0 ? (
                persona.topEmojis.map((e, idx) => {
                  const hue = [340, 200, 30, 270, 160][idx % 5];
                  return (
                    <div key={e.emoji} className="flex flex-col items-center gap-1.5">
                      <div
                        className="grid h-9 w-9 place-items-center rounded-full text-[11px] font-semibold"
                        style={{
                          background: `hsla(${hue}, 70%, 55%, 0.18)`,
                          border: `1px solid hsla(${hue}, 70%, 55%, 0.35)`,
                          color: `hsla(${hue}, 80%, 72%, 1)`,
                        }}
                      >
                        {e.count}
                      </div>
                      <div className="readable-muted text-[11px]">
                        {e.emoji}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="col-span-5 readable-muted text-[12px]">No emoji data available</div>
              )}
            </div>
          </Section>

          <div className="readable-muted mt-6 text-[11px] italic">
            All signals derived from message statistics and regex patterns. No LLM inference used.
          </div>
        </div>

        <footer
          className="flex items-center gap-2 border-t px-5 py-4"
          style={{ borderColor: "rgba(255,255,255,0.1)" }}
        >
          <button
            onClick={() => download("json")}
            className="rounded-md border px-3 py-1.5 text-[12px]"
            style={{ borderColor: "rgba(255,255,255,0.14)", color: "#E2E5EC" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            Export as JSON
          </button>
          <button
            onClick={() => download("md")}
            className="rounded-md border px-3 py-1.5 text-[12px]"
            style={{ borderColor: "rgba(255,255,255,0.14)", color: "#E2E5EC" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            Export as Markdown
          </button>
        </footer>
      </aside>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      <div
        className="readable-muted mb-3 text-[11px] font-semibold uppercase"
        style={{ letterSpacing: "0.05em" }}
      >
        {title}
      </div>
      {children}
    </section>
  );
}

function Bar({
  label,
  value,
  max,
  suffix,
}: {
  label: string;
  value: number;
  max: number;
  suffix?: string;
}) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div className="mb-3">
      <div className="mb-1 flex items-center justify-between text-[12px]">
        <span className="readable-text">{label}</span>
        <span className="readable-muted">
          {value}
          {suffix}
        </span>
      </div>
      <div className="h-1 w-full overflow-hidden rounded-sm" style={{ background: "rgba(255,255,255,0.12)" }}>
        <div className="h-full rounded-sm" style={{ width: `${pct}%`, background: "#2563EB" }} />
      </div>
    </div>
  );
}

function FactGroup({
  icon,
  label,
  items,
}: {
  icon: React.ReactNode;
  label: string;
  items: { value: string; mentions: number }[];
}) {
  if (items.length === 0) return null;
  const total = items.reduce((sum, i) => sum + i.mentions, 0);
  return (
    <div className="readable-text mb-3 text-[13px]">
      <span>{icon} </span>
      <span className="font-semibold">
        {label}:
      </span>{" "}
      {items.map((i) => i.value).join(", ")}{" "}
      <span className="readable-muted">({total} mentions)</span>
    </div>
  );
}
