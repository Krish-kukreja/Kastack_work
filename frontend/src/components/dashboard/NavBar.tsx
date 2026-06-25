import { MessageSquare, Search, User, Settings, Activity } from "lucide-react";
import { MeshOrb } from "@/components/ui/mesh-orb";

export type NavKey = "chat" | "search" | "persona" | "settings" | "insights";

interface Props {
  active: NavKey;
  onSelect: (k: NavKey) => void;
  expanded: boolean;
  onToggle: () => void;
}

const items: { key: NavKey; icon: typeof MessageSquare; label: string; hint: string }[] = [
  { key: "chat", icon: MessageSquare, label: "Chat", hint: "Chat" },
  { key: "search", icon: Search, label: "Search", hint: "Search (/)" },
  { key: "persona", icon: User, label: "Profiles", hint: "Profiles" },
  { key: "insights", icon: Activity, label: "Insights", hint: "Insights" },
  { key: "settings", icon: Settings, label: "Settings", hint: "Settings" },
];

export function NavBar({ active, onSelect, expanded, onToggle }: Props) {
  return (
    <nav
      className="relative z-50 flex shrink-0 flex-col gap-1 border-r py-3 transition-[width] duration-200 ease-out"
      style={{
        background: "rgba(8,8,12,0.38)",
        borderColor: "rgba(255,255,255,0.1)",
        backdropFilter: "blur(18px)",
        width: expanded ? 200 : 48,
      }}
      aria-label="Primary"
    >
      {/* Brain toggle */}
      <button
        onClick={onToggle}
        title={expanded ? "Collapse menu" : "Expand menu"}
        aria-label="Toggle menu"
        aria-expanded={expanded}
        className="mx-1.5 mb-2 flex h-9 items-center gap-3 rounded-md px-2 transition-colors duration-150"
        style={{ color: "#F5F5F5", background: "transparent" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <MeshOrb size={22} />
        {expanded && (
          <span className="truncate text-[13px] font-semibold tracking-tight">KaStack</span>
        )}
      </button>

      <div className="mx-2 mb-2 h-px" style={{ background: "rgba(255,255,255,0.1)" }} />

      {items.map(({ key, icon: Icon, label, hint }) => {
        const isActive = active === key;
        return (
          <button
            key={key}
            onClick={() => onSelect(key)}
            title={expanded ? undefined : hint}
            aria-label={label}
            aria-current={isActive ? "page" : undefined}
            className="mx-1.5 flex h-9 items-center gap-3 rounded-md px-2 transition-colors duration-150"
            style={{
              color: isActive ? "#F5F5F5" : "#C8CDD8",
              background: isActive ? "rgba(255,255,255,0.12)" : "transparent",
            }}
            onMouseEnter={(e) => {
              if (!isActive) (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.08)";
            }}
            onMouseLeave={(e) => {
              if (!isActive) (e.currentTarget as HTMLButtonElement).style.background = "transparent";
            }}
          >
            <Icon size={18} strokeWidth={1.75} className="shrink-0" />
            {expanded && <span className="truncate text-[13px]">{label}</span>}
          </button>
        );
      })}
    </nav>
  );
}

export type { NavKey };
