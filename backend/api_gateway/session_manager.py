from typing import Dict, List, Any
from schemas import MessageEntry

class SessionManager:
    
    def __init__(self):
        self.sessions: Dict[str, List[MessageEntry]] = {}
        

    def add(self, user_id: str, sender: str, content: Any):
        if user_id not in self.sessions:
            self.sessions[user_id] = []

        self.sessions[user_id].append(
            MessageEntry(sender=sender, content=content)
        )

    def get(self, user_id: str) -> List[MessageEntry]:
        return self.sessions.get(user_id, [])
