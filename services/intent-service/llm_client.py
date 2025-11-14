import json
from models import ParsedIntent


class LLMClient:
    def __init__(self):
        pass

    async def parse_intent(self, text: str) -> ParsedIntent:
        
        prompt = self._build_prompt(text)
        response = await self._call_llm(prompt)

        data = json.loads(response)
        return ParsedIntent(**data)


    def _build_prompt(self, text: str) -> str:
        # TODO: Промпт
        pass

    async def _call_llm(self, prompt: str) -> str:
        # TODO: Вызов LLM

        items = []
        actions = []

        items.append({"name": "рубашка", "color": "жёлтая"})
        items.append({"name": "товар", "color": None})

        actions.append({"type": "open_website", "url": "https://www.wildberries.ru"})

        query = " ".join(filter(None, [items[0]["color"], items[0]["name"]]))
        actions.append({"type": "search", "query": query})

        actions.append({"type": "open_product", "index": 0})
        
        response = {
            "goal": "buy_products",
            "items": items,
            "actions": actions
        }

        return json.dumps(response, ensure_ascii=False)