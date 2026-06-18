import json
import time
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

TOPICS_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\topic_segments.json")
JSONL_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\processed_messages.jsonl")
SUMMARIES_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\summaries.json")

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
BATCH_SIZE = 16
MAX_INPUT_CHARS = 5000  # Tokenizer handles actual precise truncation
MAX_SUMMARY_LEN = 80
MIN_SUMMARY_LEN = 15
CHECKPOINT_SIZE = 100


def load_messages(jsonl_path: Path) -> list[dict]:
    """Load all messages from JSONL."""
    messages = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            messages.append(json.loads(line))
    return messages


def build_text_for_summarization(message_texts: list[str], max_chars: int = MAX_INPUT_CHARS) -> str:
    """Concatenate messages into a single text block, truncated to max_chars."""
    combined = " ".join(msg.strip() for msg in message_texts if msg.strip())
    if len(combined) > max_chars:
        combined = combined[:max_chars]
    return combined


def batch_summarize(model, tokenizer, device, texts: list[str], batch_size: int = BATCH_SIZE) -> list[str]:
    """Summarize a list of texts in batches using direct generate method."""
    summaries = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        if batch_num % 20 == 1 or batch_num == total_batches:
            print(f"    Batch {batch_num}/{total_batches} "
                  f"({i}/{total} items, {i/total*100:.0f}%)")

        try:
            inputs = tokenizer(batch, max_length=1020, truncation=True, padding=True, return_tensors="pt").to(device)
            summary_ids = model.generate(
                inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_length=MAX_SUMMARY_LEN,
                min_length=MIN_SUMMARY_LEN,
                do_sample=False
            )
            batch_summaries = tokenizer.batch_decode(summary_ids, skip_special_tokens=True)
            for j, s in enumerate(batch_summaries):
                summary_text = s.strip()
                if not summary_text or len(summary_text) < 5:
                    summary_text = batch[j][:150]
                summaries.append(summary_text)
        except Exception as e:
            print(f"    WARNING: Batch {batch_num} failed: {e}")
            for text in batch:
                first_sentence = text.split('.')[0].strip()
                summaries.append(first_sentence[:MAX_SUMMARY_LEN] if first_sentence else "Summary unavailable.")

    return summaries


