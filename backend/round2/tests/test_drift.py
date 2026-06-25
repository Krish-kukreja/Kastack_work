import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))

from round2.drift import timeline, demo_arc

def test_detect_change_points():
    daily_affect, cps, triggers = demo_arc.process_demo_arc()
    assert cps == [6, 11]

def test_segments_dominant_moods():
    daily_affect, cps, triggers = demo_arc.process_demo_arc()
    segs = timeline.build_segments(daily_affect, cps)
    
    assert len(segs) == 3
    # Seg 1: days 0-5 (Positive)
    assert segs[0]["mean_affect"]["valence"] > 0
    # Seg 2: days 6-10 (Negative)
    assert segs[1]["mean_affect"]["valence"] < 0
    # Seg 3: days 11+ (Positive)
    assert segs[2]["mean_affect"]["valence"] > 0
