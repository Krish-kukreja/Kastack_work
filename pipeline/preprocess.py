"""
preprocess.py - Parse conversation blobs into individual messages.

Data reality:
  - CSV has 1 column; the column NAME is the first conversation (row 0)
  - Each row = one day's full conversation between User 1 and User 2
  - Format: "User 1: msg\\nUser 2: msg\\nUser 1: msg..."
  - No timestamps - row order = chronological day order
  - ~11K rows (days)

Output: processed_messages.jsonl
  Each line: {"msg_id", "conversation_id", "day", "msg_index", "sender", "message_text", "is_media"}
"""

import pandas as pd
import json
import re
import sys
from pathlib import Path

CSV_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\raw\conversations.csv")
OUTPUT_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\processed_messages.jsonl")

# Pattern to split on "User 1:" or "User 2:" at the start of a line/segment
# Captures the sender label so we can use it
SENDER_PATTERN = re.compile(r'(User [12]):')

# Media indicators (unlikely in this dataset, but handle for completeness)
MEDIA_PATTERNS = re.compile(
    r'^\s*\[(image|video|audio|media|sticker|gif|document|file|voice message|contact|location)\]',
    re.IGNORECASE
)


def load_all_conversations(csv_path: Path) -> list[str]:
    """
    Load ALL conversations including the one trapped in the header.
    
    The CSV has no real header - pandas treats the first conversation as the column name.
    We need to recover it.
    """
    # Read with header=None to avoid losing the first conversation
    # But first, let's read normally to grab the "column name" (which IS conversation 0)
    df_with_header = pd.read_csv(csv_path, encoding='utf-8')
    
    # The column name is the first conversation
    first_conversation = df_with_header.columns[0]
    
    # The remaining rows are in the dataframe
    remaining_conversations = df_with_header.iloc[:, 0].tolist()
    
    # Combine: first conversation + all rows
    all_conversations = [first_conversation] + remaining_conversations
    
    print(f"  Recovered conversation from header (Day 0)")
    print(f"  Total conversations (days): {len(all_conversations):,}")
    
    return all_conversations


def parse_conversation(convo_text: str, conversation_id: int, global_msg_counter: int) -> tuple[list[dict], int]:
    """
    Parse a single conversation blob into individual messages.
    
    Input:  "User 1: Hi!\\nUser 2: Hello!\\nUser 1: How are you?"
    Output: [{"sender": "User 1", "message_text": "Hi!"}, ...]
    
    Returns (messages_list, updated_global_counter)
    """
    if not isinstance(convo_text, str) or not convo_text.strip():
        return [], global_msg_counter
    
    messages = []
    
    # Split the text by sender patterns
    # re.split with capturing group keeps the delimiters
    parts = SENDER_PATTERN.split(convo_text)
    
    # parts looks like: ['', 'User 1', ' Hi!\\n', 'User 2', ' Hello!\\n', 'User 1', ' How are you?']
    # Index 0 is anything before the first "User X:" (usually empty)
    # Then pairs of (sender, message_text) follow
    
    msg_index = 0
    i = 1  # Skip the preamble (parts[0])
    
    while i < len(parts) - 1:
        sender = parts[i].strip()
        raw_text = parts[i + 1].strip()
        
        # Clean up the message text
        # Remove leading/trailing whitespace and newlines
        message_text = raw_text.strip()
        
        # Determine if empty
        if not message_text:
            message_text = "[empty]"
        
        # Check for media
        is_media = bool(MEDIA_PATTERNS.match(message_text))
        
        messages.append({
            "msg_id": global_msg_counter,
            "conversation_id": conversation_id,
            "day": conversation_id + 1,  # 1-indexed day number
            "msg_index": msg_index,
            "sender": sender,
            "message_text": message_text,
            "is_media": is_media
        })
        
        global_msg_counter += 1
        msg_index += 1
        i += 2
    
    return messages, global_msg_counter


