import uuid
from dataclasses import dataclass

from round2.sync.merge import merge

@dataclass
class Entry:
    id: str
    device_id: str
    lamport: int
    text: str
    deleted: bool = False

class Device:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.clock = 0
        self.log: dict[str, Entry] = {}
        
    def write(self, text: str) -> Entry:
        self.clock += 1
        entry_id = str(uuid.uuid4())
        entry = Entry(id=entry_id, device_id=self.device_id, lamport=self.clock, text=text)
        self.log[entry_id] = entry
        return entry
        
    def delete(self, entry_id: str):
        if entry_id in self.log:
            self.clock += 1
            entry = self.log[entry_id]
            # Replace with a tombstone entry
            self.log[entry_id] = Entry(
                id=entry.id, 
                device_id=self.device_id, 
                lamport=self.clock, 
                text=entry.text, 
                deleted=True
            )
            
    def export(self) -> dict[str, Entry]:
        return dict(self.log)
        
    def receive(self, remote_entries: dict[str, Entry]):
        self.log = merge(self.log, remote_entries)
        if self.log:
            max_lamport = max(e.lamport for e in self.log.values())
            self.clock = max(self.clock, max_lamport)
            
    def state(self) -> list[Entry]:
        active = [e for e in self.log.values() if not e.deleted]
        return sorted(active, key=lambda x: (x.lamport, x.id))
