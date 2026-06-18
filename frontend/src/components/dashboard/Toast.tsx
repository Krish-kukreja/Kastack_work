import { useEffect, useState } from "react";

export function useToast() {
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    if (!msg) return;
    const t = setTimeout(() => setMsg(null), 2200);
    return () => clearTimeout(t);
  }, [msg]);
  return { msg, show: setMsg };
}

export function Toast({ msg }: { msg: string | null }) {
  if (!msg) return null;
  return (
    <div
      className="glass-strong readable-text fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-xl px-4 py-2 text-[13px]"
    >
      {msg}
    </div>
  );
}
