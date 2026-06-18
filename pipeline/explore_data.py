"""
CSV Data Exploration Script
Explores conversations.csv to understand structure, content, and quality.
"""

import pandas as pd
import sys

def explore_csv(filepath: str):
    # 1. Load CSV with encoding fallback
    print("=" * 70)
    print("LOADING CSV")
    print("=" * 70)
    
    for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            print(f"✓ Loaded successfully with encoding: {enc}")
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        print("✗ Failed to load with common encodings.")
        sys.exit(1)

    # 2. Column names and dtypes
    print("\n" + "=" * 70)
    print("COLUMN NAMES & DTYPES")
    print("=" * 70)
    for col in df.columns:
        print(f"  {col!r:40s} → {df[col].dtype}")
    print(f"\nTotal columns: {len(df.columns)}")

    # 3. Total rows
    print("\n" + "=" * 70)
    print("TOTAL ROWS")
    print("=" * 70)
    print(f"  {len(df):,} rows")

    # 4. First 10 rows
    print("\n" + "=" * 70)
    print("FIRST 10 ROWS")
    print("=" * 70)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 80)
    pd.set_option('display.width', 200)
    print(df.head(10).to_string())

    # 5. Detect and parse timestamp columns
    print("\n" + "=" * 70)
    print("TIMESTAMP / DATE RANGE")
    print("=" * 70)
    
    timestamp_cols = []
    for col in df.columns:
        if df[col].dtype == 'object':
            sample = df[col].dropna().head(20)
            try:
                parsed = pd.to_datetime(sample, infer_datetime_format=True)
                if parsed.notna().sum() > len(sample) * 0.8:
                    timestamp_cols.append(col)
                    df[col + '_parsed'] = pd.to_datetime(df[col], infer_datetime_format=True, errors='coerce')
                    valid = df[col + '_parsed'].dropna()
                    print(f"  Column: {col!r}")
                    print(f"    Min : {valid.min()}")
                    print(f"    Max : {valid.max()}")
                    print(f"    Span: {valid.max() - valid.min()}")
                    print(f"    Parsed OK: {len(valid):,} / {len(df):,}")
                    print()
            except Exception:
                pass
    
    if not timestamp_cols:
        print("  No timestamp columns auto-detected.")
        print("  Columns with potential date-like names:")
        for col in df.columns:
            if any(kw in col.lower() for kw in ['date', 'time', 'stamp', 'created', 'sent']):
                print(f"    → {col!r} (dtype: {df[col].dtype}, sample: {df[col].iloc[0]})")

    # 6. Unique senders / participants
    print("\n" + "=" * 70)
    print("UNIQUE SENDERS / PARTICIPANTS")
    print("=" * 70)
    
    sender_cols = [col for col in df.columns if any(kw in col.lower() for kw in ['sender', 'from', 'user', 'author', 'name', 'participant'])]
    
    if sender_cols:
        for col in sender_cols:
            unique = df[col].dropna().unique()
            print(f"  Column: {col!r}")
            print(f"    Unique count: {len(unique)}")
            if len(unique) <= 30:
                for u in unique:
                    count = (df[col] == u).sum()
                    print(f"      • {u} ({count:,} messages)")
            else:
                print(f"    (Too many to list, showing top 20)")
                top = df[col].value_counts().head(20)
                for u, count in top.items():
                    print(f"      • {u} ({count:,} messages)")
            print()
    else:
        print("  No obvious sender column found. All columns:")
        for col in df.columns:
            nunique = df[col].nunique()
            print(f"    {col!r}: {nunique} unique values")

    # 7. Null values per column
    print("\n" + "=" * 70)
    print("NULL VALUES PER COLUMN")
    print("=" * 70)
    nulls = df.isnull().sum()
    for col in df.columns:
        if col.endswith('_parsed'):
            continue
        pct = nulls[col] / len(df) * 100
        indicator = "⚠️" if pct > 0 else "✓"
        print(f"  {indicator} {col!r:40s} → {nulls[col]:>6,} nulls ({pct:.1f}%)")

    # 8. Sample of 5 full messages per sender
    print("\n" + "=" * 70)
    print("SAMPLE MESSAGES PER SENDER (5 each, truncated to 200 chars)")
    print("=" * 70)
    
    # Try to find message column
    msg_cols = [col for col in df.columns if any(kw in col.lower() for kw in ['message', 'text', 'content', 'body', 'msg'])]
    
    if sender_cols and msg_cols:
        scol = sender_cols[0]
        mcol = msg_cols[0]
        print(f"  Using sender={scol!r}, message={mcol!r}\n")
        
        for sender in df[scol].dropna().unique():
            print(f"  --- {sender} ---")
            samples = df[df[scol] == sender][mcol].dropna().head(5)
            for i, msg in enumerate(samples, 1):
                msg_str = str(msg)
                display = msg_str[:200] + ("..." if len(msg_str) > 200 else "")
                print(f"    [{i}] {display}")
            print()
    elif msg_cols:
        mcol = msg_cols[0]
        print(f"  No sender column; showing 10 sample messages from {mcol!r}\n")
        for i, msg in enumerate(df[mcol].dropna().head(10), 1):
            msg_str = str(msg)
            display = msg_str[:200] + ("..." if len(msg_str) > 200 else "")
            print(f"    [{i}] {display}")
    else:
        print("  Could not auto-detect message column.")
        print("  Showing first 5 rows of all object columns:")
        obj_cols = df.select_dtypes(include='object').columns
        for col in obj_cols:
            if col.endswith('_parsed'):
                continue
            print(f"\n  Column: {col!r}")
            for i, val in enumerate(df[col].dropna().head(5), 1):
                val_str = str(val)[:200]
                print(f"    [{i}] {val_str}")

    # 9. Bonus: Quick stats useful for later tasks
    print("\n" + "=" * 70)
    print("BONUS: QUICK STATS FOR TASK PLANNING")
    print("=" * 70)
    
    if msg_cols:
        mcol = msg_cols[0]
        df['_msg_len'] = df[mcol].astype(str).str.len()
        print(f"  Message length stats (column: {mcol!r}):")
        print(f"    Mean  : {df['_msg_len'].mean():.1f} chars")
        print(f"    Median: {df['_msg_len'].median():.1f} chars")
        print(f"    Max   : {df['_msg_len'].max():,} chars")
        print(f"    Min   : {df['_msg_len'].min():,} chars")
        
        if sender_cols:
            scol = sender_cols[0]
            print(f"\n  Avg message length per sender:")
            avg_by_sender = df.groupby(scol)['_msg_len'].mean().sort_values(ascending=False)
            for sender, avg in avg_by_sender.items():
                print(f"    • {sender}: {avg:.1f} chars")
    
    # Check for conversation/day structure
    print(f"\n  Potential conversation grouping columns:")
    for col in df.columns:
        if col.endswith('_parsed'):
            continue
        if any(kw in col.lower() for kw in ['day', 'conversation', 'session', 'id', 'group', 'thread']):
            print(f"    → {col!r}: {df[col].nunique()} unique values")


if __name__ == "__main__":
    explore_csv(r"c:\Users\iamkr\projects\Kastack\conversations.csv")
