interface Props {
  open: boolean;
  onClose: () => void;
}

const SHORTCUTS: [string, string][] = [
  ["/", "Focus search"],
  ["1", "Switch to User 1"],
  ["2", "Switch to User 2"],
  ["t", "Topics tab"],
  ["p", "Persona tab"],
  ["s", "Sources tab"],
  ["?", "Toggle this overlay"],
  ["Esc", "Close any overlay"],
];

export function ShortcutsOverlay({ open, onClose }: Props) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.35)", backdropFilter: "blur(6px)" }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="glass-strong w-full max-w-md rounded-2xl p-5"
      >
        <div className="mb-4 text-[14px] font-medium" style={{ color: "#F5F5F5" }}>
          Keyboard shortcuts
        </div>
        <ul className="flex flex-col gap-1.5">
          {SHORTCUTS.map(([key, desc]) => (
            <li key={key} className="flex items-center justify-between text-[13px]">
              <span className="readable-text">{desc}</span>
              <kbd
                className="rounded border px-2 py-0.5 font-mono text-[11px]"
                style={{ borderColor: "rgba(255,255,255,0.14)", color: "#E2E5EC", background: "rgba(0,0,0,0.35)" }}
              >
                {key}
              </kbd>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
