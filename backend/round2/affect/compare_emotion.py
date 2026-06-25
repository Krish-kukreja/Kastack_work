import time
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))

from round2.affect import emotion
from round2.affect import emotion_model

battery = [
    "I am absolutely thrilled about the new promotion!",
    "I'm feeling really down and lonely today.",
    "This is so frustrating, nothing works properly.",
    "I wonder what happens if we mix these two chemicals?",
    "haha that's hilarious!",
    "I am not happy at all about this.",
    "I am completely indifferent.",
    "Oh my god! I can't believe that happened!",
    "I am terrified of spiders.",
    "I guess it's okay, maybe?",
    "You are the love of my life.",
    "Stop bothering me right now.",
    "Wow, look at that beautiful sunset.",
    "I didn't expect that plot twist at all.",
    "Just a normal day at the office."
]

def format_lexicon(scores):
    v = scores.get('valence', 0.0)
    c = scores.get('curiosity', 0.0)
    f = scores.get('frustration', 0.0)
    p = scores.get('playfulness', 0.0)
    return f"Val={v:+.2f} | Cur={c:.2f} | Frus={f:.2f} | Play={p:.2f}"

def format_model(scores):
    parts = []
    for k in ['joy', 'sadness', 'anger', 'fear', 'love', 'surprise']:
        parts.append(f"{k[:3]}={scores.get(k, 0.0):.2f}")
    return " | ".join(parts)

def main():
    print("Loading model...")
    emotion_model.get_model()
    print(f"Model loaded in {emotion_model._load_time:.2f}s")
    
    print("\n" + "="*130)
    print(f"{'Text':<52} | {'Lexicon (v/c/f/p)':<45} | {'DistilBERT (joy/sad/ang/fea/lov/sur)'}")
    print("-" * 130)
    
    lex_times = []
    mod_times = []
    
    for txt in battery:
        t0 = time.perf_counter()
        lex_scores = emotion.score(txt)
        t1 = time.perf_counter()
        
        t2 = time.perf_counter()
        mod_scores = emotion_model.score_model(txt)
        t3 = time.perf_counter()
        
        lex_times.append((t1 - t0) * 1000)
        mod_times.append((t3 - t2) * 1000)
        
        print(f"{txt[:50]:<52} | {format_lexicon(lex_scores):<45} | {format_model(mod_scores)}")
        
    avg_lex = sum(lex_times) / len(lex_times)
    avg_mod = sum(mod_times) / len(mod_times)
    
    print("=" * 130)
    print(f"\nLATENCY COMPARISON:")
    print(f"Lexicon average latency: {avg_lex:.4f} ms per call")
    print(f"Model average latency:   {avg_mod:.4f} ms per call")
    
    print("\n" + "="*80)
    print("COMPARISON NOTE:")
    print("Lexicon (0 deps, instant, transparent, brittle on sarcasm/negation) vs Model (richer, context-aware, 270 MB, slower).")
    print("The lexicon is the sensible default because it easily processes the entire historical stream on the fly at <0.1ms per item. The model acts as an optional 'accuracy mode' for difficult contexts or offline batch jobs.")

if __name__ == "__main__":
    main()
