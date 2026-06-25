"""
persona_extractor.py - Extract user personas from conversation data.

Data reality:
  - "User 1" and "User 2" are anonymized labels across 11K independent conversations
  - No timestamps → time-based metrics replaced with content-based regex
  - Personal facts are aggregate across many different individuals
  
Output: persona.json with separate User 1 / User 2 personas + meta section
"""

import json
import re
import statistics
from collections import Counter
from pathlib import Path

JSONL_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\processed_messages.jsonl")
OUTPUT_PATH = Path(r"c:\Users\iamkr\projects\Kastack\data\processed\persona.json")

# ============================================================
# PATTERN DEFINITIONS
# ============================================================

STOP_STARTS = {"so", "very", "quite", "rather", "pretty", "little", "bit", "lot", "too", "not", "just", "also", "really", "doing", "going", "trying", "getting", "having", "making", "taking", "moving", "looking", "thinking", "hoping", "planning", "definitely", "probably", "currently", "still", "always", "actually", "usually", "sometimes", "never", "ever"}
NOT_JOBS = {"nervous", "tired", "scared", "worried", "hungry", "happy", "sad", "excited", "bored", "sorry", "sure", "glad", "fine", "good", "great", "well", "okay", "ok", "sick", "busy", "interested", "curious", "afraid", "ready", "able", "home", "here", "there", "back", "away", "alone", "big fan", "huge fan", "new", "old", "young", "jealous", "lucky", "close", "impressed", "terrible", "awful", "horrible", "amazing", "wonderful", "fantastic", "proud", "grateful", "thankful", "blessed", "pleased", "certain", "confident", "comfortable", "uncomfortable", "confused", "lost", "stuck", "frustrated", "annoyed", "careful", "serious", "kidding", "joking", "telling", "open", "honest", "kind", "nice", "mean", "sweet", "right", "wrong", "crazy", "insane", "mad", "angry", "thinking about", "talking about", "looking forward", "managing", "coping", "surviving", "thriving", "free", "available", "late", "early", "different", "similar", "same", "like", "unlike"}

def clean_job(raw_job: str) -> str | None:
    job = raw_job.strip().lower()
    for prefix in ("a ", "an ", "the ", "my ", "this "):
        if job.startswith(prefix):
            job = job[len(prefix):]
    if len(job) < 3 or any(ch.isdigit() for ch in job):
        return None
    if job.split()[0] in STOP_STARTS or job in NOT_JOBS:
        return None
    return job


# Emoji detection (common Unicode emoji ranges)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\U00002600-\U000026FF"  # misc symbols
    "\U0000200D"             # zero width joiner
    "\U00002B50-\U00002B55"  # stars
    "]+",
    flags=re.UNICODE
)

# Humor markers
HUMOR_PATTERNS = re.compile(
    r'\b(lol|lmao|rofl|haha|hehe|hihi)\b|😂|🤣|😆',
    re.IGNORECASE
)

# Casual abbreviations
CASUAL_ABBREVS = re.compile(
    r'\b(u|ur|r|pls|plz|lol|omg|idk|tbh|imo|imho|ngl|brb|gtg|ttyl|smh|nvm|ikr|af|asap|btw|fyi|rn|wyd|hmu)\b',
    re.IGNORECASE
)

# URL detection
URL_PATTERN = re.compile(
    r'https?://\S+|www\.\S+',
    re.IGNORECASE
)

# @mentions
MENTION_PATTERN = re.compile(r'@\w+')

# ---- Content-based habit indicators (replacing timestamp-based) ----

LATE_SLEEP_PATTERNS = re.compile(
    r'stay(?:ing|ed)?\s+up\s+late|up\s+(?:at|until|till)\s+[0-9]+\s*(?:am|a\.m\.)'
    r'|night\s*owl|can\'?t\s+sleep|insomnia|up\s+all\s+night'
    r'|\b[2-5]\s*am\b|don\'?t\s+sleep|sleep\s+late|late\s+night'
    r'|midnight|staying\s+awake|pull(?:ing|ed)?\s+an?\s+all[\s-]?night',
    re.IGNORECASE
)

