import httpx
from config import Settings

settings = Settings()

class LLMClient:

    async def ask(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.MODEL_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.MODEL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": settings.TEMPERATURE,
                    "top_p": settings.TOP_P,
                }
            )
            
            # Example response:
            #{
            #   "id": "...",
            #   "choices": [
            #     {
            #       "message": {
            #         "role": "...",
            #         "content": "..."
            #       }
            #     }
            #   ]
            # }

            data = response.json()

            return data["choices"][0]["message"]["content"]
