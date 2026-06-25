"""Instant pass/fail smoke test for all Round 2 features.

Run from the backend/ directory:
    cd backend && python -m round2.smoke_test

Checks the LOGIC of every feature in ~10s (no server boot, no 294MB embeddings).
For the full HTTP/UI surface, boot the server and use the Insights page.
"""
import json

from round2.intent import classify
from round2.affect import emotion
from round2.paths import ROUND2_DIR

GREEN, RED, RESET = "\033[92m", "\033[91m", "\033[0m"
results = []


def check(name, ok, detail=""):
    tag = f"{GREEN}[PASS]{RESET}" if ok else f"{RED}[FAIL]{RESET}"
    print(f"{tag} {name}" + (f"   ({detail})" if detail and not ok else ""))
    results.append(ok)


print("\n===== INTENT CLASSIFIER =====")
intent_cases = [
    ("remind me to call mom at 6", "reminder"),
    ("ive been feeling really low since the breakup", "emotional-support"),
    ("we need to finalize the budget and send it to finance by friday", "action-item"),
    ("asldkfj qwerty zzz", "unknown"),
    ("the mitochondria is the powerhouse of the cell", "unknown"),
]
for text, expected in intent_cases:
    got = classify.classify(text)["label"]
    check(f"{text[:45]!r} -> {got}", got == expected, f"expected {expected}")

print("\n===== AFFECT / EMOTION =====")


def top_axis(s):
    return max(["curiosity", "frustration", "playfulness"], key=lambda k: s[k])


affect_cases = [
    ("I am so frustrated today, nothing works", "frustration", "neg"),
    ("haha this is so much fun lol", "playfulness", "pos"),
    ("Why does this happen? How does it actually work?", "curiosity", None),
]
for text, axis, sign in affect_cases:
    s = emotion.score(text)
    ok_axis = top_axis(s) == axis
    ok_sign = True if sign is None else (s["valence"] < 0 if sign == "neg" else s["valence"] > 0)
    check(f"{text[:40]!r} -> top={top_axis(s)}, val={s['valence']:+.2f}", ok_axis and ok_sign, f"expected {axis}")

print("\n===== PERSONA DRIFT =====")
drift = json.loads((ROUND2_DIR / "drift" / "timeline_with_triggers.json").read_text(encoding="utf-8"))
real_moods = {s["dominant_mood"] for s in drift["real_data_segments"]}
demo_moods = [s["dominant_mood"] for s in drift["demo_arc_segments"]]
check(f"real data is honestly FLAT (one mood: {real_moods})", len(real_moods) == 1)
check(f"demo arc SWINGS {demo_moods}", "frustration-negative" in demo_moods and "playfulness-positive" in demo_moods)

print("\n===== CONFLICT-RAG (subject extraction) =====")
from round2.rag import conflict_resolver  # noqa: E402 (heavy import, kept local)
for q, expected in [("how do I feel about my sister", "sister"),
                    ("what did I say about my job", "job")]:
    got = conflict_resolver.extract_subject(q)
    check(f"{q!r} -> {got}", got == expected, f"expected {expected}")

print("\n===== SYNC (CRDT) =====")
from round2.sync.device import Device  # noqa: E402
a, b = Device("a"), Device("b")
a.write("x")
b.write("y")
a.receive(b.export())
b.receive(a.export())
check("two offline devices converge with no data loss", a.state() == b.state() and len(a.state()) == 2)

print("\n" + "=" * 50)
n = len(results)
if all(results):
    print(f"{GREEN}>>> ALL {n} CHECKS PASSED - everything is working.{RESET}")
else:
    print(f"{RED}>>> {n - sum(results)}/{n} CHECKS FAILED - see [FAIL] lines above.{RESET}")