EARLY_BIRD_PATTERNS = re.compile(
    r'wake\s+up\s+early|morning\s+person|up\s+at\s+(?:4|5|6|7)\s*(?:am|a\.m\.)'
    r'|early\s+riser|love\s+mornings?|breakfast\s+person|early\s+morning'
    r'|crack\s+of\s+dawn|sunrise',
    re.IGNORECASE
)

WEEKEND_PATTERNS = re.compile(
    r'\bweekend\b|\bsaturday\b|\bsunday\b',
    re.IGNORECASE
)

WEEKDAY_PATTERNS = re.compile(
    r'\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b'
    r'|\bwork\s*week\b|\bweekday\b',
    re.IGNORECASE
)

# ---- Personal facts regex ----

NAME_PATTERNS = re.compile(
    r'(?:my\s+name\s+is|i\'?m\s+called|call\s+me|i\s+am)\s+([A-Z][a-z]+)',
    re.IGNORECASE
)

LOCATION_PATTERNS = re.compile(
    r'(?:i\s+live\s+in|i\'?m\s+from|i\s+am\s+from|moved?\s+to|living\s+in|i\s+reside\s+in'
    r'|based\s+in|grew\s+up\s+in|born\s+in|moving\s+to)\s+'
    r'([A-Z][a-zA-Z\s]{1,30}?)(?:\.|,|!|\?|\s+and\s|\s+but\s|\s+so\s|$)',
    re.IGNORECASE
)

AGE_PATTERNS = re.compile(
    r'i\s+am\s+(\d{1,2})\s+years?\s+old|i\'?m\s+(\d{1,2})\s+years?\s+old'
    r'|turning\s+(\d{1,2})|i\'?m\s+(\d{1,2})\b(?!\s*(?:am|pm|minutes?|hours?))',
    re.IGNORECASE
)

RELATIONSHIP_KEYWORDS = [
    "my boyfriend", "my girlfriend", "my husband", "my wife",
    "my mom", "my mother", "my dad", "my father",
    "my sister", "my brother", "my son", "my daughter",
    "my partner", "my fiance", "my fiancee",
    "my best friend", "my family", "my parents",
    "my grandma", "my grandmother", "my grandpa", "my grandfather",
    "my uncle", "my aunt", "my cousin"
]

JOB_PATTERNS = re.compile(
    r"\bi['']?m\s+(?:an?\s+)?([a-z\s]+?)(?:\.|,|\s+and|\s+who|\s+that|\s+at|\s+for|\s+with|$)"
    r"|\bi\s+am\s+(?:an?\s+)?([a-z\s]+?)(?:\.|,|\s+and|\s+who|\s+that|\s+at|\s+for|\s+with|$)"
    r"|(?:my\s+job\s+is|i\s+work\s+as)\s+(?:an?\s+)?([a-z\s]+?)(?:\.|,|\s+and|\s+who|\s+that|\s+at|\s+for|\s+with|$)",
    re.IGNORECASE
)

PET_KEYWORDS = {
    "dog": re.compile(r'\bmy\s+dog\b', re.IGNORECASE),
    "cat": re.compile(r'\bmy\s+cat\b', re.IGNORECASE),
    "pet": re.compile(r'\bmy\s+pet\b', re.IGNORECASE),
    "fish": re.compile(r'\bmy\s+fish\b', re.IGNORECASE),
    "bird": re.compile(r'\bmy\s+bird\b', re.IGNORECASE),
    "hamster": re.compile(r'\bmy\s+hamster\b', re.IGNORECASE),
    "rabbit": re.compile(r'\bmy\s+rabbit\b', re.IGNORECASE),
    "horse": re.compile(r'\bmy\s+horse\b', re.IGNORECASE),
}

FOOD_PATTERNS = re.compile(
    r'(?:i\s+love|i\s+like|i\s+enjoy|my\s+favorite\s+food|i\s+prefer)\s+'
    r'(?:eating\s+|to\s+eat\s+|cooking\s+|to\s+cook\s+|making\s+|to\s+make\s+)?'
    r'([a-zA-Z\s]{2,30}?)(?:\.|,|!|\?|\s+and\s|\s+but\s|$)',
    re.IGNORECASE
)

