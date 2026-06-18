/**
 * use-api.ts — React Query hooks for the Kastack backend.
 *
 * Each hook fetches from the FastAPI backend and transforms the
 * response into the shapes the UI components expect.
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchHealth, fetchPersona, fetchTopics, fetchChat } from "@/lib/api";
import {
  adaptPersonaResponse,
  adaptTopicsResponse,
  adaptChatResponse,
  adaptHealthResponse,
  FALLBACK_PERSONAS,
  type AdaptedPersonaData,
  type Topic,
  type ChatMessage,
} from "@/lib/mock-data";

// ── Health ──────────────────────────────────────────────────────

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const raw = await fetchHealth();
      return adaptHealthResponse(raw);
    },
    refetchInterval: 10_000, // poll every 10s
    retry: 2,
  });
}

// ── Persona ─────────────────────────────────────────────────────

export function usePersona() {
  return useQuery({
    queryKey: ["persona"],
    queryFn: async (): Promise<AdaptedPersonaData> => {
      const raw = await fetchPersona();
      return adaptPersonaResponse(raw);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

/** Convenience: returns personas record, with fallbacks while loading */
export function usePersonas() {
  const { data, isLoading, error } = usePersona();
  return {
    personas: data?.personas ?? FALLBACK_PERSONAS,
    totalConversations: data?.totalConversations ?? 0,
    totalMessages: data?.totalMessages ?? 0,
    isLoading,
    error,
  };
}

// ── Topics ──────────────────────────────────────────────────────

export function useTopics() {
  return useQuery({
    queryKey: ["topics"],
    queryFn: async (): Promise<Topic[]> => {
      const raw = await fetchTopics();
      return adaptTopicsResponse(raw);
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

// ── Chat mutation ───────────────────────────────────────────────

export function useChatMutation() {
  return useMutation({
    mutationFn: async ({ message, targetUser, targetTopic }: { message: string, targetUser?: string, targetTopic?: string }): Promise<ChatMessage> => {
      const raw = await fetchChat(message, targetUser, targetTopic);
      return adaptChatResponse(raw);
    },
  });
}
