import json

from round2.drift import demo_arc, timeline, triggers
from round2.paths import DATA_DIR, ROUND2_DIR

# 1. Demo Arc
demo_daily_affect, demo_cps, demo_trigs = demo_arc.process_demo_arc()
demo_segments = timeline.build_segments(demo_daily_affect, demo_cps)

cps_list = [min(demo_daily_affect.keys())] + demo_cps
demo_annotated = []
for i, seg in enumerate(demo_segments):
    start_day = cps_list[i]
    if start_day in demo_trigs:
        seg["detected_trigger"] = demo_trigs[start_day]
    demo_annotated.append(seg)

# 2. Real Data
real_affect = timeline.build_timeline("User 1", 1, 60)
data_path = DATA_DIR / "processed_messages.jsonl"
real_messages = {d: [] for d in range(1, 61)}
with open(data_path, "r", encoding="utf-8") as f:
    for line in f:
        msg = json.loads(line)
        d = msg.get("day", -1)
        if 1 <= d <= 60 and msg.get("sender") == "User 1":
            real_messages[d].append(msg["message_text"])
            
real_cps = timeline.detect_change_points(real_affect, floor_threshold=0.2)
real_trigs = triggers.detect_triggers(real_messages, real_cps, topics=triggers.load_topics())
real_segments = timeline.build_segments(real_affect, real_cps)

real_cps_list = [1] + real_cps
real_annotated = []
for i, seg in enumerate(real_segments):
    start_day = real_cps_list[i]
    if start_day in real_trigs:
        seg["detected_trigger"] = real_trigs[start_day]
    real_annotated.append(seg)

output = {
    "data_caveat": "CRITICAL: The underlying data is PersonaChat. Each day/conversation_id pairs completely different people. User 1 is NOT a continuous person across days. This timeline is analyzing an artifact, not real longitudinal drift.",
    "demo_arc_segments": demo_annotated,
    "real_data_segments": real_annotated
}

with open(ROUND2_DIR / 'drift' / 'timeline_with_triggers.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))
