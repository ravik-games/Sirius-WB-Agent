from typing import Dict, List, Any
from schemas import MessageEntry


class Storage:
    
    def __init__(self):
        self.history: Dict[str, List[MessageEntry]] = {}
        self.states: Dict[str, dict] = {}

        # Товары, которые нужно обработать агенту
        self.pending_products: Dict[str, List[dict]] = {}

        # 3 кандидата, полученные от агента
        self.candidates: Dict[str, List[dict]] = {}
        

    # ------------------------------- ДИАЛОГ -------------------------------

    def add_message(self, user_id: str, sender: str, content: Any):
        self.history.setdefault(user_id, []).append(
            MessageEntry(sender=sender, content=content)
        )

    def get_messages(self, user_id: str) -> List[MessageEntry]:
        return self.history.get(user_id, [])

    # ------------------------------- СОСТОЯНИЕ -------------------------------

    def get_state(self, user_id: str):
        return self.states.get(
            user_id,
            {"original_text": None, "awaiting_clarification": False}
        )
    
    def set_state(self, user_id: str, new_state: dict):
        self.states[user_id] = new_state

    # ------------------------------- ПРОДУКТЫ -------------------------------

    def set_products(self, user_id: str, intent: dict):
        self.pending_products[user_id] = intent.get("products", [])

    def pop_product(self, user_id: str):
        products = self.pending_products.get(user_id, [])
        if not products:
            return None
        return products.pop(0)

    # ------------------------------- КАНДИДАТЫ -------------------------------

    def set_candidates(self, user_id: str, items: List[dict]):
        self.candidates[user_id] = items

    def add_candidate(self, user_id: str, candidate: dict):
        self.candidates.setdefault(user_id, []).append(candidate)

    def get_candidates(self, user_id: str):
        return self.candidates.get(user_id, [])

    def clear_candidates(self, user_id: str):
        self.candidates[user_id] = []




    