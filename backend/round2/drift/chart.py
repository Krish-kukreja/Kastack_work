import matplotlib.pyplot as plt
from pathlib import Path

from round2.drift import demo_arc

def generate_chart():
    daily_affect, change_points, triggers = demo_arc.process_demo_arc()
    
    days = sorted(daily_affect.keys())
    valence = [daily_affect[d]["valence"] for d in days]
    frustration = [daily_affect[d]["frustration"] for d in days]
    playfulness = [daily_affect[d]["playfulness"] for d in days]
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(days, valence, label="Valence", color="green", marker="o", linewidth=2)
    plt.plot(days, frustration, label="Frustration", color="red", marker="x", linewidth=2)
    plt.plot(days, playfulness, label="Playfulness", color="blue", marker="s", linewidth=2)
    
    # Vertical lines for change points
    for cp in change_points:
        plt.axvline(x=cp, color='black', linestyle='--', alpha=0.7)
        
        # Annotate with trigger detail
        trigger = triggers.get(cp, {})
        # Format annotation text
        lines = [f"DRIFT DAY {cp}"]
        if "new_entity" in trigger:
            lines.append(f"Entity: {trigger['new_entity']}")
        if "keyword_spike" in trigger:
            lines.append(f"Spike: '{trigger['keyword_spike']}'")
            
        annotation_text = "\n".join(lines)
        
        plt.annotate(annotation_text, 
                     xy=(cp, 0), 
                     xytext=(5, 10), 
                     textcoords='offset points',
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
                     fontsize=9,
                     verticalalignment='bottom')
                     
    plt.title("Longitudinal Persona Drift (Demo Arc) - mood genuinely swings")
    plt.xlabel("Day")
    plt.ylabel("Affect Score")
    plt.ylim(-1, 1)
    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper right")
    plt.tight_layout()

    out_path = Path(__file__).parent / "drift_chart.png"
    plt.savefig(out_path)
    print(f"Chart saved to {out_path}")

def generate_real_chart():
    """Plot the REAL PersonaChat data (User 1, days 1-60).
    The detector fires, but every segment is the same mood -> a flat line.
    This is the honest 'the given data has no real drift' visual."""
    from round2.drift import timeline
    daily_affect = timeline.build_timeline("User 1", 1, 60)
    change_points = timeline.detect_change_points(daily_affect, floor_threshold=0.2)

    days = sorted(daily_affect.keys())
    valence = [daily_affect[d]["valence"] for d in days]
    frustration = [daily_affect[d]["frustration"] for d in days]
    playfulness = [daily_affect[d]["playfulness"] for d in days]

    plt.figure(figsize=(12, 6))

    plt.plot(days, valence, label="Valence", color="green", linewidth=2)
    plt.plot(days, frustration, label="Frustration", color="red", linewidth=2)
    plt.plot(days, playfulness, label="Playfulness", color="blue", linewidth=2)

    # Detector still fires - but the mood lines do not move across these markers
    for cp in change_points:
        plt.axvline(x=cp, color='black', linestyle='--', alpha=0.5)

    plt.title("Real Data (PersonaChat, User 1, Days 1-60) - detector fires, but mood never shifts")
    plt.xlabel("Day")
    plt.ylabel("Affect Score")
    plt.ylim(-1, 1)
    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper right")
    plt.tight_layout()

    out_path = Path(__file__).parent / "real_drift_chart.png"
    plt.savefig(out_path)
    print(f"Real chart saved to {out_path}")

if __name__ == "__main__":
    generate_chart()
    generate_real_chart()
