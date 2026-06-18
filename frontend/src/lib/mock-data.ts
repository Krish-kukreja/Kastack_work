/**
 * mock-data.ts → data-types.ts
 *
 * All TypeScript interfaces the UI components rely on.
 * Adapter functions transform raw API responses into these shapes.
 * No hardcoded data remains.
 */

import type {
  PersonaApiResponse,
  PersonaApiUser,
  TopicsApiResponse,
  TopicApiItem,
  ChatApiResponse,
  HealthApiResponse,
} from "./api";

// ── Core UI types ────────────────────────────────────────────────

export type UserKey = "user1" | "user2";

export interface Topic {
  id: string;
  title: string;
  messageCount: number;
  similarity: number;
}

export interface SourceMessage {
  id: string;
  user: "User 1" | "User 2";
  day: number;
  text: string;
  similarity: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  time: string;
  sources?: SourceMessage[];
  confidence?: number; // 0..1
  no_results?: boolean;
  is_job_query?: boolean;
  jobsFound?: { job: string; text: string; day: number; sender: string; msg_id: number }[];
}

export interface PersonaStats {
  messagesAnalyzed: number;
  avgLength: number;
  emojiRate: number; // percent
  questionRate: number; // percent
  capsRate: number; // percent
}

export interface PersonaFacts {
  jobs: { value: string; mentions: number }[];
  locations: { value: string; mentions: number }[];
  ages: { value: string; mentions: number }[];
  relationships: { value: string; mentions: number }[];
  pets: { value: string; mentions: number }[];
}

export interface Persona {
  label: string;
  stats: PersonaStats;
  traits: string[];
  activeTraits: string[];
  habits: { text: string; active: boolean }[];
  facts: PersonaFacts;
  topEmojis: { emoji: string; count: number }[];
}

// ── Helper ───────────────────────────────────────────────────────

export function nowTime(): string {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

const ALL_TRAITS = ["Funny", "Expressive", "Curious", "Enthusiastic", "Intense", "Formal", "Casual"];

// ── Adapter: persona API → Persona ──────────────────────────────

function toMentionList(
  raw: Record<string, number> | string[] | undefined
): { value: string; mentions: number }[] {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    return raw.map((v) => ({ value: String(v), mentions: 1 }));
  }
  return Object.entries(raw)
    .map(([value, mentions]) => ({ value, mentions }))
    .sort((a, b) => b.mentions - a.mentions);
}

