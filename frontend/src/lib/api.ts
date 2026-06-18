/**
 * api.ts — Centralized API client for the Kastack FastAPI backend.
 *
 * All fetch calls to the backend go through here so the base URL
 * and error handling are in one place.
 */

export const API_BASE_URL =
  (typeof window !== "undefined" && (window as Record<string, unknown>).__KASTACK_API_URL__) as string
  || (import.meta.env?.PROD ? "" : "http://localhost:8000");

// ── Backend response shapes ────────────────────────────────────────

/** POST /chat response */
export interface ChatApiResponse {
  query: string;
  answer: string;
  sources: {
    topics_used: {
      id: number;
      range: string;
      summary: string;
      score: number;
    }[];
    checkpoints_used?: {
      id: number;
      range: string;
      summary: string;
      score: number;
    }[];
    messages_used: {
      msg_id: number;
      text: string;
      sender: string;
      day: number;
      score: number;
    }[];
    jobs_found?: {
      job: string;
      text: string;
      day: number;
      sender: string;
      msg_id: number;
    }[];
  };
  is_persona_query: boolean;
  is_job_query?: boolean;
  no_results?: boolean;
}

/** GET /persona response — entire persona.json */
export interface PersonaApiResponse {
  meta: {
    total_messages: number;
    total_messages_user_1: number;
    total_messages_user_2: number;
    total_conversations_analyzed: number;
    data_description: string;
    [key: string]: unknown;
  };
  persona_user_1: PersonaApiUser;
  persona_user_2: PersonaApiUser;
}

export interface PersonaApiUser {
  total_messages_analyzed: number;
  communication_style: {
    avg_message_length: number;
    emoji_usage_rate: number;
    question_rate: number;
    exclamation_rate: number;
    caps_rate?: number;
    [key: string]: unknown;
  };
  personality_traits: Record<string, boolean | { detected: boolean; evidence_count?: number }>;
  personal_facts: {
    job_mentions: Record<string, number> | string[];
    location_mentions: Record<string, number> | string[];
    age_mentions?: (number | string)[];
    pet_mentions?: Record<string, number>;
    relationship_mentions?: Record<string, number>;
    [key: string]: unknown;
  };
  habits?: Record<string, unknown>;
  top_emojis?: Record<string, number>;
}

/** GET /topics response */
export interface TopicsApiResponse {
  total: number;
  topics: TopicApiItem[];
}

export interface TopicApiItem {
  topic_id: number;
  start_msg_id: number;
  end_msg_id: number;
  start_day: number;
  end_day: number;
  num_messages: number;
  summary?: string;
  dominant_sender?: string;
  [key: string]: unknown;
}

/** GET /health response */
export interface HealthApiResponse {
  status: string;
  ready: boolean;
  total_topics: number;
  total_messages: number;
  checkpoints_loaded: number;
}

// ── Fetch helpers ──────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function fetchHealth(): Promise<HealthApiResponse> {
  return apiFetch<HealthApiResponse>("/health");
}

export function fetchPersona(): Promise<PersonaApiResponse> {
  return apiFetch<PersonaApiResponse>("/persona");
}

export function fetchTopics(): Promise<TopicsApiResponse> {
  return apiFetch<TopicsApiResponse>("/topics");
}

export function fetchChat(message: string, target_user?: string, target_topic?: string): Promise<ChatApiResponse> {
  return apiFetch<ChatApiResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, target_user, target_topic }),
  });
}
