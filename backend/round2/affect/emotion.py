import re
import json
from pathlib import Path
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from round2.paths import DATA_DIR

sia = SentimentIntensityAnalyzer()

CURIOSITY_WORDS = {"why", "how", "wonder", "curious", "what", "where", "when", "who", "which"}
FRUSTRATION_WORDS = {"annoying", "ugh", "argh", "stupid", "idiot", "frustrating", "broken", "hate", "damn", "shit", "fuck", "sucks", "awful", "terrible", "worst", "frustrated", "frustration", "angry", "anger", "mad", "furious", "upset", "irritated", "annoyed", "disappointed", "hopeless", "fed up"}
PLAYFULNESS_WORDS = {"haha", "lol", "lmao", "hehe", "jk", "fun", "joke", "silly", "crazy", "yay", "woohoo", "lmfao", "lmfaoo"}
CONTRACTIONS = {"can't", "won't", "didn't", "don't", "isn't", "aren't", "couldn't", "shouldn't", "wouldn't", "it's", "i'm", "you're", "they're", "we're", "i'll", "you'll", "we'll"}

def score_affect(text):
    if not text:
        return {
            "valence": 0.0, "curiosity": 0.0, "frustration": 0.0,
            "playfulness": 0.0, "formality": 0.5, "intensity": 0.0
        }
        
    vader_scores = sia.polarity_scores(text)
    valence = vader_scores['compound']
    
    words = re.findall(r'\b\w+\b', text.lower())
    num_words = len(words)
    if num_words == 0:
        return {
            "valence": valence, "curiosity": 0.0, "frustration": 0.0,
            "playfulness": 0.0, "formality": 0.5, "intensity": 0.0
        }
        
    word_set = set(words)
    
    # Surface features
    num_caps = sum(1 for w in re.findall(r'\b[A-Z]{2,}\b', text))
    num_excl = text.count("!")
    num_quest = text.count("?")
    
    # Curiosity
    curiosity_score = 0.0
    if num_quest > 0:
        curiosity_score += 0.5
    curiosity_words_found = len(word_set.intersection(CURIOSITY_WORDS))
    curiosity_score += min(0.5, curiosity_words_found * 0.25)
    curiosity_score = min(1.0, curiosity_score)
    
    # Frustration
    frustration_score = 0.0
    if valence < -0.3:
        frustration_score += abs(valence) * 0.4
    frust_words_found = len(word_set.intersection(FRUSTRATION_WORDS))
    frustration_score += min(0.5, frust_words_found * 0.3)
    if num_caps > 0:
        frustration_score += 0.2
    frustration_score = min(1.0, frustration_score)
    
    # Playfulness
    play_words_found = len(word_set.intersection(PLAYFULNESS_WORDS))
    playfulness_score = min(1.0, play_words_found * 0.4)
    if playfulness_score == 0 and valence > 0.5 and num_excl > 0:
        playfulness_score = 0.2
        
    # Formality
    formality_score = 0.5
    num_contractions = len(word_set.intersection(CONTRACTIONS))
    formality_score -= min(0.3, num_contractions * 0.1)
    if num_caps > 0: formality_score -= 0.1
    if num_excl > 0: formality_score -= 0.1
    if play_words_found > 0: formality_score -= 0.2
    
    avg_word_len = sum(len(w) for w in words) / num_words
    if avg_word_len > 5.0: formality_score += 0.1
    if num_words > 15: formality_score += 0.1
    if text[0].isupper() and text[-1] in {".", "!", "?"}: formality_score += 0.1
    
    formality_score = max(0.0, min(1.0, formality_score))
    
    # Intensity
    intensity_score = abs(valence) * 0.5
    intensity_score += min(0.3, num_excl * 0.15)
    intensity_score += min(0.2, num_caps * 0.1)
    intensity_score = min(1.0, intensity_score)
    
    return {
        "valence": round(valence, 3),
        "curiosity": round(curiosity_score, 3),
        "frustration": round(frustration_score, 3),
        "playfulness": round(playfulness_score, 3),
        "formality": round(formality_score, 3),
        "intensity": round(intensity_score, 3)
    }

score = score_affect

def main():
    test_sentences = [
        "I wonder how the quantum physics principles apply here?", 
        "Ugh, this code is so incredibly broken and annoying!!",
        "lol that was super fun, let's do it again haha",
        "The committee will review the document and provide feedback by Friday.",
        "WHY is it not working??? I hate this so much!",
        "What do you think about the new restaurant downtown?",
        "I'm not sure I understand, could you explain further?",
        "Haha, silly goose, of course I'll be there!",
        "This is the worst day of my life, everything sucks.",
        "We're going to the park, wanna come?"
    ]
    
    print("--- 10 CUSTOM PROBES ---")
    for s in test_sentences:
        res = score_affect(s)
        print(f"TEXT: {s}")
        print(f"  --> {res}\n")

    print("--- REAL DATASET EXAMPLES ---")
    data_path = DATA_DIR / "processed_messages.jsonl"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            for _ in range(3):
                line = f.readline()
                data = json.loads(line)
                txt = data["message_text"]
                res = score_affect(txt)
                print(f"REAL: {txt}")
                print(f"  --> {res}\n")

if __name__ == "__main__":
    main()
