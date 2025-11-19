import json
from prompts import INTENT_CLASSIFY_PROMPT
import re

STOP_WORDS = {"ищи"}

class IntentClassifier:
    """
    - Поддержка multimodal input (текст + base64 картинка)
    """

    def __init__(self, llm):
        self.prompt = INTENT_CLASSIFY_PROMPT
        self.llm = llm


    # ---------- Вспомогательный метод ----------
    def _extract_text_and_image(self, raw: str):
        """
        Вытаскиваем <image>...</image>
        """

        img_match = re.search(r"<image>(.*?)</image>", raw)
        if not img_match:
            return raw.strip(), None

        image = img_match.group(1).strip()
        text = raw.replace(img_match.group(0), "").strip()
        return text, image


    # ---------- Запрос к модели ----------
    async def ask_model(self, raw_user_input: str):
        """
        raw_user_input — это то, что лежит в state.original_text,
        там уже может быть картинка.
        """

        text, image = self._extract_text_and_image(raw_user_input)

        # --- 1. Если есть картинка → шлём мультимодальный prompt ---
        if image:
            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Пользовательский запрос: {text}"},
                    {"type": "input_image", "image": image}
                ]}
            ]

            raw = await self.llm.ask(messages, multimodal=True)

        else:
            # --- 2. Обычный текстовый запрос ---
            prompt = self.prompt + f"\n\nПользовательский запрос: {text}"
            raw = await self.llm.ask(prompt)

        # --- 3. Пробуем разобрать JSON ---
        try:
            data = json.loads(raw)

            if not isinstance(data, dict):
                raise ValueError("LLM returned non-dict JSON")

            if "relevant" not in data:
                return {"relevant": False}

            return data

        except Exception as e:
            print("IntentClassifier error:", e, "RAW:", raw)
            return {"relevant": False}


    # ---------- Основная логика ----------
    async def classify(self, user_text: str, state):

        # ======= 1. Команда "ищи" =======
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

        # ======= 2. Пользователь уточняет =======
        if state.awaiting_clarification:

            merged = state.original_text + " " + user_text
            result = await self.ask_model(merged)

            products = result.get("products", [])
            still_missing = any(p.get("missing_info") for p in products)

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
            return {"type": "final", "products": products}

        # ======= 3. Первый запрос =======
        state.original_text = user_text  # в user_text уже может быть <image>base64</image>

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
                "question": result.get("clarification_question")
            }

        state.reset()
        return {"type": "final", "products": result.get("products", [])}


class DialogueState:
    def __init__(self, original_text=None, awaiting_clarification=False):
        self.original_text = original_text
        self.awaiting_clarification = awaiting_clarification

    def reset(self):
        self.original_text = None
        self.awaiting_clarification = False
