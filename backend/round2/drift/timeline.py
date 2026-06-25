import json
import numpy as np
from pathlib import Path

from round2.affect import emotion
from round2.paths import DATA_DIR

def build_timeline(user="User 1", day_start=1, day_end=60):
    data_path = DATA_DIR / "processed_messages.jsonl"
    
    daily_messages = {d: [] for d in range(day_start, day_end + 1)}
    
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            msg = json.loads(line)
            d = msg.get("day", -1)
            sender = msg.get("sender", "")
            if day_start <= d <= day_end and sender == user:
                daily_messages[d].append(msg["message_text"])

    daily_affect = {}
    
    for d in range(day_start, day_end + 1):
        msgs = daily_messages[d]
        if not msgs:
            continue
            
        scores = [emotion.score(m) for m in msgs]
        
        mean_affect = {
            k: np.mean([s[k] for s in scores]) for k in scores[0].keys()
        }
        
        avg_len = np.mean([len(m.split()) for m in msgs])
        excl_rate = np.mean([1 if "!" in m else 0 for m in msgs])
        quest_rate = np.mean([1 if "?" in m else 0 for m in msgs])
        
        mean_affect["avg_length"] = avg_len
        mean_affect["excl_rate"] = excl_rate
        mean_affect["quest_rate"] = quest_rate
        
        daily_affect[d] = mean_affect
        
    return daily_affect

def assign_dominant_traits(mean_affect):
    emotions = {
        "curiosity": mean_affect["curiosity"],
        "frustration": mean_affect["frustration"],
        "playfulness": mean_affect["playfulness"]
    }
    top_emotion = max(emotions, key=emotions.get)
    
    valence = mean_affect["valence"]
    sign = "positive" if valence > 0 else ("negative" if valence < 0 else "neutral")
    
    if emotions[top_emotion] == 0:
        dominant_mood = f"neutral-{sign}"
    else:
        dominant_mood = f"{top_emotion}-{sign}"
        
    formality = mean_affect["formality"]
    dominant_tone = "formal" if formality > 0.5 else "casual"
    
    return dominant_mood, dominant_tone

def detect_change_points(daily_affect, floor_threshold=0.2):
    days = sorted(daily_affect.keys())
    if len(days) < 4:
        return []
        
    distances = []
    
    def get_vec(d):
        aff = daily_affect[d]
        return np.array([
            aff["valence"], aff["curiosity"], aff["frustration"],
            aff["playfulness"], aff["formality"], aff["intensity"]
        ])
    
    for idx in range(2, len(days) - 1):
        prev_days = [days[idx-2], days[idx-1]]
        next_days = [days[idx], days[idx+1]]
        
        prev_vec = np.mean([get_vec(d) for d in prev_days], axis=0)
        next_vec = np.mean([get_vec(d) for d in next_days], axis=0)
        
        dist = np.linalg.norm(prev_vec - next_vec)
        distances.append((dist, days[idx]))
            
    if not distances:
        return []

    dist_values = [d[0] for d in distances]
    mean_dist = np.mean(dist_values)
    std_dist = np.std(dist_values)
    adaptive_threshold = mean_dist + 1.5 * std_dist
    
    effective_threshold = max(adaptive_threshold, floor_threshold)
            
    change_points = []
    # Local maximum check
    for i in range(len(distances)):
        dist, day = distances[i]
        if dist > effective_threshold:
            is_peak = True
            if i > 0 and distances[i-1][0] > dist:
                is_peak = False
            if i < len(distances) - 1 and distances[i+1][0] > dist:
                is_peak = False
            if is_peak:
                change_points.append(day)
                
    return change_points

def build_segments(daily_affect, change_points):
    days = sorted(daily_affect.keys())
    if not days:
        return []
        
    segments = []
    start_idx = 0
    
    all_breakpoints = change_points + [days[-1] + 1]
    
    for bp in all_breakpoints:
        seg_days = [d for d in days if days[start_idx] <= d < bp]
        if not seg_days:
            continue
            
        seg_mean = {}
        for k in daily_affect[seg_days[0]].keys():
            seg_mean[k] = round(float(np.mean([daily_affect[d][k] for d in seg_days])), 3)
            
        mood, tone = assign_dominant_traits(seg_mean)
        
        segments.append({
            "day_range": f"{seg_days[0]}-{seg_days[-1]}",
            "dominant_tone": tone,
            "dominant_mood": mood,
            "mean_affect": seg_mean
        })
        
        for i, d in enumerate(days):
            if d == bp:
                start_idx = i
                break
                
    return segments

def run_real_data():
    print("\n--- REAL TIMELINE (User 1, days 1-60) ---")
    daily_affect = build_timeline("User 1", 1, 60)
    change_points = detect_change_points(daily_affect, floor_threshold=0.2)
    print(f"Change-point days detected: {change_points}")
    
    segments = build_segments(daily_affect, change_points)
    out = {
        "data_caveat": "CRITICAL: The underlying data is PersonaChat. Each day/conversation_id pairs completely different people. User 1 is NOT a continuous person across days. This timeline is analyzing an artifact, not real longitudinal drift.",
        "segments": segments
    }
    
    out_path = Path(__file__).parent / "timeline.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
        
    for s in segments:
        print(s)
        
def test_synthetic_arc():
    print("--- SYNTHETIC ARC VALIDATION ---")
    print("(Proves detector fires when real drift exists; real data won't have a clean arc)")
    synthetic_daily = {}
    
    # State A: curious & formal (Days 1-5)
    for d in range(1, 6):
        synthetic_daily[d] = {"valence": 0.2, "curiosity": 0.8, "frustration": 0.0, "playfulness": 0.1, "formality": 0.8, "intensity": 0.2}
    # State B: frustrated & casual (Days 6-10)
    for d in range(6, 11):
        synthetic_daily[d] = {"valence": -0.8, "curiosity": 0.0, "frustration": 0.9, "playfulness": 0.0, "formality": 0.2, "intensity": 0.9}
    # State C: playful (Days 11-15)
    for d in range(11, 16):
        synthetic_daily[d] = {"valence": 0.8, "curiosity": 0.0, "frustration": 0.0, "playfulness": 0.9, "formality": 0.4, "intensity": 0.8}
        
    for d in synthetic_daily:
        synthetic_daily[d].update({"avg_length": 10, "excl_rate": 0, "quest_rate": 0})
        
    cps = detect_change_points(synthetic_daily, floor_threshold=0.2)
    print(f"Synthetic Change-points detected: {cps} (Expected: [6, 11])")
    
    segments = build_segments(synthetic_daily, cps)
    for s in segments:
        print(s)

if __name__ == "__main__":
    test_synthetic_arc()
    run_real_data()
