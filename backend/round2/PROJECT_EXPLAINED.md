# Kastack Round 2: Project Explained

## 1. What Is This? (The Big Picture)
Kastack is an experimental blueprint for a private, on-device AI assistant that remembers your past conversations, tracks your emotional moods over time, and can accurately answer questions about your history. The core philosophy is **absolute privacy**: instead of sending your personal messages to a cloud server like ChatGPT does, Kastack processes your text directly on your own computer. To achieve this, it relies on tiny, mathematically efficient algorithms that can run instantly without needing massive internet-connected artificial intelligence.

## 2. The Data (And Our Honest Caveat)
This project uses a public dataset of conversations called **PersonaChat**. However, there is a major catch: in PersonaChat, each "day" or conversation thread pairs two completely *different* people, simply labeled "User 1" and "User 2". 

Think of it like reading a diary where a different stranger wrote the entry every single day. Because Kastack is built to track a single person's mood over time, running it on this dataset means we are technically measuring the "mood swings" between completely random strangers, rather than a genuine shift in one person's personality. We openly acknowledge this caveat rather than pretending the data shows a perfectly continuous human life.

---

## 3. Glossary of Terms

*   **Model:** A set of mathematical rules learned by a computer from examples. *Analogy: A recipe that tells a chef exactly how to bake a cake based on past successes.*
*   **Embedding:** Converting a sentence of text into a long list of numbers so the computer understands its meaning. *Analogy: Translating English into a secret numeric code that captures the "vibe" of the sentence.*
*   **Vector:** A list of numbers representing something (like an embedding). *Analogy: A GPS coordinate (latitude, longitude) that pinpoints a specific location.*
*   **Cosine Similarity:** The math used to see how close two vectors are to each other. *Analogy: Checking if two houses are located on the same street.*
*   **TF-IDF:** A math trick to find the most important words in a sentence by seeing how rare they are. *Analogy: Finding a needle in a haystack-ignoring the common "the" and "and", but focusing on the rare word "passport".*
*   **Classifier:** A system that sorts incoming information into predefined buckets. *Analogy: A post office machine that sorts mail into different zip code bins.*
*   **RAG (Retrieval-Augmented Generation):** A system that searches for relevant facts in a database *before* trying to answer a question. *Analogy: Taking an open-book test instead of guessing from memory.*
*   **Sentiment (VADER):** A score measuring how positive, negative, or neutral a piece of text is. *Analogy: A mood ring that changes color based on your feelings.*
*   **Change-point:** A specific moment in time when a pattern suddenly and drastically shifts. *Analogy: A sudden, steep drop in temperature signaling winter has arrived.*
*   **CRDT (Conflict-free Replicated Data Type):** A clever way to merge data from multiple offline devices without ever deleting or losing information. *Analogy: Two people independently adding items to a shared grocery list, merging them later without erasing the other's work.*

---

## 4. The Four Parts of the System

### A) Offline Intent Classifier
*   **The Problem:** Normally, AI systems send your text to the cloud to figure out what you want, which takes seconds and ruins privacy. We need to instantly know if you are asking for a "reminder," "emotional support," "small talk," or an "action item."
*   **How it Works:** We built a tiny classifier using TF-IDF. Instead of "understanding" the sentence like a human, it acts like a mail sorter, quickly looking for specific shapes and word patterns (like the letters in "remind") to drop the message into the right bucket.
*   **The Files:** `round2/intent/classify.py` and `train.py`.
*   **Real Results:** 
    *   **MEASURED:** The model size is incredibly small at **1.1875 MB**.
    *   **MEASURED:** It is lightning fast, with a mean latency of **17.0578 ms/message** and a p95 latency of **31.1370 ms/message**.
*   **Limitations:** Because it relies on simple word patterns, it isn't very smart. The precision for "small-talk" is fairly low (0.59), meaning it sometimes gets confused by unusual or borderline sentences.

### B) Persona Drift Detector
*   **The Problem:** People change over time. We want to track how your mood evolves (e.g., from formal to frustrated) without running a heavy, slow AI on every single message.
*   **How it Works:** Like taking your average body temperature every day to see if you have a fever, the system averages the "sentiment" of your messages daily. If the temperature jumps drastically, it flags a "change-point" and points to the specific word or topic that caused the jump (the trigger).
*   **The Files:** `round2/drift/timeline.py`, `triggers.py`, and `demo_arc.py`.
*   **Real Results:**
    *   **MEASURED:** On the real dataset, the detector found change-points at days **[14, 26, 35, 53]**. 
*   **Limitations:** Because of the data caveat mentioned in Section 2, the "drift" detected on the real dataset is actually just statistical noise caused by switching to a completely different random user on those days.

