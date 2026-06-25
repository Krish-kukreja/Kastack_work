import time
import numpy as np
from sentence_transformers import CrossEncoder

_model = None
_load_time = None

def get_model():
    global _model, _load_time
    if _model is None:
        t0 = time.perf_counter()
        _model = CrossEncoder('cross-encoder/nli-deberta-v3-small')
        _load_time = time.perf_counter() - t0
    return _model

def detect_factual_contradictions(chunks):
    model = get_model()
    
    # Cap comparison to top 8 most recent chunks to avoid O(n^2) blowup
    chunks = sorted(chunks, key=lambda x: x["day"])
    chunks = chunks[-8:]
    
    flagged_pairs = []
    total_time = 0.0
    comparisons = 0
    
    if hasattr(model.model.config, 'id2label'):
        id2label = model.model.config.id2label
    else:
        id2label = {0: 'contradiction', 1: 'entailment', 2: 'neutral'}
        
    for i in range(len(chunks)):
        for j in range(i + 1, len(chunks)):
            a = chunks[i]
            b = chunks[j]
            
            t0 = time.perf_counter()
            logits = model.predict([(a["text"], b["text"])])[0]
            t1 = time.perf_counter()
            
            total_time += (t1 - t0)
            comparisons += 1
            
            best_idx = np.argmax(logits)
            best_label = id2label[best_idx].lower()
            
            # Softmax
            exp_scores = np.exp(logits - np.max(logits))
            probs = exp_scores / exp_scores.sum()
            best_prob = probs[best_idx]
            
            if "contradiction" in best_label and best_prob > 0.6:
                flagged_pairs.append({
                    "day_a": a["day"],
                    "day_b": b["day"],
                    "text_a": a["text"],
                    "text_b": b["text"],
                    "score": float(best_prob)
                })
                
    per_pair_latency = (total_time / comparisons) * 1000 if comparisons > 0 else 0.0
    return flagged_pairs, per_pair_latency
