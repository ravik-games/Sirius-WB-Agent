import httpx
import base64
from pathlib import Path
from typing import Union
import json

from config import settings


class LLMClassificator:
    def __init__(self):
        self.base_url = f"{settings.MODEL_URL}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {settings.MODEL_API_KEY}",
            "Content-Type": "application/json",
        }

    # def _encode_image(self, image_path: Union[str, Path]) -> str:
    #     """Кодирует изображение в base64."""
    #     with open(image_path, "rb") as f:
    #         return base64.b64encode(f.read()).decode("utf-8")

    async def analyze_image(self, image_base64: str, user_query: str) -> str:
        """
        Анализирует соответствие изображения запросу пользователя.

        Args:
            image_base64: изображение в формате base64
            user_query: JSON‑строка с запросом пользователя

        Returns:
            "OK" или "ERROR"
        """
        # Формируем data URL из base64
        image_url = f"data:image/png;base64,{image_base64}"  # ← используем image_base64 из аргументов

        # Формируем сообщения
        messages = [
            {
                "role": "system",
                "content": settings.ANALYSIS_PROMPT.strip()
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    },
                    {
                        "type": "text",
                        "text": f"Запрос пользователя: {user_query}"
                    }
                ]
            }
        ]

        # Параметры генерации
        payload = {
            "model": settings.MODEL_NAME,
            "messages": messages,
            "temperature": settings.TEMPERATURE,
            "top_p": settings.TOP_P,
            "repetition_penalty": settings.REPETITION_PENALTY,
            "max_tokens": 100
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            response_text = data["choices"][0]["message"]["content"].strip()

                
            try:
                # Парсим JSON ответ от модели
                result = json.loads(response_text)
                return result  # Уже словарь {response: "...", comment: "..."}
                
            except json.JSONDecodeError:
                # Если модель вернула не JSON, создаем структурированный ответ
                return {
                    "response": "ERROR",
                    "comment": "Неверный формат ответа от модели"
                }


    # async def analyze_image(self, image_path: Union[str, Path], user_query: str) -> str:
    #     """
    #     Анализирует соответствие изображения запросу пользователя.

    #     Args:
    #         image_path: путь к изображению
    #         user_query: JSON‑строка с запросом пользователя

    #     Returns:
    #         "OK" или "ERROR"
    #     """
    #     # Кодируем изображение
    #     image_base64 = self._encode_image(image_path)
    #     image_url = f"data:image/png;base64,{image_base64}"

    #     # Формируем сообщения
    #     messages = [
    #         {
    #             "role": "system",
    #             "content": settings.ANALYSIS_PROMPT.strip()
    #         },
    #         {
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "image_url",
    #                     "image_url": {"url": image_url}
    #                 },
    #                 {
    #                     "type": "text",
    #                     "text": f"Запрос пользователя: {user_query}"
    #                 }
    #             ]
    #         }
    #     ]

    #     # Параметры генерации
    #     payload = {
    #         "model": settings.MODEL_NAME,
    #         "messages": messages,
    #         "temperature": settings.TEMPERATURE,
    #         "top_p": settings.TOP_P,
    #         "repetition_penalty": settings.REPETITION_PENALTY,
    #         "max_tokens": 100  # Ограничиваем ответ
    #     }

    #     async with httpx.AsyncClient(timeout=30) as client:
    #         response = await client.post(
    #             self.base_url,
    #             headers=self.headers,
    #             json=payload
    #         )
    #         response.raise_for_status()
    #         data = response.json()

    #     # Извлекаем ответ
    #     return data["choices"][0]["message"]["content"].strip()


# async def analyze_image(self, image_path: Union[str, Path], user_query: str) -> str:
#     # ... подготовка payload (предыдущий код)

#     try:
#         async with httpx.AsyncClient(timeout=30) as client:
#             response = await client.post(
#                 self.base_url,
#                 headers=self.headers,
#                 json=payload
#             )
#             response.raise_for_status()
#             data = response.json()
        
#         return data["choices"][0]["message"]["content"].strip()

#     except httpx.ConnectError:
#         return "ERROR: Не удалось подключиться к серверу модели"
    
#     except httpx.TimeoutException:
#         return "ERROR: Превышено время ожидания ответа от модели"
    
#     except httpx.HTTPStatusError as e:
#         return f"ERROR: Ошибка HTTP {e.response.status_code} — {e.response.text}"
    
#     except httpx.RequestError as e:
#         return f"ERROR: Ошибка запроса: {str(e)}"
    
#     except KeyError:
#         return "ERROR: Неверный формат ответа от модели"
    
#     except Exception as e:
#         return f"ERROR: Неизвестная ошибка: {str(e)}"
