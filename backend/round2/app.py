import streamlit as st
import sys
from pathlib import Path
import json
import contextlib
import io

BASE_DIR = Path(__file__).parent.parent  # .../backend
sys.path.insert(0, str(BASE_DIR))        # so the round2 package is importable

from round2.intent import classify
from round2.rag import conflict_resolver

st.set_page_config(page_title="Kastack Demo", layout="wide")
st.title("Kastack Round 2 Demo")

st.warning("Data caveat: CRITICAL: The underlying data is PersonaChat. Each day/conversation_id pairs completely different people. User 1 is NOT a continuous person across days. This timeline is analyzing an artifact, not real longitudinal drift.")

# Section 1: Intent Classifier
st.header("1. Offline Intent Classifier")
intent_col1, intent_col2 = st.columns(2)
with intent_col1:
    user_text = st.text_input("Enter text to classify:")
    if st.button("Classify"):
        if user_text:
            res = classify.classify(user_text)
            st.json(res)
with intent_col2:
    st.write("Examples:")
    if st.button("Example: Reminder"):
        st.json(classify.classify("remind me to buy milk tomorrow at 5pm"))
    if st.button("Example: Emotional Support"):
        st.json(classify.classify("I feel so sad and lonely today."))
    if st.button("Example: Gibberish"):
        st.json(classify.classify("asdfasdf zxczxcvqwer"))

# Section 2: Drift
st.header("2. Persona Drift Detector")

DRIFT_DIR = BASE_DIR / 'round2' / 'drift'
timeline_path = DRIFT_DIR / 'timeline_with_triggers.json'
if not timeline_path.exists():
    timeline_path = DRIFT_DIR / 'timeline.json'

def render_segments_table(segments):
    rows = [
        "| Days | Dominant Mood | Tone | Valence | Detected Trigger |",
        "|---|---|---|---|---|",
    ]
    for s in segments:
        aff = s.get("mean_affect", {})
        trig = s.get("detected_trigger", {})
        bits = []
        if trig.get("new_entity"):
            bits.append(f"entity: **{trig['new_entity']}**")
        if trig.get("keyword_spike"):
            bits.append(f"spike: '{trig['keyword_spike']}'")
        trig_str = ", ".join(bits) if bits else "-"
        rows.append(
            f"| {s['day_range']} | {s['dominant_mood']} | {s['dominant_tone']} "
            f"| {aff.get('valence', 0):+.2f} | {trig_str} |"
        )
    return "\n".join(rows)

if timeline_path.exists():
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline_data = json.load(f)

    # --- View 1: the honest result on the data we were actually given ---
    st.subheader("On the data we were given (PersonaChat, User 1)")
    real_chart = DRIFT_DIR / 'real_drift_chart.png'
    if real_chart.exists():
        st.image(str(real_chart),
                 caption="Detector fires (dashed lines), but the three mood lines never move.")
    if "real_data_segments" in timeline_data:
        st.markdown(render_segments_table(timeline_data["real_data_segments"]))
    st.info(
        "Every segment is **curiosity-positive**, valence stuck near +0.5. The detector "
        "found change-points, but there is no real mood shift - because each PersonaChat "
        "'day' is a different pair of people. This flat result is the correct, honest answer."
    )

    # --- View 2: proof the engine works when real drift exists ---
    show_demo = st.toggle(
        "▶  Show the demo-arc validation (proof the engine detects real drift)"
    )
    if show_demo:
        st.subheader("Same engine, run on a synthetic 15-day arc with a KNOWN mood shift")
        demo_chart = DRIFT_DIR / 'drift_chart.png'
        if demo_chart.exists():
            st.image(str(demo_chart),
                     caption="The mood genuinely swings; the engine flags both change-points and the trigger.")
        if "demo_arc_segments" in timeline_data:
            st.markdown(render_segments_table(timeline_data["demo_arc_segments"]))
        st.success(
            "Here the mood truly moves: curiosity-positive → frustration-**NEGATIVE** → "
            "playfulness-positive. The engine catches both change-points (days 6 and 11) and "
            "auto-detects the 'sister' trigger. This proves the detector works when drift is real."
        )
else:
    st.error(f"{timeline_path} not found")

# Section 3: Conflict-RAG
st.header("3. Conflict-Resolution RAG")

st.subheader("Curated Demo Arc (Sister Thread)")
f = io.StringIO()
with contextlib.redirect_stdout(f):
    conflict_resolver.run_curated_demo()
st.text(f.getvalue())

@st.cache_resource
def load_rag_assets():
    return conflict_resolver.load_assets()

if st.button("Search real data (Heavy)"):
    with st.spinner("Loading assets..."):
        load_rag_assets()
    with st.spinner("Retrieving and reranking..."):
        f2 = io.StringIO()
        with contextlib.redirect_stdout(f2):
            conflict_resolver.retrieve_and_rerank(query="did I mention my sister", subject_term="sister", top_k=10)
        st.text(f2.getvalue())

# Section 4: Design
st.header("4. Sync Architecture Design")
design_path = BASE_DIR / 'round2' / 'SYNC_DESIGN.md'
if design_path.exists():
    with open(design_path, 'r', encoding='utf-8') as f:
        st.markdown(f.read())
else:
    st.error("SYNC_DESIGN.md not found")