HOBBY_PATTERNS = re.compile(
    r'(?:i\s+(?:love|like|enjoy)\s+(?:to\s+)?'
    r'|my\s+hobbies?\s+(?:is|are|include)\s+'
    r'|i\'?m\s+(?:really\s+)?into\s+)'
    r'([a-zA-Z\s]{2,40}?)(?:\.|,|!|\?|\s+and\s|\s+but\s|$)',
    re.IGNORECASE
)


# ============================================================
# EXTRACTION FUNCTIONS
# ============================================================

def extract_emojis(text: str) -> list[str]:
    """Extract all emojis from text."""
    return EMOJI_PATTERN.findall(text)


def compute_communication_style(messages: list[str]) -> dict:
    """Compute quantitative communication style metrics."""
    total = len(messages)
    if total == 0:
        return {}

    lengths = [len(m) for m in messages]
    
    # Emoji stats
    all_emojis = []
    msgs_with_emoji = 0
    for m in messages:
        emojis = extract_emojis(m)
        all_emojis.extend(emojis)
        if emojis:
            msgs_with_emoji += 1

    emoji_counts = Counter(all_emojis)
    top_emojis = [{"emoji": e, "count": c} for e, c in emoji_counts.most_common(10)]

    # Punctuation stats
    msgs_with_excl = sum(1 for m in messages if "!" in m)
    msgs_with_ques = sum(1 for m in messages if "?" in m)

    # Caps usage (>50% uppercase)
    msgs_with_caps = 0
    for m in messages:
        alpha_chars = [c for c in m if c.isalpha()]
        if alpha_chars and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > 0.5:
            msgs_with_caps += 1

    return {
        "avg_message_length": round(statistics.mean(lengths), 1),
        "median_message_length": round(statistics.median(lengths), 1),
        "message_length_variance": round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0.0,
        "emoji_usage_rate": round(msgs_with_emoji / total, 4),
        "top_emojis": top_emojis,
        "exclamation_rate": round(msgs_with_excl / total, 4),
        "question_rate": round(msgs_with_ques / total, 4),
        "caps_usage_rate": round(msgs_with_caps / total, 4),
        "response_time_avg_seconds": None,  # Impossible: no timestamps
        "messages_per_conversation": round(total / max(1, 1), 1),  # filled later
        "most_active_hour": None,  # Impossible: no timestamps
        "activity_pattern": "unknown_no_timestamps",
        "media_sharing_rate": 0.0  # No media in dataset
    }


def compute_habits(messages: list[str], num_conversations: int) -> dict:
    """Compute habits using content-based detection (not timestamps)."""
    total = len(messages)
    if total == 0:
        return {}

    avg_len = statistics.mean(len(m) for m in messages)

    # Content-based time indicators
    late_sleep_mentions = sum(1 for m in messages if LATE_SLEEP_PATTERNS.search(m))
    early_bird_mentions = sum(1 for m in messages if EARLY_BIRD_PATTERNS.search(m))
    weekend_mentions = sum(1 for m in messages if WEEKEND_PATTERNS.search(m))
    weekday_mentions = sum(1 for m in messages if WEEKDAY_PATTERNS.search(m))
    url_messages = sum(1 for m in messages if URL_PATTERN.search(m))
    mention_messages = sum(1 for m in messages if MENTION_PATTERN.search(m))

    msgs_per_convo = total / max(num_conversations, 1)

    return {
        "late_sleeper": {
            "detected": late_sleep_mentions > 0,
            "evidence_count": late_sleep_mentions,
            "method": "content_regex (no timestamps available)"
        },
        "early_bird": {
            "detected": early_bird_mentions > 0,
            "evidence_count": early_bird_mentions,
            "method": "content_regex (no timestamps available)"
        },
        "frequent_sender": msgs_per_convo > 10,
        "brief_communicator": avg_len < 20,
        "verbose_communicator": avg_len > 150,
        "weekend_active": {
            "detected": weekend_mentions > weekday_mentions,
            "weekend_mentions": weekend_mentions,
            "weekday_mentions": weekday_mentions,
            "method": "content_regex (no timestamps available)"
        },
        "link_sharer": round(url_messages / total, 4) > 0.05,
        "link_sharing_rate": round(url_messages / total, 4),
        "mentions_others_often": round(mention_messages / total, 4) > 0.20,
        "mention_rate": round(mention_messages / total, 4)
    }


