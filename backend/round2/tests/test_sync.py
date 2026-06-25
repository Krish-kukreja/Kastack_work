import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))

try:
    from round2.sync.device import Device
    from round2.sync.merge import merge_logs
    SYNC_EXISTS = True
except ImportError:
    SYNC_EXISTS = False

@pytest.mark.skipif(not SYNC_EXISTS, reason="Sync module not implemented")
def test_convergence():
    d1 = Device("A")
    d2 = Device("B")
    
    d1.write("Hello")
    d2.write("World")
    
    merged = merge_logs(d1.export(), d2.export())
    
    d1.import_log(merged)
    d2.import_log(merged)
    
    assert d1.export() == d2.export(), "Logs did not converge after merge"

@pytest.mark.skipif(not SYNC_EXISTS, reason="Sync module not implemented")
def test_tombstone():
    d1 = Device("A")
    e1 = d1.write("Hello")
    d1.delete(e1.id)
    
    assert d1.log[e1.id].deleted == True, "Tombstone was not set correctly"
