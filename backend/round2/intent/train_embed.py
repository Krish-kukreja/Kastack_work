import pickle
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
import train

MODEL_EMBED_PATH = Path(__file__).parent / "model_embed.pkl"

def main():
    train_texts, train_labels = train.get_train_data()
    
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
    
    test_texts_set = {x[0].lower() for x in test_data}
    filtered_train_texts = []
    filtered_train_labels = []
    for txt, lbl in zip(train_texts, train_labels):
        if txt.lower() not in test_texts_set:
            filtered_train_texts.append(txt)
            filtered_train_labels.append(lbl)
            
    print("Loading all-MiniLM-L6-v2...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Encoding training data...")
    X_train = embedder.encode(filtered_train_texts, show_progress_bar=True)
    
    base_clf = LinearSVC(random_state=42, max_iter=2000, dual=False)
    clf = CalibratedClassifierCV(base_clf, method='sigmoid', cv=5)
    
    print("Training classifier head...")
    clf.fit(X_train, filtered_train_labels)
    
    print("Saving model head...")
    with open(MODEL_EMBED_PATH, 'wb') as f:
        pickle.dump(clf, f)

if __name__ == "__main__":
    main()
