import json
import re
import numpy as np
from sentence_transformers import SentenceTransformer

from round2.affect import emotion
from round2.paths import DATA_DIR

RELATIONSHIPS = {
    "sister", "brother", "mom", "dad", "mother", "father", 
    "boss", "partner", "friend", "husband", "wife", "son", 
    "daughter", "uncle", "aunt", "cousin", "boyfriend", "girlfriend"
}

def extract_subject(query):
    query_lower = query.lower()
    
    # 1. Relationship check
    for rel in RELATIONSHIPS:
        if re.search(r'\b' + rel + r'\b', query_lower):
            return rel
            
    # 2. Noun right after phrases
    m = re.search(r'\b(?:about my|about the|about|my)\s+([a-zA-Z]+)', query_lower)
    if m:
        return m.group(1)
        
    # 3. Last capitalized word
    words = re.findall(r'\b[a-zA-Z]+\b', query)
    for w in reversed(words):
        if w.istitle():
            return w
            
    return None

# Tunable weights for re-ranking
W_COSINE = 0.5
W_RECENCY = 0.2
W_EMOTION = 0.3

# Paths
EMB_PATH = DATA_DIR / "embeddings.npy"
INDEX_PATH = DATA_DIR / "embedding_index.json"
JSONL_PATH = DATA_DIR / "processed_messages.jsonl"

