import { MeshGradient } from "@paper-design/shaders-react";

interface MeshOrbProps {
  size?: number;
  className?: string;
  speed?: number;
  rounded?: boolean;
}

const ORB_COLORS = ["#FFB3D9", "#87CEEB", "#4A90E2", "#2C3E50", "#1A1A2E"];

/**
 * Compact animated mesh-gradient orb. Used in place of a static logo/icon.
 */
export function MeshOrb({ size = 20, className, speed = 0.4, rounded = true }: MeshOrbProps) {
  return (
    <span
      className={className}
      style={{
        display: "inline-block",
        width: size,
        height: size,
        borderRadius: rounded ? "9999px" : 6,
        overflow: "hidden",
        flexShrink: 0,
        boxShadow: "0 0 12px rgba(74,144,226,0.35)",
      }}
      aria-hidden
    >
      <MeshGradient
        colors={ORB_COLORS}
        speed={speed}
        style={{ width: "100%", height: "100%" }}
      />
    </span>
  );
}

/**
 * Full-bleed animated mesh-gradient background. Sits behind dashboard UI.
 */
export function MeshBackground({ opacity = 1 }: { opacity?: number }) {
  return (
    <div
      aria-hidden
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
        opacity,
        // Instant CSS gradient fallback — visible immediately while the WebGL
        // shader compiles/initializes, so the page never flashes black on refresh.
        background:
          "radial-gradient(circle at 20% 20%, #FFB3D9 0%, transparent 45%)," +
          "radial-gradient(circle at 80% 15%, #87CEEB 0%, transparent 50%)," +
          "radial-gradient(circle at 70% 80%, #4A90E2 0%, transparent 55%)," +
          "radial-gradient(circle at 15% 85%, #2C3E50 0%, transparent 50%)," +
          "linear-gradient(135deg, #1A1A2E 0%, #2C3E50 100%)",
      }}
    >
      <MeshGradient
        colors={ORB_COLORS}
        speed={0.18}
        style={{ width: "100%", height: "100%" }}
      />
      {/* light dark wash for legibility — gradient stays clearly visible */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(8,8,12,0.55)",
        }}
      />
    </div>
  );
}
