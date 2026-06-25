from round2.sync.device import Device

def run_demo():
    print("--- CRDT SYNC DEMO ---")
    phone = Device("phone")
    laptop = Device("laptop")
    
    print("\n1. OFFLINE WRITES")
    # Phone writes
    p1 = phone.write("Phone entry A")
    p2 = phone.write("Phone entry B")
    
    # Laptop writes
    l1 = laptop.write("Laptop entry C")
    l2 = laptop.write("Laptop entry D")
    
    print("Phone state:", [e.text for e in phone.state()])
    print("Laptop state:", [e.text for e in laptop.state()])
    
    print("\n2. SYNC")
    phone.receive(laptop.export())
    laptop.receive(phone.export())
    
    print("Phone state after sync:", [e.text for e in phone.state()])
    print("Laptop state after sync:", [e.text for e in laptop.state()])
    print("Convergence achieved:", phone.state() == laptop.state())
    
    print("\n3. TOMBSTONE DELETION")
    print(f"Phone deleting Laptop's entry: '{l1.text}'")
    phone.delete(l1.id)
    
    print("Phone state after delete:", [e.text for e in phone.state()])
    print("Laptop state before sync:", [e.text for e in laptop.state()])
    
    print("\n4. SYNC AGAIN")
    laptop.receive(phone.export())
    phone.receive(laptop.export())
    
    print("Phone state after 2nd sync:", [e.text for e in phone.state()])
    print("Laptop state after 2nd sync:", [e.text for e in laptop.state()])
    print("Convergence achieved:", phone.state() == laptop.state())
    print("Did tombstone resurrect?", any(e.id == l1.id for e in phone.state()))
    
    print("\n5. PROOF")
    print("phone.state() == laptop.state() ->", phone.state() == laptop.state())

if __name__ == "__main__":
    run_demo()
