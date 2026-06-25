import json
import random
import re
from pathlib import Path

from round2.paths import DATA_DIR

MESSAGES_PATH = DATA_DIR / "processed_messages.jsonl"
OUTPUT_PATH = Path(__file__).parent / "dataset.json"

# --- Hand-written templates (~40 per class) ---
REMINDER_TEMPLATES = [
    "remind me to {}", "set a reminder to {}", "don't let me forget to {}",
    "remind me about {} tomorrow", "ping me to {}", "remind me in 10 minutes to {}",
    "alert me to {}", "remind me: {}", "set an alarm for {}", "make sure I {}",
    "remind me at 5pm to {}", "schedule a reminder to {}", "remind me next week to {}",
    "please remind me to {}", "can you remind me to {}", "I need a reminder to {}",
    "remind me to {} this evening", "remind me to {} in the morning",
    "remind me to {} on Friday", "remind me when I get home to {}",
    "remind me to {} when I wake up", "add a reminder to {}", "create a reminder for {}",
    "don't forget to {}", "remind me tomorrow morning to {}", "remind me before I sleep to {}",
    "remind me to call {}", "remind me to email {}", "remind me to buy {}",
    "remind me to pay {}", "remind me to check {}", "remind me to finish {}",
    "remind me to review {}", "remind me to submit {}", "remind me to text {}",
    "remind me to bring {}", "remind me to pick up {}", "remind me to feed {}",
    "remind me to water {}", "remind me to cancel {}", "remind me to start {}"
]
REMINDER_FILLERS = [
    "buy milk", "call mom", "pay the bills", "feed the dog", "take my medicine",
    "send the email", "review the PR", "book the flight", "cancel the subscription",
    "water the plants", "take out the trash", "call the doctor", "finish the report"
]

SUPPORT_TEMPLATES = [
    "I'm feeling {}", "I just feel so {} lately", "It's been a {} day",
    "I'm really {} right now", "I can't stop feeling {}", "Everything is so {}",
    "I'm so {} about this", "I've been {} all week", "Why am I so {}?",
    "I'm having a {} time", "I'm struggling with being {}", "I feel incredibly {}",
    "I'm just so {}", "I'm a bit {}", "I feel very {}", "I am feeling {}",
    "It makes me feel {}", "I've been feeling {}", "I am so {}", "I feel so {} today",
    "I'm kind of {}", "I am really {}", "I'm feeling quite {}", "I feel absolutely {}",
    "I just want to cry because I'm {}", "I need some help, I'm {}", "Can someone talk to me? I'm {}",
    "I'm overwhelmed and {}", "I am dealing with being {}", "I am suffering from feeling {}",
    "I am coping with being {}", "I am trying to handle being {}", "I am managing feeling {}",
    "I am surviving feeling {}", "I am enduring feeling {}", "I am experiencing being {}",
    "I am going through a {} phase", "I am in a {} mood", "I am having a {} moment",
    "I am dealing with a {} situation", "I am facing a {} time"
]
SUPPORT_FILLERS = [
    "sad", "depressed", "anxious", "lonely", "exhausted", "stressed",
    "overwhelmed", "hopeless", "frustrated", "tired", "burned out",
    "upset", "angry", "heartbroken", "scared", "nervous", "down"
]

ACTION_ITEM_TEMPLATES = [
    "I need to {}", "I have to {}", "I must {}", "My action item is to {}",
    "To-do: {}", "Task: {}", "Add to my list: {}", "I should {}",
    "I will {}", "I am going to {}", "I plan to {}", "I am planning to {}",
    "I intend to {}", "I aim to {}", "I'm supposed to {}", "I've got to {}",
    "I better {}", "I need to make sure I {}", "I need to remember to {}",
    "I have to remember to {}", "I must remember to {}", "I should remember to {}",
    "I will remember to {}", "I am going to remember to {}", "I plan to remember to {}",
    "I am planning to remember to {}", "I intend to remember to {}", "I aim to remember to {}",
    "I need to focus on {}", "I have to focus on {}", "I must focus on {}",
    "I should focus on {}", "I will focus on {}", "I am going to focus on {}",
    "I plan to focus on {}", "I am planning to focus on {}", "I intend to focus on {}",
    "I aim to focus on {}", "I need to work on {}", "I have to work on {}"
]
ACTION_FILLERS = [
    "finish the slides", "write the document", "fix the bug", "clean the house",
    "prepare for the meeting", "do the laundry", "grocery shop", "read the paper",
    "update the tracker", "push the code", "run the script", "test the feature"
]

