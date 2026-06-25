from round2.sync.device import Device
from round2.sync.merge import merge

def test_no_loss():
    d1 = Device("d1")
    d2 = Device("d2")
    
    d1.write("Hello")
    d1.write("World")
    
    d2.write("Foo")
    d2.write("Bar")
    
    d1.receive(d2.export())
    d2.receive(d1.export())
    
    assert len(d1.state()) == 4
    assert len(d2.state()) == 4
    
def test_convergence():
    d1 = Device("d1")
    d2 = Device("d2")
    
    d1.write("1")
    d2.write("2")
    
    d1.receive(d2.export())
    d2.receive(d1.export())
    
    assert d1.state() == d2.state()
    
def test_tombstone():
    d1 = Device("d1")
    d2 = Device("d2")
    
    e1 = d1.write("test")
    d2.receive(d1.export())
    
    # d2 deletes
    d2.delete(e1.id)
    
    # d1 syncs
    d1.receive(d2.export())
    
    # Should be gone from active state
    assert len(d1.state()) == 0
    assert len(d2.state()) == 0
    # But log has tombstone
    assert len(d1.log) == 1
    assert d1.log[e1.id].deleted is True
    
def test_commutative_idempotent():
    d1 = Device("d1")
    d2 = Device("d2")
    
    d1.write("a")
    d2.write("b")
    
    log1 = d1.export()
    log2 = d2.export()
    
    # Commutative: merge(A, B) == merge(B, A)
    assert merge(log1, log2) == merge(log2, log1)
    
    # Idempotent: merge(A, A) == A
    assert merge(log1, log1) == log1
