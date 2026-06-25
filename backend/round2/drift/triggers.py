import json
import re
from collections import Counter

from round2.paths import DATA_DIR

RELATIONSHIPS = {
    "sister", "brother", "mom", "dad", "mother", "father", 
    "boss", "partner", "friend", "husband", "wife", "son", 
    "daughter", "uncle", "aunt", "cousin", "boyfriend", "girlfriend"
}

STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
    "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", 
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", 
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", 
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", 
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", 
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", 
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", 
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", 
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
}

def load_topics():
    topics_path = DATA_DIR / "topic_segments.json"
    if not topics_path.exists():
        return []
    with open(topics_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_entities(text):
    entities = []
    # Relationship match
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    for w in words:
        if w.lower() in RELATIONSHIPS:
            entities.append(w.lower())
            
    # Mid-sentence capitalization rule
    sentences = re.split(r'[.!?]+', text)
    for s in sentences:
        s_words = re.findall(r'\b[a-zA-Z]+\b', s)
        if len(s_words) > 1:
            for w in s_words[1:]:
                if w.istitle() and w.lower() not in STOPWORDS:
                    entities.append(w)
    return set(entities)

def get_words(text):
    return [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', text) if w.lower() not in STOPWORDS]

def detect_triggers(daily_messages, change_points, topics=None):
    triggers = {}
    
    all_cps = [min(daily_messages.keys())] + change_points
    
    for i, cp in enumerate(change_points):
        prev_cp = all_cps[i]
        prior_window_days = [d for d in range(prev_cp, cp) if d in daily_messages]
        current_day_msgs = daily_messages.get(cp, [])
        prior_window_msgs = []
        for d in prior_window_days:
            prior_window_msgs.extend(daily_messages[d])
            
        current_text = " ".join(current_day_msgs)
        prior_text = " ".join(prior_window_msgs)
        
        trigger_detail = {}
        
        # a) new TOPIC
        new_topic = None
        if topics is not None:
            for t in topics:
                if t["start_day"] == cp:
                    new_topic = t["summary"]
                    break
        else:
            # self-contained topic derivation
            prior_words = set(get_words(prior_text))
            curr_words = get_words(current_text)
            new_curr_words = [w for w in curr_words if w not in prior_words]
            if new_curr_words:
                top_new = [x[0] for x in Counter(new_curr_words).most_common(2)]
                new_topic = "shift toward: " + ", ".join(top_new)
                
        if new_topic:
            trigger_detail["new_topic"] = new_topic
            
        # b) new PERSON/ENTITY
        prior_entities = extract_entities(prior_text)
        curr_entities = extract_entities(current_text)
        new_entities = curr_entities - prior_entities
        
        if new_entities:
            # Prioritize relationship words over proper nouns
            rels = [e for e in new_entities if e in RELATIONSHIPS]
            if rels:
                trigger_detail["new_entity"] = rels[0]
            else:
                trigger_detail["new_entity"] = list(new_entities)[0]
                
        # c) keyword SPIKE
        prior_words = get_words(prior_text)
        curr_words = get_words(current_text)
        
        if curr_words:
            prior_counts = Counter(prior_words)
            curr_counts = Counter(curr_words)
            
            # normalize to frequencies
            prior_len = len(prior_words) or 1
            curr_len = len(curr_words) or 1
            
            spikes = {}
            for w, c in curr_counts.items():
                curr_freq = c / curr_len
                prior_freq = prior_counts.get(w, 0) / prior_len
                if curr_freq > prior_freq:
                    spikes[w] = curr_freq - prior_freq
                    
            if spikes:
                top_spike = max(spikes.items(), key=lambda x: x[1])
                trigger_detail["keyword_spike"] = top_spike[0]
                
        triggers[cp] = trigger_detail
        
    return triggers

if __name__ == "__main__":
    # Test on Real Data
    from round2.drift import timeline
    
    print("--- REAL TIMELINE TRIGGERS ---")
    daily_affect = timeline.build_timeline("User 1", 1, 60)
    # Re-fetch the raw messages since build_timeline only gives affect
    data_path = DATA_DIR / "processed_messages.jsonl"
    daily_messages = {d: [] for d in range(1, 61)}
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            msg = json.loads(line)
            d = msg.get("day", -1)
            if 1 <= d <= 60 and msg.get("sender") == "User 1":
                daily_messages[d].append(msg["message_text"])
                
    cps = timeline.detect_change_points(daily_affect, floor_threshold=0.2)
    print(f"Change-points: {cps}")
    trigs = detect_triggers(daily_messages, cps, topics=load_topics())
    print(json.dumps(trigs, indent=2))
