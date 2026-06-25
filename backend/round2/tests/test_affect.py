import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))

from round2.affect import emotion

def test_valence_polarity():
    pos_score = emotion.score("I am so happy and thrilled")
    neg_score = emotion.score("I am sad and angry")
    assert pos_score["valence"] > 0, "Expected positive valence"
    assert neg_score["valence"] < 0, "Expected negative valence"

def test_frustration():
    # A frustrated sentence
    scores = emotion.score("This is so frustrating and nothing works properly!")
    # Check if frustration is the top emotion axis (formality is a style axis, not an emotion)
    axes = ["curiosity", "frustration", "playfulness"]
    top_axis = max(axes, key=lambda x: scores.get(x, 0))
    assert top_axis == "frustration", f"Expected frustration to be highest, got {top_axis}"
