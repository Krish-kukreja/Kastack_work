"""
topic_detector.py - Sliding Window Topic Segmentation

Algorithm:
  1. Load embeddings, L2-normalize
  2. Compute consecutive cosine similarities
  3. Smooth with window=3
  4. Threshold = mu - 1.5*sigma → candidate boundaries
  5. Filter: min topic length=5, merge boundaries within 3 msgs
  6. Output topic_segments.json

Input:  embeddings.npy, embedding_index.json, processed_messages.jsonl
Output: topic_segments.json
"""

import json
import time
import numpy as np
from pathlib import Path

EMB_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\embeddings.npy")
INDEX_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\embedding_index.json")
JSONL_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\processed_messages.jsonl")
OUTPUT_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\topic_segments.json")

MIN_TOPIC_LENGTH = 5
MERGE_DISTANCE = 3
THRESHOLD_FACTOR = 1.5
SMOOTHING_WINDOW = 3
MSG_TRUNCATE_LEN = 200


def load_messages(jsonl_path: Path) -> list[dict]:
    """Load all messages from JSONL."""
    messages = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            messages.append(json.loads(line))
    return messages


def compute_consecutive_similarities(embeddings: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between each consecutive pair of messages."""
    # Embeddings are already L2-normalized, so dot product = cosine similarity
    sims = np.sum(embeddings[:-1] * embeddings[1:], axis=1)
    return sims


def smooth_similarities(sims: np.ndarray, window: int = 3) -> np.ndarray:
    """Apply sliding window mean smoothing, handling edges."""
    n = len(sims)
    smoothed = np.zeros(n)
    half_w = window // 2

    for i in range(n):
        start = max(0, i - half_w)
        end = min(n, i + half_w + 1)
        smoothed[i] = np.mean(sims[start:end])

    return smoothed


def detect_boundaries(smoothed_sims: np.ndarray, messages: list[dict], threshold: float) -> list[int]:
    """Find indices where smoothed similarity < threshold OR day changes."""
    candidates = []
    for i in range(len(smoothed_sims)):
        # 1. Check semantic similarity drop
        if smoothed_sims[i] < threshold:
            candidates.append(i + 1)
        
        # 2. CRITICAL: Enforce hard boundary if conversation_id/day changes
        # Assuming messages have 'day' or 'conversation_id' field
        current_day = messages[i].get("day")
        next_day = messages[i+1].get("day")
        if current_day != next_day:
            # Force a boundary here, overriding any merge logic later
            candidates.append(i + 1)
            
    return sorted(list(set(candidates))) # Remove duplicates and sort


def filter_boundaries(boundaries: list[int], num_messages: int, messages: list[dict]) -> list[int]:
    """
    Filter boundaries:
      - Preserve ALL boundaries that correspond to a day change (hard boundaries)
      - For soft boundaries (semantic), merge within MERGE_DISTANCE (keep earlier)
      - Ensure minimum topic length of MIN_TOPIC_LENGTH for soft boundaries
    """
    if not boundaries:
        return []
        
    hard_boundaries = set()
    for i in range(num_messages - 1):
        if messages[i].get("day") != messages[i+1].get("day"):
            hard_boundaries.add(i + 1)

    # Step 1: Merge close boundaries, but always keep hard boundaries
    merged = [boundaries[0]]
    for b in boundaries[1:]:
        if b in hard_boundaries or b - merged[-1] >= MERGE_DISTANCE:
            merged.append(b)
        # else: skip this boundary (too close to previous soft boundary)

    # Step 2: Enforce minimum topic length, EXCEPT for hard boundaries
    filtered = []
    prev_start = 0
    for b in merged:
        topic_len = b - prev_start
        if b in hard_boundaries or topic_len >= MIN_TOPIC_LENGTH:
            filtered.append(b)
            prev_start = b

    # Check last topic
    if filtered:
        last_topic_len = num_messages - filtered[-1]
        if last_topic_len < MIN_TOPIC_LENGTH and filtered[-1] not in hard_boundaries:
            filtered.pop()

    return sorted(list(set(filtered)))


def build_topic_segments(
    boundaries: list[int],
    messages: list[dict],
    num_messages: int
) -> list[dict]:
    """Build topic segment records from boundary indices."""
    segments = []

    # Create start points: [0, b1, b2, ..., bN]
    starts = [0] + boundaries
    # Create end points: [b1-1, b2-1, ..., num_messages-1]
    ends = [b - 1 for b in boundaries] + [num_messages - 1]

    for topic_id, (start, end) in enumerate(zip(starts, ends), 1):
        topic_messages = messages[start:end + 1]

        # Get day range
        days = [m["day"] for m in topic_messages]
        start_day = min(days)
        end_day = max(days)

        # Check if topic spans a conversation break (day change)
        unique_days = set(days)
        spans_break = len(unique_days) > 1

        # Truncated message texts for inline storage
        msg_texts = []
        for m in topic_messages:
            txt = m["message_text"]
            if len(txt) > MSG_TRUNCATE_LEN:
                txt = txt[:MSG_TRUNCATE_LEN] + "..."
            msg_texts.append(txt)

        segments.append({
            "topic_id": topic_id,
            "start_msg_id": messages[start]["msg_id"],
            "end_msg_id": messages[end]["msg_id"],
            "start_day": start_day,
            "end_day": end_day,
            "spans_conversation_break": spans_break,
            "summary": "",  # Placeholder for Stage 4 summarization
            "num_messages": len(topic_messages),
            "messages": msg_texts
        })

    return segments


def main():
    t_start = time.time()

    # === STEP 1: Load embeddings ===
    print("=" * 70)
    print("STEP 1: LOADING EMBEDDINGS")
    print("=" * 70)

    embeddings = np.load(EMB_PATH)
    print(f"  Shape: {embeddings.shape}")
    print(f"  Dtype: {embeddings.dtype}")

    N = embeddings.shape[0]

    # === STEP 2: L2 normalize ===
    print()
    print("=" * 70)
    print("STEP 2: L2 NORMALIZING")
    print("=" * 70)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid division by zero
    norms = np.maximum(norms, 1e-10)
    embeddings = embeddings / norms

    # Verify normalization
    sample_norms = np.linalg.norm(embeddings[:5], axis=1)
    print(f"  Sample norms after normalization: {sample_norms}")

    # === STEP 3: Consecutive cosine similarities ===
    print()
    print("=" * 70)
    print("STEP 3: COMPUTING CONSECUTIVE COSINE SIMILARITIES")
    print("=" * 70)

    raw_sims = compute_consecutive_similarities(embeddings)
    print(f"  Computed {len(raw_sims):,} similarities")
    print(f"  Raw sim stats: mean={raw_sims.mean():.4f}, std={raw_sims.std():.4f}, "
          f"min={raw_sims.min():.4f}, max={raw_sims.max():.4f}")

    # === STEP 4: Smoothing ===
    print()
    print("=" * 70)
    print("STEP 4: SMOOTHING (window={})".format(SMOOTHING_WINDOW))
    print("=" * 70)

    smoothed = smooth_similarities(raw_sims, window=SMOOTHING_WINDOW)
    print(f"  Smoothed sim stats: mean={smoothed.mean():.4f}, std={smoothed.std():.4f}, "
          f"min={smoothed.min():.4f}, max={smoothed.max():.4f}")

    # === STEP 5: Threshold & boundary detection ===
    print()
    print("=" * 70)
    print("STEP 5: DETECTING BOUNDARIES")
    print("=" * 70)

    mu = smoothed.mean()
    sigma = smoothed.std()
    threshold = mu - THRESHOLD_FACTOR * sigma

    print(f"  mu     = {mu:.4f}")
    print(f"  sigma  = {sigma:.4f}")
    print(f"  Threshold (mu - {THRESHOLD_FACTOR}*sigma) = {threshold:.4f}")

    messages = load_messages(JSONL_PATH)
    print(f"  Loaded {len(messages):,} messages")

    raw_boundaries = detect_boundaries(smoothed, messages, threshold)
    print(f"  Raw candidate boundaries: {len(raw_boundaries):,}")

    # === STEP 6: Filter boundaries ===
    print()
    print("=" * 70)
    print("STEP 6: FILTERING BOUNDARIES")
    print("=" * 70)

    filtered_boundaries = filter_boundaries(raw_boundaries, N, messages)
    print(f"  After filtering (min_len={MIN_TOPIC_LENGTH}, merge_dist={MERGE_DISTANCE}): "
          f"{len(filtered_boundaries):,} boundaries")
    print(f"  Expected topics: {len(filtered_boundaries) + 1:,}")

    # === STEP 7: Load messages & build segments ===
    print()
    print("=" * 70)
    print("STEP 7: BUILDING TOPIC SEGMENTS")
    print("=" * 70)

    segments = build_topic_segments(filtered_boundaries, messages, N)
    print(f"  Built {len(segments):,} topic segments")

    # === STEP 8: Save ===
    print()
    print("=" * 70)
    print("STEP 8: SAVING")
    print("=" * 70)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    file_size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"  Saved to: {OUTPUT_PATH}")
    print(f"  File size: {file_size_mb:.1f} MB")

    # === STATS ===
    print()
    print("=" * 70)
    print("STATS SUMMARY")
    print("=" * 70)

    topic_lengths = [s["num_messages"] for s in segments]
    print(f"\n  Total topics: {len(segments):,}")
    print(f"\n  Topic length distribution:")
    print(f"    Min   : {min(topic_lengths)}")
    print(f"    Max   : {max(topic_lengths)}")
    print(f"    Mean  : {np.mean(topic_lengths):.1f}")
    print(f"    Median: {np.median(topic_lengths):.1f}")
    print(f"    Std   : {np.std(topic_lengths):.1f}")

    # How many span conversation breaks
    cross_break = sum(1 for s in segments if s["spans_conversation_break"])
    print(f"\n  Topics spanning conversation breaks: {cross_break} / {len(segments)} "
          f"({cross_break/len(segments)*100:.1f}%)")

    # First 3 topics sample
    print(f"\n  First 3 topics:")
    for seg in segments[:3]:
        print(f"    Topic {seg['topic_id']}:")
        print(f"      msg_id range : {seg['start_msg_id']} - {seg['end_msg_id']}")
        print(f"      day range    : Day {seg['start_day']} - Day {seg['end_day']}")
        print(f"      num_messages : {seg['num_messages']}")
        print(f"      spans_break  : {seg['spans_conversation_break']}")
        print(f"      first msg    : {seg['messages'][0][:100]}...")
        print()

    elapsed = time.time() - t_start
    print(f"  Total time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
