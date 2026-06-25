import sys
import io
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))

from round2.rag import conflict_resolver
from round2.drift.demo_arc import build_demo_arc

def test_conflict_resolution():
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    
    try:
        # Resolve conflict on sister using the known demo_msgs which contains opposing views
        demo_msgs = build_demo_arc()
        chunks = [{"day": d, "text": " ".join(msgs)} for d, msgs in demo_msgs.items()]
        conflict_resolver.resolve_conflict(chunks, "sister")
    finally:
        sys.stdout = old_stdout
        
    output = captured.getvalue()
    assert "CONTRADICTION DETECTED" in output, "Expected contradiction detected"
    assert "changed over time" in output, "Expected the merged answer to flag a change over time"
    
def test_extract_subject():
    sub = conflict_resolver.extract_subject("how do I feel about my sister")
    assert sub == "sister", f"Expected 'sister', got {sub}"