function adaptPersonaUser(raw: PersonaApiUser, label: string): Persona {
  const style = raw.communication_style ?? {};
  const traits = raw.personality_traits ?? {};
  const facts = raw.personal_facts ?? {};
  const habits = raw.habits ?? {};
  const emojis = raw.top_emojis ?? {};

  // Determine active traits
  const activeTraits: string[] = [];
  for (const [key, val] of Object.entries(traits)) {
    const detected = typeof val === "boolean" ? val : (val as { detected?: boolean })?.detected;
    if (detected) {
      // Capitalise first letter
      activeTraits.push(key.charAt(0).toUpperCase() + key.slice(1));
    }
  }

  // Build habit list
  const habitList: { text: string; active: boolean }[] = [];
  const habitDescriptions: Record<string, string> = {
    late_sleeper: "Late sleeper (mentions staying up late)",
    early_bird: "Early bird (active in mornings)",
    brief_communicator: "Brief communicator (short messages)",
    verbose_communicator: "Verbose communicator (longer messages)",
    link_sharer: "Link sharer (shares URLs frequently)",
    heavy_emoji_user: "Heavy emoji user",
  };
  for (const [key, val] of Object.entries(habits)) {
    const isObj = typeof val === "object" && val !== null;
    const detected = isObj ? (val as { detected?: boolean }).detected ?? false : Boolean(val);
    habitList.push({
      text: habitDescriptions[key] ?? key.replace(/_/g, " "),
      active: detected,
    });
  }
  // Infer some habits from style if not already present
  if (!habits.brief_communicator && !habits.verbose_communicator) {
    if (style.avg_message_length < 30) {
      habitList.push({ text: "Brief communicator (short messages)", active: true });
    } else if (style.avg_message_length > 80) {
      habitList.push({ text: "Verbose communicator (longer messages)", active: true });
    }
  }
  if (habitList.length === 0) {
    // Fallback: generate from style stats
    if (style.emoji_usage_rate > 0.15) habitList.push({ text: "Heavy emoji user", active: true });
    if (style.question_rate > 0.2) habitList.push({ text: "Asks more questions than average", active: true });
  }

  // Top emojis
  const topEmojiList = Object.entries(emojis)
    .map(([emoji, count]) => ({ emoji, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  return {
    label,
    stats: {
      messagesAnalyzed: raw.total_messages_analyzed ?? 0,
      avgLength: Math.round(style.avg_message_length ?? 0),
      emojiRate: Math.round((style.emoji_usage_rate ?? 0) * 100),
      questionRate: Math.round((style.question_rate ?? 0) * 100),
      capsRate: Math.round((style.caps_rate ?? 0) * 100),
    },
    traits: ALL_TRAITS,
    activeTraits,
    habits: habitList,
    facts: {
      jobs: toMentionList(facts.job_mentions),
      locations: toMentionList(facts.location_mentions),
      ages: Array.isArray(facts.age_mentions)
        ? facts.age_mentions.map((a) => ({ value: String(a), mentions: 1 }))
        : [],
      relationships: toMentionList(facts.relationship_mentions),
      pets: toMentionList(facts.pet_mentions),
    },
    topEmojis: topEmojiList,
  };
}

export interface AdaptedPersonaData {
  personas: Record<UserKey, Persona>;
  totalConversations: number;
  totalMessages: number;
}

export function adaptPersonaResponse(raw: PersonaApiResponse): AdaptedPersonaData {
  return {
    personas: {
      user1: adaptPersonaUser(raw.persona_user_1, "User 1 Profile"),
      user2: adaptPersonaUser(raw.persona_user_2, "User 2 Profile"),
    },
    totalConversations: raw.meta?.total_conversations_analyzed ?? 0,
    totalMessages:
      (raw.meta?.total_messages_user_1 ?? 0) +
      (raw.meta?.total_messages_user_2 ?? 0),
  };
}

// ── Adapter: topics API → Topic[] ───────────────────────────────

export function adaptTopicsResponse(raw: TopicsApiResponse): Topic[] {
  return raw.topics.slice(0, 20).map((t: TopicApiItem) => ({
    id: `t${t.topic_id}`,
    title: t.summary
      ? t.summary.length > 50
        ? t.summary.slice(0, 47) + "…"
        : t.summary
      : `Topic ${t.topic_id} (Day ${t.start_day}–${t.end_day})`,
    messageCount: t.num_messages,
    similarity: 0,
  }));
}

// ── Adapter: chat API → ChatMessage ─────────────────────────────

export function adaptChatResponse(raw: ChatApiResponse): ChatMessage {
  const sources: SourceMessage[] = (raw.sources?.messages_used ?? []).map((m, i) => ({
    id: `s${m.msg_id ?? i}`,
    user: (m.sender?.includes("1") ? "User 1" : "User 2") as "User 1" | "User 2",
    day: m.day ?? 0,
    text: m.text ?? "",
    similarity: m.score ?? 0,
  }));

  // Also include topics as context, but ONLY if they have a summary
  const topicSources: SourceMessage[] = (raw.sources?.topics_used ?? [])
    .filter(t => !!t.summary)
    .map((t, i) => ({
      id: `st${t.id ?? i}`,
      user: "User 1" as const, // Topic summaries are generic
      day: 0,
      text: `[Topic] ${t.summary}`,
      similarity: t.score ?? 0,
    }));

  const allSources = [...sources, ...topicSources].sort((a, b) => b.similarity - a.similarity);

  const avgSim =
    allSources.length > 0
      ? allSources.reduce((sum, s) => sum + s.similarity, 0) / allSources.length
      : undefined;

  return {
    id: crypto.randomUUID(),
    role: "assistant",
    text: raw.answer || "",
    time: nowTime(),
    sources: allSources.length > 0 ? allSources : undefined,
    confidence: avgSim,
    no_results: raw.no_results,
    is_job_query: raw.is_job_query,
    jobsFound: raw.sources.jobs_found,
  };
}

// ── Adapter: health API → display stats ─────────────────────────

export function adaptHealthResponse(raw: HealthApiResponse) {
  return {
    ready: raw.ready,
    totalTopics: raw.total_topics,
    totalMessages: raw.total_messages,
    checkpointsLoaded: raw.checkpoints_loaded,
  };
}

// ── Fallback data (shown while loading) ─────────────────────────

export const FALLBACK_PERSONA: Persona = {
  label: "Loading…",
  stats: { messagesAnalyzed: 0, avgLength: 0, emojiRate: 0, questionRate: 0, capsRate: 0 },
  traits: ALL_TRAITS,
  activeTraits: [],
  habits: [],
  facts: { jobs: [], locations: [], ages: [], relationships: [], pets: [] },
  topEmojis: [],
};

export const FALLBACK_PERSONAS: Record<UserKey, Persona> = {
  user1: { ...FALLBACK_PERSONA, label: "User 1 Profile" },
  user2: { ...FALLBACK_PERSONA, label: "User 2 Profile" },
};
