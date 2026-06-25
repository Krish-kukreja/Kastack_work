import sys
import re
import csv
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.parent
INPUT_DIR = BASE_DIR / "round2" / "drift" / "_input"
INPUT_DIR.mkdir(parents=True, exist_ok=True)
TXT_FILE = INPUT_DIR / "chat.txt"
CSV_FILE = INPUT_DIR / "chat.csv"
OUT_FILE = BASE_DIR / "round2" / "drift" / "real_messages.jsonl"

def parse_whatsapp_date(date_str, time_str):
    date_str = date_str.strip()
    time_str = time_str.strip()
    date_formats = ["%d/%m/%Y", "%m/%d/%y", "%d/%m/%y", "%m/%d/%Y"]
    time_formats = ["%H:%M", "%I:%M %p", "%I:%M %P"]
    
    for df in date_formats:
        for tf in time_formats:
            try:
                return datetime.strptime(f"{date_str} {time_str}", f"{df} {tf}")
            except ValueError:
                pass
    return None

def parse_txt(file_path):
    pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}(?: [aApP][mM])?) - (.*?): (.*)$")
    system_pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}(?: [aApP][mM])?) - (.*)$")
    
    messages = []
    current_msg = None
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            m = pattern.match(line)
            if m:
                d_str, t_str, sender, text = m.groups()
                dt = parse_whatsapp_date(d_str, t_str)
                if dt:
                    if current_msg:
                        messages.append(current_msg)
                    current_msg = {"dt": dt, "sender": sender.strip(), "message_text": text}
                else:
                    if current_msg:
                        current_msg["message_text"] += "\n" + line
            else:
                m_sys = system_pattern.match(line)
                if m_sys:
                    if current_msg:
                        messages.append(current_msg)
                        current_msg = None
                else:
                    if current_msg:
                        current_msg["message_text"] += "\n" + line
                        
    if current_msg:
        messages.append(current_msg)
        
    return messages

def parse_csv(file_path):
    messages = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "date" in row and "sender" in row and "text" in row:
                try:
                    dt = datetime.fromisoformat(row["date"])
                    messages.append({"dt": dt, "sender": row["sender"].strip(), "message_text": row["text"]})
                except ValueError:
                    pass
    return messages

def main():
    if not TXT_FILE.exists() and not CSV_FILE.exists():
        print("Export a WhatsApp chat: open the chat -> ... -> More -> Export chat -> WITHOUT media -> save the .txt to round2/drift/_input/chat.txt")
        sys.exit(0)
        
    if TXT_FILE.exists():
        messages = parse_txt(TXT_FILE)
    else:
        messages = parse_csv(CSV_FILE)
        
    if not messages:
        print("No valid messages found.")
        sys.exit(0)
        
    messages.sort(key=lambda x: x["dt"])
    first_dt = messages[0]["dt"]
    
    senders = set()
    rows_parsed = 0
    
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for m in messages:
            day = (m["dt"] - first_dt).days + 1
            week = (day - 1) // 7 + 1
            sender = m["sender"]
            senders.add(sender)
            
            record = {
                "day": day,
                "week": week,
                "date": m["dt"].isoformat(),
                "sender": sender,
                "message_text": m["message_text"]
            }
            f.write(json.dumps(record) + "\n")
            rows_parsed += 1
            
    print(f"Parsed rows: {rows_parsed}")
    print(f"Senders found: {', '.join(senders)}")
    print(f"Saved to {OUT_FILE}")

if __name__ == "__main__":
    main()