def compute_personality_traits(messages: list[str]) -> dict:
    """Compute personality traits from linguistic markers."""
    total = len(messages)
    if total == 0:
        return {}

    # Humor
    humor_msgs = sum(1 for m in messages if HUMOR_PATTERNS.search(m))

    # Emoji rate (recompute for threshold check)
    emoji_msgs = sum(1 for m in messages if EMOJI_PATTERN.search(m))

    # Question rate
    question_msgs = sum(1 for m in messages if "?" in m)

    # Exclamation rate
    excl_msgs = sum(1 for m in messages if "!" in m)

    # Caps rate
    caps_msgs = 0
    for m in messages:
        alpha = [c for c in m if c.isalpha()]
        if alpha and sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.5:
            caps_msgs += 1

    # Casual abbreviation rate
    casual_msgs = sum(1 for m in messages if CASUAL_ABBREVS.search(m))

    # Compute rates
    humor_rate = humor_msgs / total
    emoji_rate = emoji_msgs / total
    question_rate = question_msgs / total
    excl_rate = excl_msgs / total
    caps_rate = caps_msgs / total
    casual_rate = casual_msgs / total
    avg_len = statistics.mean(len(m) for m in messages)

    return {
        "funny": {
            "detected": humor_rate > 0.05,
            "rate": round(humor_rate, 4),
            "threshold": 0.05
        },
        "expressive": {
            "detected": emoji_rate > 0.10,
            "rate": round(emoji_rate, 4),
            "threshold": 0.10
        },
        "curious": {
            "detected": question_rate > 0.15,
            "rate": round(question_rate, 4),
            "threshold": 0.15
        },
        "enthusiastic": {
            "detected": excl_rate > 0.20,
            "rate": round(excl_rate, 4),
            "threshold": 0.20
        },
        "intense": {
            "detected": caps_rate > 0.05,
            "rate": round(caps_rate, 4),
            "threshold": 0.05
        },
        "formal": {
            "detected": avg_len > 100 and emoji_rate < 0.01 and casual_rate < 0.05,
            "avg_length": round(avg_len, 1),
            "emoji_rate": round(emoji_rate, 4),
            "casual_rate": round(casual_rate, 4)
        },
        "casual": {
            "detected": casual_rate > 0.10,
            "rate": round(casual_rate, 4),
            "threshold": 0.10
        }
    }


def extract_personal_facts(messages: list[str]) -> dict:
    """Extract personal facts using regex patterns only."""
    # Names
    names = []
    for m in messages:
        found = NAME_PATTERNS.findall(m)
        names.extend(found)
    name_counts = Counter(n.strip() for n in names if len(n.strip()) > 1)

    # Locations
    locations = []
    for m in messages:
        found = LOCATION_PATTERNS.findall(m)
        locations.extend(found)
    location_counts = Counter(loc.strip().rstrip('.!?,') for loc in locations if len(loc.strip()) > 1)

    # Ages
    ages = []
    for m in messages:
        found = AGE_PATTERNS.findall(m)
        for groups in found:
            for g in groups:
                if g and g.isdigit() and 10 <= int(g) <= 100:
                    ages.append(g)
    age_counts = Counter(ages)

    # Relationships
    rel_counts = {}
    for kw in RELATIONSHIP_KEYWORDS:
        count = sum(1 for m in messages if kw.lower() in m.lower())
        if count > 0:
            label = kw.replace("my ", "")
            rel_counts[label] = count

    # Jobs
    jobs = []
    for m in messages:
        found = JOB_PATTERNS.findall(m)
        for groups in found:
            if isinstance(groups, str):
                g = groups
            else:
                g = next((x for x in groups if x), "")
            cleaned = clean_job(g.rstrip('.!?,'))
            if cleaned:
                jobs.append(cleaned)
    job_counts = Counter(jobs)

    # Pets
    pet_counts = {}
    for pet_type, pattern in PET_KEYWORDS.items():
        count = sum(1 for m in messages if pattern.search(m))
        if count > 0:
            pet_counts[pet_type] = count

    # Food mentions
    food_mentions = []
    for m in messages:
        found = FOOD_PATTERNS.findall(m)
        food_mentions.extend(f.strip().rstrip('.!?,') for f in found if len(f.strip()) > 2)
    food_counts = Counter(food_mentions)

    # Hobbies
    hobbies = []
    for m in messages:
        found = HOBBY_PATTERNS.findall(m)
        hobbies.extend(h.strip().rstrip('.!?,') for h in found if len(h.strip()) > 2)
    hobby_counts = Counter(hobbies)

    return {
        "name_mentions": dict(name_counts.most_common(20)),
        "location_mentions": dict(location_counts.most_common(30)),
        "age_mentions": dict(age_counts.most_common(10)),
        "relationship_mentions": rel_counts,
        "job_mentions": dict(job_counts.most_common(30)),
        "pet_mentions": pet_counts,
        "food_mentions": dict(food_counts.most_common(20)),
        "hobby_mentions": dict(hobby_counts.most_common(20))
    }


