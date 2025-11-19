from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import base64

from classificator import LLMClassificator
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Image Analysis Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или конкретные домены
    allow_credentials=True,
    allow_methods=["*"],  # важно!
    allow_headers=["*"],
)

llm_client = LLMClassificator()

class HealthResponse(BaseModel):
    status: str

class AnalysisRequest(BaseModel):
    image_base64: str
    user_query: str  # JSON-строка с запросом пользователя

class AnalysisResponse(BaseModel):
    response: str
    comment: str

@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}

@app.post("/classificator", response_model=AnalysisResponse)
async def analyze_image_base64(request: AnalysisRequest):
    """
    Анализирует соответствие изображения (в base64) запросу пользователя.
    Принимает JSON в теле запроса.
    """
    try:
        # Проверяем что это валидный base64
        base64.b64decode(request.image_base64, validate=True)
        
        # Анализируем изображение
        result = await llm_client.analyze_image(request.image_base64, request.user_query)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Ошибка при обработке изображения: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)