"""message_system stub (SYS-NORM修复)."""
class MessageSystem:
    def send(self, *a, **kw): return True
    def broadcast(self, *a, **kw): return True
message_system = MessageSystem()