def build_persona(user_label: str, messages: list[str], num_conversations: int) -> dict:
    """Build complete persona for a single user label."""
    print(f"\n  Building persona for {user_label} ({len(messages):,} messages)...")

    style = compute_communication_style(messages)
    style["messages_per_conversation"] = round(len(messages) / max(num_conversations, 1), 1)

    habits = compute_habits(messages, num_conversations)
    traits = compute_personality_traits(messages)
    facts = extract_personal_facts(messages)

    return {
        "user_id": user_label,
        "total_messages_analyzed": len(messages),
        "communication_style": style,
        "habits": habits,
        "personality_traits": traits,
        "personal_facts": facts,
        "confidence_note": (
            "All signals derived from message statistics and regex patterns. "
            "No LLM inference used. Time-based metrics (response_time, active_hour, "
            "activity_pattern) are IMPOSSIBLE due to lack of timestamps and set to null. "
            "Habits like late_sleeper/early_bird are detected from message CONTENT "
            "(e.g., 'I stay up late') not from message timestamps. "
            "Personal facts are aggregate across ~11K different individuals "
            "(each conversation features different people labeled User 1/User 2)."
        )
    }


def main():
    print("=" * 70)
    print("LOADING MESSAGES")
    print("=" * 70)

    from collections import defaultdict
    conversations = defaultdict(list)
    total_messages = 0

    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            m = json.loads(line)
            conversations[m["conversation_id"]].append(m)
            total_messages += 1

    num_convos = len(conversations)
    print(f"  Total messages: {total_messages:,}")
    print(f"  Unique conversations: {num_convos:,}")

    # Build global personas
    print()
    print("=" * 70)
    print("EXTRACTING GLOBAL PERSONAS")
    print("=" * 70)

    user1_msgs = []
    user2_msgs = []
    
    for group in conversations.values():
        for m in group:
            text = m.get("message_text", "") or m.get("text", "")
            if text:
                if m.get("sender") == 'User 1':
                    user1_msgs.append(text)
                elif m.get("sender") == 'User 2':
                    user2_msgs.append(text)

    persona_user_1 = build_persona('User 1', user1_msgs, num_convos)
    persona_user_2 = build_persona('User 2', user2_msgs, num_convos)

    all_personas = {
        "meta": {
            "total_messages_user_1": len(user1_msgs),
            "total_messages_user_2": len(user2_msgs),
            "total_conversations": num_convos
        },
        "persona_user_1": persona_user_1,
        "persona_user_2": persona_user_2
    }

    # Save
    print()
    print("=" * 70)
    print("SAVING")
    print("=" * 70)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_personas, f, ensure_ascii=False, indent=2)

    file_size = OUTPUT_PATH.stat().st_size / 1024
    print(f"  Saved to: {OUTPUT_PATH}")
    print(f"  File size: {file_size:.1f} KB")

if __name__ == "__main__":
    main()