def load_assets():
    print("Loading assets...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    raw = np.load(EMB_PATH).astype(np.float32)
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    embeddings = raw / np.maximum(norms, 1e-10)
    
    with open(INDEX_PATH, 'r') as f:
        idx = json.load(f)
    msg_index = [int(idx[str(i)]) for i in range(len(idx))]
    
    messages = {}
    max_day = 1
    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            messages[rec["msg_id"]] = rec
            max_day = max(max_day, rec.get("day", 1))
            
    return embedder, embeddings, msg_index, messages, max_day

def resolve_conflict(chunks, subject):
    from . import nli
    
    for c in chunks:
        if "valence" not in c:
            c["valence"] = emotion.score(c["text"])["valence"]
            
    chunks = sorted(chunks, key=lambda x: x["day"])
    
    print("\n" + "="*80)
    print("CONTRADICTION RESOLUTION & MERGED ANSWER (v2)")
    print("="*80)
    
    # 1. EMOTIONAL CONTRADICTIONS
    neg_chunks = [c for c in chunks if c["valence"] < -0.25]
    pos_chunks = [c for c in chunks if c["valence"] > 0.25]
    
    print("--- 1. EMOTIONAL CONTRADICTIONS (POLARITY) ---")
    emo_flagged = False
    if neg_chunks and pos_chunks:
        emo_flagged = True
        extremes = neg_chunks + pos_chunks
        extremes.sort(key=lambda x: x["day"])
        earliest = extremes[0]
        
        if earliest["valence"] < -0.25:
            latest_opposite = pos_chunks[-1]
            sent1 = "negative"
            sent2 = "positive"
        else:
            latest_opposite = neg_chunks[-1]
            sent1 = "positive"
            sent2 = "negative"
            
        print("CONTRADICTION DETECTED: Opposing valences found.")
        print(f"  - Day {earliest['day']} (Valence {earliest['valence']:.4f}): {earliest['text']}")
        print(f"  - Day {latest_opposite['day']} (Valence {latest_opposite['valence']:.4f}): {latest_opposite['text']}")
    else:
        print("NO emotional contradiction detected.")

    # 2. FACTUAL CONTRADICTIONS
    print("\n--- 2. FACTUAL CONTRADICTIONS (NLI) ---")
    fac_flagged = False
    if len(chunks) > 1:
        flagged_pairs, per_pair_lat = nli.detect_factual_contradictions(chunks)
        if flagged_pairs:
            fac_flagged = True
            print(f"CONTRADICTION DETECTED: {len(flagged_pairs)} factual clash(es) found.")
            for f in flagged_pairs:
                print(f"  - Day {f['day_a']} vs Day {f['day_b']} (Score: {f['score']:.4f}):")
                print(f"      '{f['text_a']}'  <-- CLASHES WITH -->  '{f['text_b']}'")
        else:
            print("NO factual contradiction detected.")
            
        if nli._load_time:
            print(f"  [NLI model load time: {nli._load_time:.2f}s | per-pair latency: {per_pair_lat:.2f}ms]")
    else:
        print("NO factual contradiction detected (not enough chunks).")

    print("\nMERGED COHERENT ANSWER:")
    if not chunks:
        print("No relevant chunks to form an answer.")
    else:
        latest = chunks[-1]
        if not emo_flagged and not fac_flagged:
            print(f"You consistently feel the same about your {subject}. Most recently (day {latest['day']}): '{latest['text']}'.")
        else:
            msg = f"[!] Your facts or feelings about {subject} changed over time. "
            if emo_flagged: msg += f"Earlier you felt {sent1}, but most recently you felt {sent2}. "
            if fac_flagged: msg += f"Additionally, there are factual inconsistencies in your statements. "
            print(msg)


def retrieve_and_rerank(query: str, subject_term: str = None, top_k: int = 10):
    if subject_term is None:
        subject_term = extract_subject(query)
        if subject_term is None:
            # Fallback to the most salient query noun (naively the last word)
            words = re.findall(r'\b[a-zA-Z]+\b', query)
            subject_term = words[-1] if words else "topic"
        print(f"Auto-selected subject: '{subject_term}'")
        
    embedder, embeddings, msg_index, messages, max_day = load_assets()
    
    print(f"Embedding query: '{query}'")
    query_emb = embedder.encode([query], convert_to_numpy=True)[0]
    norm = np.linalg.norm(query_emb)
    query_emb = query_emb / max(norm, 1e-10)
    
    print("Computing cosine similarities...")
    sims = embeddings @ query_emb
    
    # 1. Top ~50 by cosine similarity
    top_50_idx = np.argpartition(sims, -50)[-50:]
    cosine_candidates = {msg_index[i] for i in top_50_idx}
    
    # 2. All messages containing subject term
    keyword_candidates = set()
    term_lower = subject_term.lower()
    for mid, rec in messages.items():
        if term_lower in rec.get("message_text", "").lower():
            keyword_candidates.add(mid)
            
    # Union of candidates
    candidate_mids = cosine_candidates.union(keyword_candidates)
    print(f"Broad recall candidates: {len(candidate_mids)} (Top 50 Cosine + {len(keyword_candidates)} Keyword Hits)")
    
    # Build candidate records
    candidate_records = []
    # Create a reverse index to get sims easily
    mid_to_arr_idx = {mid: i for i, mid in enumerate(msg_index)}
    
    for mid in candidate_mids:
        rec = messages[mid]
        text = rec.get("message_text", "")
        arr_idx = mid_to_arr_idx[mid]
        cos_sim = float(sims[arr_idx])
        
        # Calculate components
        recency = rec.get("day", 1) / max_day
        em_score = emotion.score(text)
        emotional_weight = em_score["intensity"]
        
        final_score = (W_COSINE * cos_sim) + (W_RECENCY * recency) + (W_EMOTION * emotional_weight)
        
        candidate_records.append({
            "msg_id": mid,
            "text": text,
            "day": rec.get("day", 1),
            "sender": rec.get("sender", ""),
            "cosine": cos_sim,
            "recency": recency,
            "emotional_weight": emotional_weight,
            "final_score": final_score
        })
        
    # Sort by pure cosine for BEFORE
    before_sorted = sorted(candidate_records, key=lambda x: x["cosine"], reverse=True)
    
    # Sort by final score for AFTER
    after_sorted = sorted(candidate_records, key=lambda x: x["final_score"], reverse=True)
    
    print("\n" + "="*80)
    print("BEFORE: Top 10 by PURE COSINE SIMILARITY")
    print("="*80)
    for i, item in enumerate(before_sorted[:top_k]):
        print(f"[{i+1}] Day {item['day']} | {item['sender']} | Cosine: {item['cosine']:.4f}")
        print(f"    Text: {item['text']}")
        print()
        
    print("\n" + "="*80)
    print("AFTER: Top 10 by RE-RANKED SCORE (Cosine + Recency + Emotion)")
    print("="*80)
    top_results = after_sorted[:top_k]
    for i, item in enumerate(top_results):
        print(f"[{i+1}] Day {item['day']} | {item['sender']} | Final Score: {item['final_score']:.4f}")
        print(f"    Components -> Cosine: {item['cosine']:.4f} * {W_COSINE} = {item['cosine']*W_COSINE:.4f}")
        print(f"               -> Recency: {item['recency']:.4f} * {W_RECENCY} = {item['recency']*W_RECENCY:.4f}")
        print(f"               -> Emotion: {item['emotional_weight']:.4f} * {W_EMOTION} = {item['emotional_weight']*W_EMOTION:.4f}")
        print(f"    Text: {item['text']}")
        print()
        
    chunks_for_resolution = [{"day": item["day"], "text": item["text"]} for item in top_results if item['sender'] == 'User 1']
    print("\n--- REAL DATA RETRIEVAL ---")
    resolve_conflict(chunks_for_resolution, subject_term)

def run_curated_demo():
    print("\n--- CURATED DEMO ARC ---")
    curated_chunks = [
        {"day": 6, "text": "this is so frustrating. my sister is being so annoying."},
        {"day": 9, "text": "still furious about my sister. idiot."},
        {"day": 11, "text": "haha just talked to my sister, we made up! yay!"}
    ]
    resolve_conflict(curated_chunks, "sister")


def resolve_conflict_data(chunks, subject):
    """Structured (non-printing) version of resolve_conflict, for API use."""
    from round2.rag import nli
    for c in chunks:
        if "valence" not in c:
            c["valence"] = emotion.score(c["text"])["valence"]
    chunks = sorted(chunks, key=lambda x: x["day"])

    neg = [c for c in chunks if c["valence"] < -0.25]
    pos = [c for c in chunks if c["valence"] > 0.25]
    emotional = None
    if neg and pos:
        extremes = sorted(neg + pos, key=lambda x: x["day"])
        earliest = extremes[0]
        if earliest["valence"] < -0.25:
            latest_opp, s1, s2 = pos[-1], "negative", "positive"
        else:
            latest_opp, s1, s2 = neg[-1], "positive", "negative"
        emotional = {
            "earlier": {"day": earliest["day"], "valence": round(earliest["valence"], 4), "text": earliest["text"], "sentiment": s1},
            "later": {"day": latest_opp["day"], "valence": round(latest_opp["valence"], 4), "text": latest_opp["text"], "sentiment": s2},
        }

    factual = []
    if len(chunks) > 1:
        flagged, _ = nli.detect_factual_contradictions(chunks)
        factual = flagged

    if not chunks:
        merged = "No relevant chunks to form an answer."
    elif not emotional and not factual:
        latest = chunks[-1]
        merged = f"You consistently feel the same about your {subject}. Most recently (day {latest['day']}): '{latest['text']}'."
    else:
        merged = f"[!] Your facts or feelings about {subject} changed over time. "
        if emotional:
            merged += f"Earlier you felt {emotional['earlier']['sentiment']}, but most recently you felt {emotional['later']['sentiment']}. "
        if factual:
            merged += "Additionally, there are factual inconsistencies in your statements."

    return {
        "subject": subject,
        "emotional_contradiction": emotional,
        "factual_contradictions": factual,
        "merged_answer": merged.strip(),
    }


def retrieve_and_rerank_data(query, assets, subject_term=None, top_k=10):
    """Structured version of retrieve_and_rerank that returns data for the API."""
    embedder, embeddings, msg_index, messages, max_day = assets
    if subject_term is None:
        subject_term = extract_subject(query)
        if subject_term is None:
            words = re.findall(r'\b[a-zA-Z]+\b', query)
            subject_term = words[-1] if words else "topic"

    query_emb = embedder.encode([query], convert_to_numpy=True)[0]
    query_emb = query_emb / max(np.linalg.norm(query_emb), 1e-10)
    sims = embeddings @ query_emb

    top_50_idx = np.argpartition(sims, -50)[-50:]
    cosine_candidates = {msg_index[i] for i in top_50_idx}
    term_lower = subject_term.lower()
    keyword_candidates = {mid for mid, rec in messages.items() if term_lower in rec.get("message_text", "").lower()}
    candidate_mids = cosine_candidates.union(keyword_candidates)

    mid_to_arr = {mid: i for i, mid in enumerate(msg_index)}
    records = []
    for mid in candidate_mids:
        rec = messages[mid]
        text = rec.get("message_text", "")
        cos = float(sims[mid_to_arr[mid]])
        recency = rec.get("day", 1) / max_day
        ew = emotion.score(text)["intensity"]
        records.append({
            "day": rec.get("day", 1),
            "sender": rec.get("sender", ""),
            "text": text,
            "cosine": round(cos, 4),
            "final_score": round(W_COSINE * cos + W_RECENCY * recency + W_EMOTION * ew, 4),
        })

    before = sorted(records, key=lambda x: x["cosine"], reverse=True)[:top_k]
    after = sorted(records, key=lambda x: x["final_score"], reverse=True)[:top_k]
    chunks = [{"day": r["day"], "text": r["text"]} for r in after if r["sender"] == "User 1"]
    resolution = resolve_conflict_data(chunks, subject_term)
    return {"subject": subject_term, "before": before, "after": after, "resolution": resolution}


if __name__ == "__main__":
    print("\n--- SCRATCH BATTERY (NLI) ---")
    from round2.rag import nli
    test_c = [{"day": 1, "text": "I am an only child."}, {"day": 2, "text": "I went shopping with my sister."}]
    flagged, lat = nli.detect_factual_contradictions(test_c)
    print(f"Contradiction probe ('I am an only child' vs 'I went shopping with my sister'): Flagged={len(flagged) > 0}")
    
    test_nc = [{"day": 1, "text": "I love pizza."}, {"day": 2, "text": "Pizza is my favorite food."}]
    flagged, lat = nli.detect_factual_contradictions(test_nc)
    print(f"Non-contradiction probe ('I love pizza' vs 'Pizza is my favorite food'): Flagged={len(flagged) > 0}")

    print("\n--- TEST AUTO SUBJECT ---")
    retrieve_and_rerank(query="what did I say about my family", top_k=10)
    
    run_curated_demo()
