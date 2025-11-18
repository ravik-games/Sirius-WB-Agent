import httpx
import json
from typing import List, Dict, Any

from config import settings

class LLMNadziratel:
    def __init__(self):
        self.base_url = f"{settings.MODEL_URL}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {settings.MODEL_API_KEY}",
            "Content-Type": "application/json",
        }

    async def analyze_agent_steps(
        self,
        steps: List[Dict[str, Any]]
    ) -> str:
        """
        Анализирует последовательность шагов агента.

        Args:
            steps: список шагов [{"description": "...", "image_base64": "..."}]

        Returns:
            "OK" если все действия корректны и нет зацикливаний,
            "ERROR" в противном случае.
        """
        # Формируем контент с описаниями и изображениями
        content_elements = []
        
        for i, step in enumerate(steps, 1):
            # Добавляем текстовое описание шага
            content_elements.append({
                "type": "text",
                "text": f"Шаг {i}: {step.get('description', 'Нет описания')}"
            })
            
            # Добавляем изображение если есть
            if 'image_base64' in step and step['image_base64']:
                image_url = f"data:image/png;base64,{step['image_base64']}"
                content_elements.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })

        messages = [
            {
                "role": "system",
                "content": settings.ANALYSIS_PROMPT.strip()
            },
            {
                "role": "user",
                "content": content_elements
            }
        ]

        # Параметры запроса
        payload = {
            "model": settings.MODEL_NAME,
            "messages": messages,
            "temperature": settings.TEMPERATURE,
            "top_p": settings.TOP_P,
            "repetition_penalty": settings.REPETITION_PENALTY,
            "max_tokens": 1000
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"].strip()