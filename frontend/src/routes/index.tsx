import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { NavBar, type NavKey } from "@/components/dashboard/NavBar";
import { MeshBackground } from "@/components/ui/mesh-orb";
import { ChatArea } from "@/components/dashboard/ChatArea";
import { ContextPanel } from "@/components/dashboard/ContextPanel";
import { PersonaDrawer } from "@/components/dashboard/PersonaDrawer";
import { SearchOverlay } from "@/components/dashboard/SearchOverlay";
import { ShortcutsOverlay } from "@/components/dashboard/ShortcutsOverlay";
import { Toast, useToast } from "@/components/dashboard/Toast";
import { usePersonas, useTopics, useChatMutation, useHealth } from "@/hooks/use-api";
import {
  nowTime,
  type ChatMessage,
  type Topic,
  type UserKey,
} from "@/lib/mock-data";

export const Route = createFileRoute("/")(
  {
  head: () => ({
    meta: [
      { title: "KaStack RAG — Conversation Intelligence" },
      {
        name: "description",
        content: "Analyze 11,000 conversations: topics, personas, and retrieved sources.",
      },
    ],
  }),
  component: Dashboard,
});

type ContextTab = "topics" | "persona" | "sources";

function Dashboard() {
  const [nav, setNav] = useState<NavKey>("chat");
  const [navExpanded, setNavExpanded] = useState(false);
  const [activeUser, setActiveUser] = useState<UserKey>("user1");
  const [activeTopic, setActiveTopic] = useState<Topic | null>(null);
  const [tab, setTab] = useState<ContextTab>("topics");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const toast = useToast();

  // ── Live data from backend ──────────────────────────────────
  const { personas, totalConversations, totalMessages, isLoading: personaLoading } = usePersonas();
  const { data: topics = [], isLoading: topicsLoading } = useTopics();
  const { data: health } = useHealth();
  const chatMutation = useChatMutation();

  const lastAssistant = useMemo(
    () => [...messages].reverse().find((m) => m.role === "assistant") ?? null,
    [messages]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      // Add user message immediately
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        text,
        time: nowTime(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setTab("sources");

      try {
        // Call the real backend
        const aiMsg = await chatMutation.mutateAsync({ 
          message: text, 
          targetUser: activeUser === "user1" ? "User 1" : "User 2",
          targetTopic: activeTopic?.id
        });
        setMessages((prev) => [...prev, aiMsg]);
      } catch (err) {
        // Add error message
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          text: `Sorry, I encountered an error: ${err instanceof Error ? err.message : "Unknown error"}. Make sure the backend is running on port 8000.`,
          time: nowTime(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    },
    [chatMutation]
  );

  const handleUserChange = useCallback(
    (u: UserKey) => {
      if (u === activeUser) return;
      setActiveUser(u);
      toast.show(`Now viewing ${u === "user1" ? "User 1" : "User 2"} profile`);
    },
    [activeUser, toast]
  );

  const handleNav = useCallback((k: NavKey) => {
    setNav(k);
    setSearchOpen(false);
    setDrawerOpen(false);
    setShortcutsOpen(false);
    if (k === "search") setSearchOpen(true);
    else if (k === "persona") setDrawerOpen(true);
    else if (k === "settings") setShortcutsOpen(true);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      const typing = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA");
      if (e.key === "Escape") {
        setSearchOpen(false);
        setShortcutsOpen(false);
        setDrawerOpen(false);
        setNav("chat");
        return;
      }
      if (typing) return;
      if (e.key === "/") {
        e.preventDefault();
        setSearchOpen(true);
      } else if (e.key === "?") {
        e.preventDefault();
        setShortcutsOpen((v) => !v);
      } else if (e.key === "1") {
        handleUserChange("user1");
      } else if (e.key === "2") {
        handleUserChange("user2");
      } else if (e.key === "t") {
        setTab("topics");
      } else if (e.key === "p") {
        setTab("persona");
      } else if (e.key === "s") {
        setTab("sources");
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleUserChange]);

  const isDataLoading = personaLoading || topicsLoading;

  return (
    <div className="relative flex h-screen w-screen overflow-hidden" style={{ background: "#050505" }}>
      <MeshBackground opacity={0.45} />
      <div className="relative z-10 flex h-full w-full">
      <NavBar
        active={nav}
        onSelect={handleNav}
        expanded={navExpanded}
        onToggle={() => setNavExpanded((v) => !v)}
      />
      <ChatArea
        activeUser={activeUser}
        onUserChange={handleUserChange}
        messages={
          activeTopic
            ? messages.filter((m) => m.role === "user" || (m.sources?.length ?? 0) > 0)
            : messages
        }
        onSend={sendMessage}
        activeTopic={activeTopic}
        onSelectTopic={(t) => {
          setActiveTopic(t);
          if (t) {
            setTab("topics");
            toast.show(`Filtering by "${t.title}" · ${t.messageCount.toLocaleString()} messages`);
          }
        }}
        topics={topics}
        totalMessages={totalMessages}
        isLoading={chatMutation.isPending}
        backendReady={health?.ready ?? false}
      />
      <ContextPanel
        activeUser={activeUser}
        activeTopic={activeTopic}
        onSelectTopic={(t) => setActiveTopic(t)}
        lastAssistant={lastAssistant}
        onOpenPersona={() => setDrawerOpen(true)}
        tab={tab}
        onTabChange={setTab}
        personas={personas}
        topics={topics}
        totalConversations={totalConversations}
        totalMessages={totalMessages}
        isLoading={isDataLoading}
      />

      <PersonaDrawer
        open={drawerOpen}
        user={activeUser}
        onClose={() => {
          setDrawerOpen(false);
          setNav("chat");
        }}
        personas={personas}
        totalConversations={totalConversations}
      />
      <SearchOverlay
        open={searchOpen}
        onClose={() => {
          setSearchOpen(false);
          setNav("chat");
        }}
        topics={topics}
        personas={personas}
        totalMessages={totalMessages}
      />
      <ShortcutsOverlay
        open={shortcutsOpen}
        onClose={() => {
          setShortcutsOpen(false);
          setNav("chat");
        }}
      />
      <Toast msg={toast.msg} />

      {/* Suppress unused topics warning by exporting nothing; kept for parity */}
      <span hidden>{topics.length}</span>
      </div>
    </div>
  );
}
