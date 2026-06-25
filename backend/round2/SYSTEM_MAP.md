# Kastack System Map (Round 2)

## Exact Message Schema
Based on `data/processed/processed_messages.jsonl`:
```json
{
  "msg_id": 0,               // Integer
  "conversation_id": 0,      // Integer
  "day": 1,                  // Integer
  "msg_index": 0,            // Integer
  "sender": "User 1",        // String (e.g., "User 1" or "User 2")
  "message_text": "Hi! How are you?", // String
  "is_media": false          // Boolean
}
```

## What `persona.json` Contains
Contains a global amalgamation of stats and traits for "User 1" and "User 2":
- **`meta`**: Total messages and conversations (11,001).
- **`communication_style`**: Metrics like average message length, exclamation rate, question rate. Time-based metrics (response time, active hour) are `null` because timestamps are missing.
- **`habits`**: Traits like `late_sleeper` and `early_bird` derived from regex matching on text content, not metadata.
- **`personality_traits`**: Scores/flags for traits like curious, enthusiastic, formal, and casual.
- **`personal_facts`**: Extracted categories (`name_mentions`, `location_mentions`, `age_mentions`, `relationship_mentions`, `job_mentions`, `pet_mentions`, `food_mentions`, `hobby_mentions`).
- **`confidence_note`**: Explains no LLM inference was used, no timestamps exist, and that personal facts are aggregated across ~11K different individuals.

## How `rag_engine` Retrieval Works Today
Located in `backend/rag_engine.py`:
1. **Query Processing**: Replaces "user 1" and "user 2" with "you/your" to reduce persona keyword bias.
2. **Embedding**: Embeds the query using `SentenceTransformer("all-MiniLM-L6-v2")` and normalizes it.
3. **Retrieval Paths**:
   - **Messages**: Computes cosine similarity against all 191K message embeddings in `embeddings.npy`. Applies hard filters for `target_user` and `target_topic` if provided.
   - **Topics & Checkpoints**: Computes cosine similarity against precomputed topic/checkpoint summary embeddings.
4. **Persona Fast-Path**: If the query triggers `is_persona_query()`, it bypasses generation and formats an answer directly from `persona.json`.
5. **Answer Generation**: If not a persona query, passes the retrieved context (topics, checkpoints, messages) to `google/flan-t5-small` to generate an answer.

## Reusable Assets for Round 2
- **Part 1 (Adaptive Persona Engine):** 
  - Cannot reuse `persona.json` directly as it lacks per-day tracking and mixes multiple users.
  - Can reuse `processed_messages.jsonl` (contains `day` and `message_text`) and `topic_segments.json` to detect drift over time within specific conversations.
- **Part 2 (Offline Intent Classifier):** 
  - Can reuse `processed_messages.jsonl` for training data.
  - Can reuse the pre-computed `embeddings.npy` as input features for a lightweight classifier (like Logistic Regression) to stay under the <50MB constraint.
- **Part 3 (Conflict-resolution RAG):** 
  - Can reuse `rag_engine.py`'s topic and checkpoint retrieval functions.
  - Can reuse `topic_segments.json` (has `start_day` and `end_day`) to weight retrieval by recency and find contradictory information across days.
- **Part 4 (SYNC Design Doc):** 
  - Can reuse knowledge of the current on-device, offline JSON storage architecture.

## Surprises & Flags
- **Flawed Persona Aggregation**: `persona.json` aggregates "User 1" across 11,001 different conversations. User 1 in conversation 1 is NOT the same person as User 1 in conversation 2. The prompt requires a persona drift detector across days; this must be isolated per `conversation_id` rather than treating "User 1" as a global entity.
- **Noisy Fact Extraction**: The `job_mentions` in `persona.json` include highly inaccurate extractions like "glad to hear" (588 mentions) and "sorry to hear".
- **No True Timestamps**: Only a sequential `day` integer exists. There are no timestamps, making actual time-based metrics impossible.
