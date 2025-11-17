from typing import Dict, List, Any
from schemas import MessageEntry

class Storage:
    
    def __init__(self):
        self.history: Dict[str, List[MessageEntry]] = {}
        self.states: dict[str, dict] = {}
        self.pending_products: Dict[str, List[dict]] = {}
        

    def add_message(self, user_id: str, sender: str, content: Any):
        self.history.setdefault(user_id, []).append(MessageEntry(sender=sender, content=content))


    def get_messages(self, user_id: str) -> List[MessageEntry]:
        return self.history.get(user_id, [])


    def get_state(self, user_id: str):
        return self.states.get(user_id, {"original_text": None, "awaiting_clarification": False})
    
    
    def set_state(self, user_id: str, new_state: dict):
        self.states[user_id] = new_state
        

    def set_products(self, user_id: str, intent):
        self.pending_products = intent.get("products", [])
        self.history.setdefault(user_id, [])
        
    def has_products(self, user_id: str) -> bool:
        return bool(self.pending_products.get(user_id))
        
    
    def pop_product(self, user_id: str):
        items = self.pending_products.get(user_id, [])
        if not items:
            return None
        return items.pop(0)
    






    