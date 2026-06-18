import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search as SearchIcon, CornerDownLeft } from "lucide-react";
import type { Persona, Topic, UserKey } from "@/lib/mock-data";

interface Props {
  open: boolean;
  onClose: () => void;
  topics: Topic[];
  personas: Record<UserKey, Persona>;
  totalMessages: number;
}

const ROTATING = ["topics", "personas", "facts", "moments", "messages"];

export function SearchOverlay({ open, onClose, topics, personas, totalMessages }: Props) {
  const [q, setQ] = useState("");
  const [rot, setRot] = useState(0);
  const ref = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQ("");
      setTimeout(() => ref.current?.focus(), 10);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const id = setInterval(() => setRot((r) => (r + 1) % ROTATING.length), 2200);
    return () => clearInterval(id);
  }, [open]);

  const query = q.toLowerCase().trim();
  const matchedTopics = useMemo(
    () => topics.filter((t) => t.title.toLowerCase().includes(query)),
    [query, topics]
  );
  const facts = useMemo(
    () => [
      ...personas.user1.facts.jobs.map((j) => ({ type: "Job · User 1", value: j.value })),
      ...personas.user1.facts.locations.map((j) => ({ type: "Location · User 1", value: j.value })),
      ...personas.user2.facts.jobs.map((j) => ({ type: "Job · User 2", value: j.value })),
      ...personas.user2.facts.locations.map((j) => ({ type: "Location · User 2", value: j.value })),
    ],
    [personas]
  );
  const matchedFacts = query ? facts.filter((f) => f.value.toLowerCase().includes(query)) : [];

  if (!open) return null;

  return (
    <div
      className="fixed inset-y-0 right-0 z-40 flex items-start justify-center pt-24"
      style={{
        left: 48,
        background: "rgba(0,0,0,0.35)",
        backdropFilter: "blur(6px)",
      }}
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className="glass-strong mx-4 w-full max-w-2xl overflow-hidden rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Animated headline */}
        <div className="px-5 pt-5">
          <div className="readable-muted text-[11px] uppercase tracking-[0.14em]">
            KaStack · Search
          </div>
          <div className="readable-text mt-1 flex flex-wrap items-baseline gap-x-2 text-[22px] font-semibold tracking-tight">
            <span>Look across</span>
            <span className="relative inline-flex h-[28px] min-w-[120px] overflow-hidden">
              <AnimatePresence mode="wait">
                <motion.span
                  key={ROTATING[rot]}
                  initial={{ y: 24, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -24, opacity: 0 }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  className="absolute"
                  style={{ color: "#2563EB" }}
                >
                  {ROTATING[rot]}
                </motion.span>
              </AnimatePresence>
            </span>
          </div>
          <div className="readable-muted mt-1 text-[12px]">
            {totalMessages.toLocaleString()} messages indexed · {topics.length} topics detected
          </div>
        </div>

        {/* Input */}
        <div
          className="glass mx-5 mt-4 flex items-center gap-2 rounded-xl px-3"
        >
          <SearchIcon size={15} style={{ color: "#B7BBC6" }} />
          <input
            ref={ref}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Escape" && onClose()}
            placeholder="Search topics, personas, facts…"
            className="flex-1 bg-transparent py-3 text-[15px] outline-none placeholder:text-[#B7BBC6]"
            style={{ color: "#F7F7FA" }}
          />
          <kbd
            className="rounded border px-1.5 py-0.5 font-mono text-[10px]"
            style={{ borderColor: "rgba(255,255,255,0.16)", color: "#D4D7E0", background: "rgba(0,0,0,0.3)" }}
          >
            Esc
          </kbd>
        </div>

        {/* Results */}
        <div className="mt-3 max-h-[50vh] overflow-y-auto pb-3">
          {query ? (
            <>
              <Group label="Topics">
                {matchedTopics.length === 0 ? (
                  <Empty />
                ) : (
                  matchedTopics.map((t) => (
                    <Row key={t.id} primary={t.title} secondary={`${t.messageCount} messages`} />
                  ))
                )}
              </Group>
              <Group label="Facts">
                {matchedFacts.length === 0 ? (
                  <Empty />
                ) : (
                  matchedFacts.slice(0, 6).map((f, i) => (
                    <Row key={i} primary={f.value} secondary={f.type} />
                  ))
                )}
              </Group>
            </>
          ) : (
            <Group label="Suggested">
              {topics.slice(0, 4).map((t) => (
                <Row key={t.id} primary={t.title} secondary={`${t.messageCount} messages`} />
              ))}
            </Group>
          )}
        </div>

        <div
          className="flex items-center justify-between border-t px-5 py-2 text-[11px]"
          style={{ borderColor: "rgba(255,255,255,0.1)", color: "#B7BBC6" }}
        >
          <span>Press / to open search anywhere</span>
          <span className="inline-flex items-center gap-1">
            <CornerDownLeft size={11} /> to jump
          </span>
        </div>
      </motion.div>
    </div>
  );
}

function Group({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="px-2 py-1">
      <div className="readable-muted px-3 pb-1 pt-2 text-[10px] uppercase" style={{ letterSpacing: "0.08em" }}>
        {label}
      </div>
      {children}
    </div>
  );
}

function Row({ primary, secondary }: { primary: string; secondary: string }) {
  return (
    <button
      className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-[13px] transition-colors"
      style={{ color: "#DCE0EA" }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
    >
      <span className="readable-text">{primary}</span>
      <span className="readable-muted">{secondary}</span>
    </button>
  );
}

function Empty() {
  return (
    <div className="readable-muted px-3 py-2 text-[12px]">
      No matches.
    </div>
  );
}
