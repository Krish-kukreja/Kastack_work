import json
import numpy as np

from round2.affect import emotion
from round2.drift.timeline import assign_dominant_traits, detect_change_points, build_segments
from round2.drift.triggers import detect_triggers

def build_demo_arc():
    # 15 days of curated textual messages
    demo_messages = {
        # Days 1-5: curious & formal
        1: ["Greetings. I was wondering what time the meeting is scheduled for?", "Could you kindly provide more information?"],
        2: ["I am quite curious about the new project timeline.", "Who will be leading the initiative, if I may ask?"],
        3: ["How fascinating! I would love to understand the underlying mechanics.", "Which approach is most recommended?"],
        4: ["I am wondering if we should reconsider the architecture.", "What are your thoughts on the proposal?"],
        5: ["It is interesting to observe the latest trends.", "Why did the committee decide on that direction?"],
        
        # Days 6-10: frustrated & casual, with "sister" conflict
        6: ["this is so frustrating. my sister is being so annoying.", "ugh i cant deal with this right now."],
        7: ["everything is broken and i hate it. stupid arguments.", "im so mad at her. she ruined everything."],
        8: ["fed up with all this nonsense.", "argh, why does nothing work? this sucks."],
        9: ["still furious about my sister. idiot.", "terrible day. i just want to scream."],
        10: ["so annoyed. whatever.", "damn it, i give up. it's awful."],
        
        # Days 11-15: playful, resolving conflict
        11: ["haha just talked to my sister, we made up! yay!", "lol it was just a silly misunderstanding."],
        12: ["hehe life is good today.", "crazy how things turn around lmfaoo."],
        13: ["woohoo! let's do something fun this weekend.", "jk, i'm just going to stay in and play games haha."],
        14: ["such a funny joke lmao.", "yay, happy times."],
        15: ["everything is great haha.", "silly me for worrying!"]
    }
    
    return demo_messages

def process_demo_arc():
    demo_messages = build_demo_arc()
    
    # 1. Compute per-day affect vector using emotion.score
    daily_affect = {}
    for d, msgs in demo_messages.items():
        scores = [emotion.score(m) for m in msgs]
        mean_affect = {k: np.mean([s[k] for s in scores]) for k in scores[0].keys()}
        
        avg_len = np.mean([len(m.split()) for m in msgs])
        excl_rate = np.mean([1 if "!" in m else 0 for m in msgs])
        quest_rate = np.mean([1 if "?" in m else 0 for m in msgs])
        
        mean_affect["avg_length"] = avg_len
        mean_affect["excl_rate"] = excl_rate
        mean_affect["quest_rate"] = quest_rate
        
        daily_affect[d] = mean_affect
        
    # 2. Detect adaptive change-points
    change_points = detect_change_points(daily_affect, floor_threshold=0.2)
    
    # 3. Detect triggers
    triggers = detect_triggers(demo_messages, change_points)
    
    # 4. Build segments for display
    segments = build_segments(daily_affect, change_points)
    
    print("--- DEMO ARC PIPELINE RESULTS ---")
    print(f"Change-point days detected: {change_points}")
    print("\nSegments:")
    for s in segments:
        print(s)
        
    print("\nTriggers DETECTED by code (not hardcoded):")
    print(json.dumps(triggers, indent=2))
    
    return daily_affect, change_points, triggers

if __name__ == "__main__":
    process_demo_arc()
