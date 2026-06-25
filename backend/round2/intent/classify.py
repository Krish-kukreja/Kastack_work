import pickle
import time
import numpy as np
from pathlib import Path

from round2.paths import DATA_DIR

MODEL_PATH = Path(__file__).parent / "model.pkl"

with open(MODEL_PATH, "rb") as f:
    pipeline = pickle.load(f)

def classify(text):
    # A) Real vocabulary gate
    word_vec = None
    for name, vec in pipeline['features'].transformer_list:
        if getattr(vec, 'analyzer', None) == 'word':
            word_vec = vec
            break
            
    if word_vec is not None:
        word_features = word_vec.transform([text])
        if word_features.nnz == 0:
            return {"label": "unknown", "confidence": 0.0}
    else:
        features = pipeline['features'].transform([text])
        if features.nnz == 0:
            return {"label": "unknown", "confidence": 0.0}
        
    probs = pipeline.predict_proba([text])[0]
    best_idx = np.argmax(probs)
    best_prob = probs[best_idx]
    best_label = pipeline.classes_[best_idx]
    
    # B) Margin gate
    sorted_probs = np.sort(probs)
    margin = sorted_probs[-1] - sorted_probs[-2]
    
    if best_label == "other" or best_prob < 0.45 or margin < 0.10:
        return {"label": "unknown", "confidence": float(best_prob)}
        
    # C) small-talk precision gate
    if best_label == "small-talk" and best_prob < 0.55:
        return {"label": "unknown", "confidence": float(best_prob)}
    
    return {"label": best_label, "confidence": float(best_prob)}

def run_checks():
    probe_unknown = [
        "asldkfj qwerty zzz",
        "the mitochondria is the powerhouse of the cell",
        "the stock market fell 3 percent today"
    ]
    
    probe_known = [
        "don't let me forget to renew my passport next week",
        "we need to finalize the budget and send it to finance by friday",
        "ive been feeling really low since the breakup"
    ]
    
    scratch_known = [
        "please remind me to call my mom at 5",
        "i am so depressed and sad right now",
        "could you add eggs to the shopping list?",
        "i feel like crying today",
        "make sure i don't miss the dentist appointment",
        "im really frustrated with my job",
        "schedule a meeting with bob",
        "hello there how are you doing"
    ]
    
    scratch_ood = [
        "qwertyuiop asdfghjkl",
        "the quick brown fox jumps over the lazy dog",
        "e = mc squared is a famous equation",
        "hola como estas mi amigo",
        "did you know that honey never spoils?",
        "xkfjdslk fjdslkfjd",
        "water boils at 100 degrees celsius",
        "lorem ipsum dolor sit amet"
    ]
    
    print("\n--- UNKNOWN PROBES ---")
    for txt in probe_unknown:
        res = classify(txt)
        print(f"[{res['label'].upper()}] (conf: {res['confidence']:.2f}) -> {txt}")
        
    print("\n--- KNOWN PROBES ---")
    for txt in probe_known:
        res = classify(txt)
        print(f"[{res['label'].upper()}] (conf: {res['confidence']:.2f}) -> {txt}")

    print("\n--- SCRATCH KNOWN ---")
    for txt in scratch_known:
        res = classify(txt)
        print(f"[{res['label'].upper()}] (conf: {res['confidence']:.2f}) -> {txt}")
        
    print("\n--- SCRATCH OOD ---")
    for txt in scratch_ood:
        res = classify(txt)
        print(f"[{res['label'].upper()}] (conf: {res['confidence']:.2f}) -> {txt}")
        
def benchmark():
    import json
    MESSAGES_PATH = DATA_DIR / "processed_messages.jsonl"
    
    real_msgs = []
    with open(MESSAGES_PATH, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 1000: break
            rec = json.loads(line)
            real_msgs.append(rec["message_text"])
            
    print("\nBenchmarking 1000 classifications...")
    latencies = []
    for msg in real_msgs:
        t0 = time.perf_counter()
        classify(msg)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)
        
    print(f"Mean latency: {np.mean(latencies):.4f} ms/message")
    print(f"p95 latency:  {np.percentile(latencies, 95):.4f} ms/message")

if __name__ == "__main__":
    run_checks()
    benchmark()
