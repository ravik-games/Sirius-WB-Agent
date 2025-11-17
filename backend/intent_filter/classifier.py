import json
from prompts import INTENT_CLASSIFY_PROMPT

STOP_WORDS = {"ищи"}


class IntentClassifier:
    """
    - Определяет релевантность маркетплейсу
    - Извлекает товары
    - Находит отсутствующие атрибуты
    - Задаёт уточняющие вопросы
    """

    def __init__(self, llm):
        self.prompt = INTENT_CLASSIFY_PROMPT
        self.llm = llm


    async def ask_model(self, text: str):
        prompt = self.prompt + f"\n\nПользовательский запрос: {text}"

        try:
            raw = await self.llm.ask(prompt)
            data = json.loads(raw)

            if not isinstance(data, dict):
                raise ValueError("JSON не dict")

            if "relevant" not in data:
                return {"relevant": False}

            return data

        except Exception as e:
            print("IntentClassifier error:", e)
            return {"relevant": False}


    async def classify(self, user_text: str, state):
        
        # =============== 1. ПОЛЬЗОВАТЕЛЬ ГОВОРИТ "ИЩИ" ===============
        if user_text.strip().lower() in STOP_WORDS:

            if not state.original_text:
                return {
                    "type": "not_relevant",
                    "message": "Мне нужно сначала понимать, что вы хотите найти."
                }

            result = await self.ask_model(state.original_text)
            
            state.reset()

            return {
                "type": "final",
                "products": result.get("products", [])
            }

        # =============== 2. ЭТО ОТВЕТ НА УТОЧНЕНИЕ ===============
        if state.awaiting_clarification:
            merged = state.original_text + ". Уточнение пользователя:" + user_text
            result = await self.ask_model(merged)

            products = result.get("products", [])

            still_missing = any(p.get("missing_info") for p in products if p.get("missing_info"))

            if still_missing:
                state.original_text = merged
                state.awaiting_clarification = True

                return {
                    "type": "clarification",
                    "question": result.get(
                        "clarification_question",
                        "Уточните недостающие параметры."
                    )
                }

            state.reset()
            return {
                "type": "final",
                "products": products
            }

        # =============== 3. ЭТО ПЕРВЫЙ ЗАПРОС ===============
        state.original_text = user_text
        result = await self.ask_model(user_text)

        if result.get("relevant") is False:
            state.reset()
            return {
                "type": "not_relevant",
                "message": "Я могу помочь подобрать товары. Что вы хотите найти или купить?"
            }

        if result.get("need_clarification"):
            state.awaiting_clarification = True

            return {
                "type": "clarification",
                "question": result.get(
                    "clarification_question",
                    "Уточните недостающие параметры."
                )
            }

        state.reset()
        return {
            "type": "final",
            "products": result.get("products", [])
        }


class DialogueState:
    def __init__(self, original_text=None, awaiting_clarification=False):
        self.original_text = original_text
        self.awaiting_clarification = awaiting_clarification

    def reset(self):
        self.original_text = None
        self.awaiting_clarification = False