SMALL_TALK_TEMPLATES = [
    "{}", "Hey {}", "Hi {}", "Hello {}", "Good morning {}", "Good afternoon {}",
    "Good evening {}", "How are you {}", "What's up {}", "How's it going {}",
    "How have you been {}", "What have you been up to {}", "How is your day {}",
    "How was your day {}", "How is your week {}", "How was your week {}",
    "How is your weekend {}", "How was your weekend {}", "How is your family {}",
    "How was your family {}", "How is your job {}", "How was your job {}",
    "How is your work {}", "How was your work {}", "How is your school {}",
    "How was your school {}", "How is your life {}", "How was your life {}",
    "How is everything {}", "How was everything {}", "How are things {}",
    "How were things {}", "How is it {}", "How was it {}", "What are you doing {}",
    "What did you do {}", "What will you do {}", "What are you up to {}",
    "What were you up to {}", "What will you be up to {}", "What's new {}"
]
SMALL_TALK_FILLERS = [
    "today?", "lately?", "recently?", "there?", "friend.", "man.", "bro.",
    "dude.", "mate.", "pal.", "buddy.", "chap.", "guy.", "girl.", "lady.",
    "woman.", "sir.", "madam.", "miss.", "mrs.", "mr.", "dr.", "prof."
]

def generate_base_data(templates, fillers, label):
    data = []
    for t in templates:
        for _ in range(3): # generate 3 per template
            text = t.format(random.choice(fillers))
            data.append({"text": text, "label": label})
    return data

# --- Augmentation ---
SYNONYMS = {
    "remind": ["ping", "alert", "notify"],
    "need": ["have", "must", "got"],
    "sad": ["down", "blue", "upset"],
    "happy": ["glad", "joyful", "cheerful"],
    "finish": ["complete", "wrap up", "done with"]
}

def augment(text):
    # Synonym swap
    words = text.split()
    new_words = []
    for w in words:
        clean_w = w.lower().strip(".,!?")
        if clean_w in SYNONYMS and random.random() < 0.3:
            new_w = random.choice(SYNONYMS[clean_w])
            new_words.append(new_w)
        else:
            new_words.append(w)
    res = " ".join(new_words)
    
    # Typos (swap adjacent chars)
    if random.random() < 0.1 and len(res) > 3:
        idx = random.randint(0, len(res)-2)
        chars = list(res)
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
        res = "".join(chars)
    
    # Paraphrase / punctuation drop
    if random.random() < 0.2:
        res = res.replace("?", "").replace(".", "").lower()
        
    return res

def main():
    print("Generating base templates...")
    dataset = []
    dataset.extend(generate_base_data(REMINDER_TEMPLATES, REMINDER_FILLERS, "reminder"))
    dataset.extend(generate_base_data(SUPPORT_TEMPLATES, SUPPORT_FILLERS, "emotional-support"))
    dataset.extend(generate_base_data(ACTION_ITEM_TEMPLATES, ACTION_FILLERS, "action-item"))
    dataset.extend(generate_base_data(SMALL_TALK_TEMPLATES, SMALL_TALK_FILLERS, "small-talk"))
    
    print("Augmenting data...")
    augmented = []
    for item in dataset:
        augmented.append(item) # keep original
        for _ in range(2): # 2 augmentations per item
            aug_text = augment(item["text"])
            if aug_text != item["text"]:
                augmented.append({"text": aug_text, "label": item["label"]})
    
    print(f"Dataset size before mining: {len(augmented)}")
    
    print("Mining real small-talk examples from processed_messages.jsonl...")
    real_small_talk = []
    try:
        with open(MESSAGES_PATH, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i > 5000: break # Only scan first 5000 lines
                rec = json.loads(line)
                txt = rec["message_text"]
                # Heuristic for small talk: short, no action verbs, greeting-like
                l_txt = txt.lower()
                if len(txt.split()) < 10 and not any(kw in l_txt for kw in ["remind", "to do", "must", "need to", "sad", "depressed", "anxious"]):
                    real_small_talk.append(txt)
    except Exception as e:
        print(f"Could not read messages: {e}")
        
    random.shuffle(real_small_talk)
    mined = real_small_talk[:300] # Take 300
    for txt in mined:
        augmented.append({"text": txt, "label": "small-talk"})
        
    print(f"Added {len(mined)} mined small-talk examples.")
    print(f"Total dataset size: {len(augmented)}")
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(augmented, f, indent=2)
    print(f"Saved dataset to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
