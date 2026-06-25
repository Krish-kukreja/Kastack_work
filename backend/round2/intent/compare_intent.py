import os
import time
import pickle
import numpy as np
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score
from sentence_transformers import SentenceTransformer

import sys
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))
from round2.intent import classify as tfidf_classifier

MODEL_TFIDF_PATH = Path(__file__).parent / "model.pkl"
MODEL_EMBED_PATH = Path(__file__).parent / "model_embed.pkl"

def classify_embed(text, embedder, clf):
    emb = embedder.encode([text])
    probs = clf.predict_proba(emb)[0]
    best_idx = np.argmax(probs)
    best_prob = probs[best_idx]
    best_label = clf.classes_[best_idx]
    
    sorted_probs = np.sort(probs)
    margin = sorted_probs[-1] - sorted_probs[-2]
    
    if best_label == "other" or best_prob < 0.45 or margin < 0.10:
        return "unknown"
    if best_label == "small-talk" and best_prob < 0.55:
        return "unknown"
        
    return best_label

def main():
    test_data = [
        ("ping me to call my mom at 5", "reminder"),
        ("i need a reminder to pick up groceries", "reminder"),
        ("set an alarm for the meeting tomorrow", "reminder"),
        ("don't let me forget about the dentist appointment", "reminder"),
        ("remind me to text sarah back", "reminder"),
        ("please remind me to pay the electricity bill", "reminder"),
        ("can you alert me when it's time to leave", "reminder"),
        ("make sure i remember to cancel my free trial", "reminder"),
        ("remind me to take out the trash tonight", "reminder"),
        ("remind me to check the oven in 20 minutes", "reminder"),
        
        ("i am feeling super devastated today", "emotional-support"),
        ("it's been a really tough week for me", "emotional-support"),
        ("i feel like nobody understands my anxiety", "emotional-support"),
        ("my heart is broken after what happened", "emotional-support"),
        ("i am so burnt out and need a break", "emotional-support"),
        ("i just want to cry right now", "emotional-support"),
        ("feeling incredibly isolated and alone", "emotional-support"),
        ("i am totally overwhelmed with everything", "emotional-support"),
        ("i'm extremely stressed about the future", "emotional-support"),
        ("i am having a panic attack", "emotional-support"),
        
        ("i need to finish writing that design doc", "action-item"),
        ("my goal is to review all open pull requests", "action-item"),
        ("gotta clean my apartment before guests arrive", "action-item"),
        ("add buy new shoes to my to do list", "action-item"),
        ("i am planning to hit the gym later", "action-item"),
        ("i have to prepare the slides for the presentation", "action-item"),
        ("i will cook dinner for the family tonight", "action-item"),
        ("task: figure out the budget deficit", "action-item"),
        ("i aim to complete the tutorial by friday", "action-item"),
        ("i'll focus on fixing the frontend bugs today", "action-item"),
        
        ("how are things going over there", "small-talk"),
        ("what did you get up to this weekend", "small-talk"),
        ("nice weather we are having lately", "small-talk"),
        ("hey man what's new with you", "small-talk"),
        ("hope you're having a good day", "small-talk"),
        ("i love listening to classical music", "small-talk"),
        ("did you catch the game last night", "small-talk"),
        ("i'm doing pretty well, thanks for asking", "small-talk"),
        ("what's your favorite type of movie", "small-talk"),
        ("that sounds like a fun trip", "small-talk"),
        
        ("the mitochondria is the powerhouse of the cell", "other"),
        ("the stock market fell 3 percent today", "other"),
        ("asldkfj qwerty zzz", "other"),
        ("deploying the pod via helm chart", "other"),
        ("photosynthesis requires sunlight and water", "other"),
        ("the local sports team won the championship", "other"),
        ("fjghk fhgkjhkj hkjh", "other"),
        ("new studies show coffee may be good for you", "other"),
        ("sudo rm -rf /", "other"),
        ("the capital of australia is canberra", "other")
    ]
    
    true_labels = [lbl if lbl != "other" else "unknown" for _, lbl in test_data]
    texts = [txt for txt, _ in test_data]
    
    print("Evaluating TF-IDF Model...")
    tfidf_preds = []
    latencies = []
    for txt in texts:
        t0 = time.perf_counter()
        res = tfidf_classifier.classify(txt)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)
        tfidf_preds.append(res['label'])
        
    tfidf_acc = accuracy_score(true_labels, tfidf_preds)
    tfidf_f1 = f1_score(true_labels, tfidf_preds, average='macro')
    
    ood_true = [1 if l == "unknown" else 0 for l in true_labels]
    ood_pred = [1 if p == "unknown" else 0 for p in tfidf_preds]
    tfidf_ood_acc = accuracy_score(ood_true, ood_pred)
    
    tfidf_size_mb = os.path.getsize(MODEL_TFIDF_PATH) / (1024 * 1024)
    tfidf_mean_lat = np.mean(latencies)
    tfidf_p95_lat = np.percentile(latencies, 95)
    
    print("Loading Embeddings Model...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    with open(MODEL_EMBED_PATH, "rb") as f:
        embed_clf = pickle.load(f)
        
    print("Evaluating Embeddings Model...")
    embed_preds = []
    latencies = []
    for txt in texts:
        t0 = time.perf_counter()
        pred = classify_embed(txt, embedder, embed_clf)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)
        embed_preds.append(pred)
        
    embed_acc = accuracy_score(true_labels, embed_preds)
    embed_f1 = f1_score(true_labels, embed_preds, average='macro')
    
    ood_pred_e = [1 if p == "unknown" else 0 for p in embed_preds]
    embed_ood_acc = accuracy_score(ood_true, ood_pred_e)
    
    head_size_mb = os.path.getsize(MODEL_EMBED_PATH) / (1024 * 1024)
    embed_runtime_mb = head_size_mb + 90.0 
    
    embed_mean_lat = np.mean(latencies)
    embed_p95_lat = np.percentile(latencies, 95)
    
    print("\n" + "="*120)
    print(f"{'Model':<10} | {'Accuracy':<10} | {'Macro-F1':<10} | {'OOD Detect':<10} | {'Head MB':<10} | {'Runtime MB':<10} | {'Mean ms':<10} | {'p95 ms':<10}")
    print("-" * 120)
    print(f"{'TF-IDF':<10} | {tfidf_acc:<10.4f} | {tfidf_f1:<10.4f} | {tfidf_ood_acc:<10.4f} | {tfidf_size_mb:<10.4f} | {tfidf_size_mb:<10.4f} | {tfidf_mean_lat:<10.4f} | {tfidf_p95_lat:<10.4f}")
    print(f"{'MiniLM':<10} | {embed_acc:<10.4f} | {embed_f1:<10.4f} | {embed_ood_acc:<10.4f} | {head_size_mb:<10.4f} | {embed_runtime_mb:<10.4f} | {embed_mean_lat:<10.4f} | {embed_p95_lat:<10.4f}")
    print("="*120)

if __name__ == "__main__":
    main()