def main():
    print("=" * 70)
    print("STEP 1: LOADING CONVERSATIONS")
    print("=" * 70)
    
    all_conversations = load_all_conversations(CSV_PATH)
    
    # Quick validation
    empty_count = sum(1 for c in all_conversations if not isinstance(c, str) or not c.strip())
    print(f"  Empty/null conversations: {empty_count}")
    
    print()
    print("=" * 70)
    print("STEP 2: PARSING INTO INDIVIDUAL MESSAGES")
    print("=" * 70)
    
    all_messages = []
    global_counter = 0
    parse_failures = 0
    
    for conv_id, convo_text in enumerate(all_conversations):
        msgs, global_counter = parse_conversation(convo_text, conv_id, global_counter)
        if not msgs and isinstance(convo_text, str) and convo_text.strip():
            parse_failures += 1
        all_messages.extend(msgs)
        
        # Progress indicator
        if (conv_id + 1) % 2000 == 0:
            print(f"  Processed {conv_id + 1:,} / {len(all_conversations):,} conversations "
                  f"({len(all_messages):,} messages so far)")
    
    print(f"  Done! Total messages extracted: {len(all_messages):,}")
    print(f"  Parse failures (non-empty but 0 messages): {parse_failures}")
    
    print()
    print("=" * 70)
    print("STEP 3: SAVING TO JSONL")
    print("=" * 70)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for msg in all_messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    file_size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"  Saved to: {OUTPUT_PATH}")
    print(f"  File size: {file_size_mb:.1f} MB")
    
    # === STATS ===
    print()
    print("=" * 70)
    print("STATS SUMMARY")
    print("=" * 70)
    
    df = pd.DataFrame(all_messages)
    
    # Total messages
    print(f"\n  Total messages: {len(df):,}")
    print(f"  Total conversations (days): {df['conversation_id'].nunique():,}")
    
    # Messages per sender
    print(f"\n  Messages per sender:")
    sender_counts = df['sender'].value_counts()
    for sender, count in sender_counts.items():
        pct = count / len(df) * 100
        print(f"    {sender}: {count:,} ({pct:.1f}%)")
    
    # Messages per conversation stats
    msgs_per_convo = df.groupby('conversation_id').size()
    print(f"\n  Messages per conversation:")
    print(f"    Mean  : {msgs_per_convo.mean():.1f}")
    print(f"    Median: {msgs_per_convo.median():.1f}")
    print(f"    Min   : {msgs_per_convo.min()}")
    print(f"    Max   : {msgs_per_convo.max()}")
    print(f"    Std   : {msgs_per_convo.std():.1f}")
    
    # Day range (positional chronology)
    print(f"\n  Day range: Day {df['day'].min()} to Day {df['day'].max()}")
    
    # Message length stats per sender
    df['msg_len'] = df['message_text'].str.len()
    print(f"\n  Avg message length per sender:")
    for sender in df['sender'].unique():
        avg_len = df[df['sender'] == sender]['msg_len'].mean()
        print(f"    {sender}: {avg_len:.1f} chars")
    
    # Media messages
    media_count = df['is_media'].sum()
    print(f"\n  Media messages: {media_count}")
    
    # Empty messages
    empty_msgs = (df['message_text'] == '[empty]').sum()
    print(f"  Empty messages: {empty_msgs}")
    
    # Sample output (first 3 messages)
    print(f"\n  Sample output (first 5 messages):")
    for msg in all_messages[:5]:
        preview = msg['message_text'][:80] + ("..." if len(msg['message_text']) > 80 else "")
        print(f"    msg_id={msg['msg_id']:>3} | day={msg['day']:>3} | "
              f"{msg['sender']}: {preview}")
    
    # Sample from middle
    mid = len(all_messages) // 2
    print(f"\n  Sample from middle (around msg_id {mid}):")
    for msg in all_messages[mid:mid+5]:
        preview = msg['message_text'][:80] + ("..." if len(msg['message_text']) > 80 else "")
        print(f"    msg_id={msg['msg_id']:>3} | day={msg['day']:>3} | "
              f"{msg['sender']}: {preview}")


if __name__ == "__main__":
    main()
