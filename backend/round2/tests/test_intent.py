import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))

from round2.intent import classify

def test_intent_classes():
    # Clear inputs -> expected classes
    assert classify.classify("remind me to buy milk")["label"] == "reminder"
    assert classify.classify("I feel so sad today")["label"] == "emotional-support"
    # Gibberish/OOD -> "unknown"
    assert classify.classify("asldkfj qwerty")["label"] == "unknown", "Bug: OOD gibberish not defaulting to 'unknown'"

def test_intent_latency():
    t0 = time.perf_counter()
    classify.classify("this is a latency test")
    t1 = time.perf_counter()
    assert (t1 - t0) * 1000 < 200, "classify() latency > 200ms"

def test_model_size():
    model_path = BASE_DIR / "round2" / "intent" / "model.pkl"
    size = os.path.getsize(model_path)
    assert size < 50 * 1024 * 1024, "Model size exceeds 50MB"