def main():
    t_start = time.time()

    print("=" * 70)
    print("STEP 1: LOADING SUMMARIZATION MODEL")
    print("=" * 70)

    t0 = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
    print(f"  Model: {MODEL_NAME}")
    print(f"  Device: {device}")
    print(f"  Load time: {time.time() - t0:.1f}s")

    print()
    print("=" * 70)
    print("STEP 2: LOADING DATA")
    print("=" * 70)

    with open(TOPICS_PATH, 'r', encoding='utf-8') as f:
        topics = json.load(f)
    print(f"  Topics loaded: {len(topics):,}")

    messages = load_messages(JSONL_PATH)
    print(f"  Messages loaded: {len(messages):,}")

    print()
    print("=" * 70)
    print(f"STEP 3: SUMMARIZING TOPIC SEGMENTS ({len(topics):,} topics)")
    print("=" * 70)

    topic_texts = []
    for topic in topics:
        text = build_text_for_summarization(topic["messages"])
        topic_texts.append(text)

    texts_to_summarize = []
    short_topic_indices = []
    normal_topic_indices = []

    for i, text in enumerate(topic_texts):
        if len(text.split()) < 20:
            short_topic_indices.append(i)
        else:
            normal_topic_indices.append(i)
            texts_to_summarize.append(text)

    print(f"  Topics needing model summarization: {len(texts_to_summarize):,}")
    print(f"  Topics too short (extractive fallback): {len(short_topic_indices):,}")

    t0 = time.time()
    model_summaries = batch_summarize(model, tokenizer, device, texts_to_summarize)
    topic_summarize_time = time.time() - t0
    print(f"  Topic summarization time: {topic_summarize_time:.1f}s")

    model_idx = 0
    for i, topic in enumerate(topics):
        if i in short_topic_indices:
            topic["summary"] = " ".join(topic["messages"][:3])[:200]
        else:
            topic["summary"] = model_summaries[model_idx]
            model_idx += 1

    print()
    print("=" * 70)
    print("STEP 4: CREATING 100-MESSAGE CHECKPOINTS")
    print("=" * 70)

    total_msgs = len(messages)
    num_checkpoints = (total_msgs + CHECKPOINT_SIZE - 1) // CHECKPOINT_SIZE
    print(f"  Total messages: {total_msgs:,}")
    print(f"  Checkpoint size: {CHECKPOINT_SIZE}")
    print(f"  Total checkpoints: {num_checkpoints:,}")

    checkpoint_texts = []
    checkpoint_meta = []

    for ck_id in range(num_checkpoints):
        start_idx = ck_id * CHECKPOINT_SIZE
        end_idx = min(start_idx + CHECKPOINT_SIZE, total_msgs)
        chunk_msgs = messages[start_idx:end_idx]

        text_block = build_text_for_summarization(
            [m["message_text"] for m in chunk_msgs]
        )
        checkpoint_texts.append(text_block)

        checkpoint_meta.append({
            "checkpoint_id": ck_id + 1,
            "start_msg_id": chunk_msgs[0]["msg_id"],
            "end_msg_id": chunk_msgs[-1]["msg_id"],
            "start_day": chunk_msgs[0]["day"],
            "end_day": chunk_msgs[-1]["day"],
            "num_messages": len(chunk_msgs),
            "msg_range": f"{chunk_msgs[0]['msg_id']}-{chunk_msgs[-1]['msg_id']}"
        })

    ck_texts_to_summarize = []
    ck_short_indices = []
    ck_normal_indices = []

    for i, text in enumerate(checkpoint_texts):
        if len(text.split()) < 20:
            ck_short_indices.append(i)
        else:
            ck_normal_indices.append(i)
            ck_texts_to_summarize.append(text)

    print(f"  Checkpoints needing model: {len(ck_texts_to_summarize):,}")
    print(f"  Checkpoints too short: {len(ck_short_indices):,}")

    t0 = time.time()
    ck_summaries = batch_summarize(model, tokenizer, device, ck_texts_to_summarize)
    ck_summarize_time = time.time() - t0
    print(f"  Checkpoint summarization time: {ck_summarize_time:.1f}s")

    ck_model_idx = 0
    checkpoint_records = []
    for i, meta in enumerate(checkpoint_meta):
        if i in ck_short_indices:
            summary = checkpoint_texts[i][:200]
        else:
            summary = ck_summaries[ck_model_idx]
            ck_model_idx += 1

        record = {**meta, "summary": summary}
        checkpoint_records.append(record)

    print()
    print("=" * 70)
    print("STEP 5: SAVING")
    print("=" * 70)

    summaries_output = {
        "topic_summaries": [
            {
                "topic_id": t["topic_id"],
                "summary": t["summary"],
                "start_msg_id": t["start_msg_id"],
                "end_msg_id": t["end_msg_id"],
                "start_day": t["start_day"],
                "end_day": t["end_day"],
                "num_messages": t["num_messages"]
            }
            for t in topics
        ],
        "checkpoint_summaries": checkpoint_records,
        "meta": {
            "summarization_model": MODEL_NAME,
            "total_topics": len(topics),
            "total_checkpoints": len(checkpoint_records),
            "checkpoint_size": CHECKPOINT_SIZE
        }
    }

    with open(SUMMARIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(summaries_output, f, ensure_ascii=False, indent=2)

    summaries_size = SUMMARIES_PATH.stat().st_size / (1024 * 1024)
    print(f"  summaries.json: {summaries_size:.1f} MB")

    with open(TOPICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

    topics_size = TOPICS_PATH.stat().st_size / (1024 * 1024)
    print(f"  topic_segments.json (updated): {topics_size:.1f} MB")

    print()
    print("=" * 70)
    print("STATS SUMMARY")
    print("=" * 70)

    print(f"\n  Topic summaries generated: {len(topics):,}")
    print(f"  Checkpoint summaries generated: {len(checkpoint_records):,}")

    print(f"\n  Sample topic summaries (first 3):")
    for t in topics[:3]:
        print(f"    Topic {t['topic_id']} (Day {t['start_day']}-{t['end_day']}, "
              f"{t['num_messages']} msgs):")
        print(f"      {t['summary'][:150]}")
        print()

    print(f"  Sample checkpoint summaries (first 3):")
    for ck in checkpoint_records[:3]:
        print(f"    Checkpoint {ck['checkpoint_id']} "
              f"(msgs {ck['msg_range']}, Day {ck['start_day']}-{ck['end_day']}):")
        print(f"      {ck['summary'][:150]}")
        print()

    total_time = time.time() - t_start
    print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")


if __name__ == "__main__":
    main()