### C) Conflict-Resolution RAG
*   **The Problem:** If you tell your diary "I hate my sister" on Day 1, and "I love my sister" on Day 10, a normal RAG system gets confused and just spits out both facts blindly. 
*   **How it Works:** Like a detective reviewing a timeline of witness statements, Kastack searches for all your past messages about a topic. It scores the emotion of those messages. If it notices you used to be negative but are now positive, it specifically points out the shift: "Earlier you felt negative, but most recently you felt positive."
*   **The Files:** `round2/rag/conflict_resolver.py`.
*   **Real Results:** 
    *   **MEASURED:** During retrieval, the system pulled a broad recall of **296** candidate messages (Top 50 Cosine + 269 Keyword Hits) before re-ranking them.
*   **Limitations:** The system currently tracks *emotional polarity* (positive vs. negative mood) rather than true factual contradictions. It knows you shifted from angry to happy about a topic, but it can't mathematically prove the logic of "I am an only child" vs "I have a sister."

### D) Sync Architecture Design
*   **The Problem:** If you use Kastack offline on your phone, and offline on your laptop, and both devices try to sync later, most software simply lets the "Last Write Win" (overwriting and permanently deleting the older data).
*   **How it Works:** We designed the system to use CRDTs. Like a shared grocery list where you only ever *add* items, Kastack mathematically merges the data from both devices so that the timeline of your emotional history is perfectly preserved without any data destruction.
*   **The Files:** `round2/SYNC_DESIGN.md`.
*   **Real Results:** N/A (This is an architectural design document, not executable code).
*   **Limitations:** CRDTs are notoriously complex to build and require extra computer memory to keep track of deleted items (called "tombstones").

---

## 5. How the Pieces Connect
Kastack is built to be highly efficient by reusing its core components:
*   The **Emotion Scorer** (`emotion.py`) is a shared utility. It is used by the Drift Detector to calculate your daily mood averages, and it is reused by the Conflict-Resolution RAG to determine if your feelings on a specific topic have flipped from negative to positive.
*   The **Embeddings** (the numeric translations of text) generated in Round 1 are completely reused by the Conflict-RAG to find relevant messages, saving massive amounts of processing power.

---

## 6. The Key Decisions (And Why We Made Them)
*   **Why a tiny TF-IDF model instead of a big LLM for intent?** Speed and battery life. We need instant, offline sorting. A 1.18 MB model running in 17 milliseconds is infinitely better for a phone battery than a massive AI model.
*   **Why are answers built by templates instead of an LLM?** To completely eliminate the risk of "hallucination" (AI making things up). By injecting your exact past quotes into a strict text template, Kastack can never lie to you about your own history.
*   **Why openly admit the cross-person data caveat?** Because trust is the currency of private AI. If the system is measuring statistical noise, we must disclose it rather than fabricating a "success" story.
*   **Why CRDT for sync?** Because a personal journal is an "append-mostly" timeline. Erasing history because of a sync conflict is unacceptable for an app designed to track your life's evolution.

---

## 7. How to Run the Demo
To see all of this in action, you can run the Streamlit dashboard on your local machine using this exact command in your terminal:
```bash
C:\Users\iamkr\AppData\Local\Programs\Python\Python312\python.exe -m streamlit run round2/app.py --server.headless=true
```
When you open `http://localhost:8501` in your browser, you will see four tabs:
1.  **Offline Intent Classifier:** A text box to type messages and instantly see how the tiny model categorizes them.
2.  **Persona Drift Detector:** Displays the visual chart of the mood timeline, plus the JSON data showing the exact triggers detected for each shift.
3.  **Conflict-Resolution RAG:** Shows the curated "sister" timeline proving the contradiction detector works, with a button to run the heavy RAG search on the real dataset.
4.  **Sync Architecture Design:** Renders the Markdown document explaining the CRDT sync logic.

---

## 8. What's Weak & What I'd Do Next
While Kastack proves that on-device, private RAG is possible, it has strict limitations that must be addressed in Round 3:
1.  **Factual Contradictions:** The current RAG only detects emotional flips. To detect true factual lies (e.g., "I live in Paris" vs "I live in London"), we need to upgrade the resolver to use an **NLI (Natural Language Inference)** model.
2.  **Unknown Detection:** The intent classifier struggles with "unknown" text (like gibberish). Because it uses simple word patterns, if you type gibberish that happens to share letters with training data, it might accidentally categorize it instead of rejecting it.
3.  **Real Longitudinal Data:** To truly prove the Drift Detector works, the system must be tested on a dataset tracking a *single continuous human* over a year, rather than disjointed strangers.
