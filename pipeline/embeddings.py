"""
embeddings.py — Generate per-message embeddings using sentence-transformers.

Input:  processed_messages.jsonl (fields: msg_id, conversation_id, day, msg_index, sender, message_text, is_media)
Output: embeddings.npy          (shape: [num_messages, 384])
        embedding_index.json    (array index -> msg_id mapping)

Model: all-MiniLM-L6-v2 (384-dim, ~80MB, CPU-friendly)
"""

import json
import time
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

JSONL_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\processed_messages.jsonl")
EMB_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\embeddings.npy")
INDEX_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\embedding_index.json")

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 256


def load_messages(jsonl_path: Path) -> tuple[list[int], list[str]]:
    """Load messages in chronological order (already sorted by msg_id)."""
    msg_ids = []
    texts = []
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            msg_ids.append(record["msg_id"])
            texts.append(record["message_text"])
    
    return msg_ids, texts


def main():
    # === STEP 1: Load messages ===
    print("=" * 70)
    print("STEP 1: LOADING MESSAGES")
    print("=" * 70)
    
    msg_ids, texts = load_messages(JSONL_PATH)
    print(f"  Loaded {len(texts):,} messages")
    print(f"  msg_id range: {msg_ids[0]} to {msg_ids[-1]}")
    
    # === STEP 2: Load model ===
    print()
    print("=" * 70)
    print("STEP 2: LOADING MODEL")
    print("=" * 70)
    
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME)
    model_load_time = time.time() - t0
    print(f"  Model: {MODEL_NAME}")
    print(f"  Embedding dimension: {model.get_sentence_embedding_dimension()}")
    print(f"  Load time: {model_load_time:.1f}s")
    
    # === STEP 3: Generate embeddings ===
    print()
    print("=" * 70)
    print("STEP 3: GENERATING EMBEDDINGS")
    print("=" * 70)
    
    total = len(texts)
    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"  Total messages: {total:,}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Total batches: {num_batches:,}")
    print()
    
    t0 = time.time()
    
    # sentence-transformers handles batching internally with show_progress_bar
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=False  # Keep raw; we can normalize later if needed
    )
    
    encode_time = time.time() - t0
    msgs_per_sec = total / encode_time
    
    print(f"\n  Encoding time: {encode_time:.1f}s ({msgs_per_sec:.0f} msgs/sec)")
    
    # === STEP 4: Save embeddings ===
    print()
    print("=" * 70)
    print("STEP 4: SAVING")
    print("=" * 70)
    
    # Save numpy array
    np.save(EMB_PATH, embeddings)
    emb_size_mb = EMB_PATH.stat().st_size / (1024 * 1024)
    print(f"  embeddings.npy: {emb_size_mb:.1f} MB")
    
    # Save index mapping
    index_map = {str(i): mid for i, mid in enumerate(msg_ids)}
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index_map, f)
    idx_size_mb = INDEX_PATH.stat().st_size / (1024 * 1024)
    print(f"  embedding_index.json: {idx_size_mb:.1f} MB")
    
    # === STATS ===
    print()
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    print(f"\n  Array shape: {embeddings.shape}")
    print(f"  Dtype: {embeddings.dtype}")
    
    # Sample norms
    norms = np.linalg.norm(embeddings[:10], axis=1)
    print(f"\n  Sample embedding norms (first 10):")
    for i, norm in enumerate(norms):
        print(f"    [{i}] norm = {norm:.4f}")
    
    # Overall norm stats
    all_norms = np.linalg.norm(embeddings, axis=1)
    print(f"\n  Norm statistics (all embeddings):")
    print(f"    Mean:   {all_norms.mean():.4f}")
    print(f"    Std:    {all_norms.std():.4f}")
    print(f"    Min:    {all_norms.min():.4f}")
    print(f"    Max:    {all_norms.max():.4f}")
    
    # Total time
    total_time = model_load_time + encode_time
    print(f"\n  Total time (load + encode): {total_time:.1f}s")


if __name__ == "__main__":
    main()
