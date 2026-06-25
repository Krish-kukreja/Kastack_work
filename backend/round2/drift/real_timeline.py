import sys
import json
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))

from round2.affect import emotion
from round2.drift import timeline, triggers
import matplotlib.pyplot as plt

INPUT_FILE = BASE_DIR / "round2" / "drift" / "real_messages.jsonl"
OUT_JSON = BASE_DIR / "round2" / "drift" / "real_person_timeline.json"
OUT_PNG = BASE_DIR / "round2" / "drift" / "real_person_chart.png"

TARGET_SENDER = None # Default to most frequent

def main():
    if not INPUT_FILE.exists():
        print(f"File not found: {INPUT_FILE}")
        print("Please run ingest_real.py first.")
        sys.exit(0)
        
    messages = []
    sender_counts = defaultdict(int)
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            messages.append(rec)
            sender_counts[rec["sender"]] += 1
            
    if not messages:
        print("No messages to process.")
        sys.exit(0)
        
    if TARGET_SENDER is None:
        target = max(sender_counts.items(), key=lambda x: x[1])[0]
    else:
        target = TARGET_SENDER
        
    print(f"Analyzing sender: {target} ({sender_counts[target]} messages)")
    
    weekly_texts = defaultdict(list)
    for m in messages:
        if m["sender"] == target:
            weekly_texts[m["week"]].append(m["message_text"])
            
    if not weekly_texts:
        print(f"No messages found for sender {target}.")
        sys.exit(0)
        
    weeks = sorted(weekly_texts.keys())
    
    series = []
    for w in weeks:
        texts = weekly_texts[w]
        combined = " ".join(texts)
        scores = emotion.score(combined)
        series.append(scores["valence"])
        
    cps = timeline.detect_change_points(series, threshold=0.3, min_segment=2)
    segs = timeline.build_segments(series, cps)
    
    adjusted_segs = []
    for s in segs:
        start_idx = s["start_day"]
        end_idx = min(s["end_day"], len(weeks) - 1)
        start_week = weeks[start_idx]
        end_week = weeks[end_idx]
        adjusted_segs.append({
            "start_week": start_week,
            "end_week": end_week,
            "mean_valence": s["mean_valence"],
            "variance": s.get("variance", 0.0)
        })
        
    chunks = [{"day": weeks[i], "text": " ".join(weekly_texts[weeks[i]])} for i in range(len(weeks))]
    for s in adjusted_segs:
        s["start_day"] = s["start_week"]
        s["end_day"] = s["end_week"]
        
    try:
        triggers.detect_triggers(adjusted_segs, chunks, topics=None)
    except Exception as e:
        print(f"Warning: trigger detection failed: {e}")
        
    for s in adjusted_segs:
        s["start_week"] = s.pop("start_day")
        s["end_week"] = s.pop("end_day")
        
    print(f"Detected {len(cps)} change points: {cps}")
    print("Segments:")
    for s in adjusted_segs:
        print(f"  Week {s['start_week']} - Week {s['end_week']}: Valence {s['mean_valence']:.3f} (Trigger: {s.get('trigger', 'N/A')})")
        
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(adjusted_segs, f, indent=2)
        
    plt.figure(figsize=(10, 5))
    plt.plot(weeks, series, marker="o", linestyle="-", color="purple")
    for cp in cps:
        if cp < len(weeks):
            plt.axvline(weeks[cp], color="red", linestyle="--", alpha=0.5)
    plt.ylim(-1.0, 1.0)
    plt.title(f"Valence Timeline (Weekly) for {target}")
    plt.xlabel("Week")
    plt.ylabel("Valence")
    plt.grid(True, alpha=0.3)
    plt.savefig(OUT_PNG)
    plt.close()
    print(f"Chart saved to {OUT_PNG}")

if __name__ == "__main__":
    main()
