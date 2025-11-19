from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
from typing import List, Dict, Any

from nadziratel import LLMNadziratel

app = FastAPI(title="Nadziratel Analysis Service")

llm_client = LLMNadziratel()

class HealthResponse(BaseModel):
    status: str

class AnalysisResponse(BaseModel):
    result: str
    status: str

class StepAnalysisRequest(BaseModel):
    steps: List[Dict[str, Any]]

@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}

# @app.post("/analyze-sequence")
# async def analyze_sequence(request: StepAnalysisRequest):
#     """
#     Анализирует последовательность шагов агента.
    
#     Args:
#         request: JSON с шагами агента {description, image_base64}
    
#     Returns:
#         AnalysisResponse с результатом анализа
#     """
#     try:
#         # Проверяем валидность base64 для всех изображений
#         for step in request.steps:
#             if 'image_base64' in step:
#                 base64.b64decode(step['image_base64'], validate=True)
        
#         # Анализируем последовательность
#         result = await llm_client.analyze_agent_steps(
#             steps=request.steps
#         )
        
#         return result

# @app.post("/analyze-sequence")
# async def analyze_sequence(request: StepAnalysisRequest):
#     """
#     Анализирует последовательность шагов агента.
    
#     Args:
#         request: JSON с шагами агента {descriptions, images_base64}
#     """
#     try:
#         # Разделяем описания и картинки
#         descriptions = []
#         images_base64 = []
        
#         for step in request.steps:
#             # Разделяем описания по переносам строк
#             step_descriptions = step['description'].strip().split('\n')
#             descriptions.extend([desc.strip() for desc in step_descriptions if desc.strip()])
            
#             # Разделяем картинки по переносам строк
#             step_images = step['image_base64'].strip().split('\n')
#             images_base64.extend([img.strip() for img in step_images if img.strip()])
        
#         # Проверяем что количество описаний и картинок совпадает
#         if len(descriptions) != len(images_base64):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Количество описаний ({len(descriptions)}) не совпадает с количеством картинок ({len(images_base64)})"
#             )
        
#         # Проверяем валидность base64
#         for img_base64 in images_base64:
#             base64.b64decode(img_base64, validate=True)
        
#         # Создаем нормализованные шаги
#         normalized_steps = []
#         for i, (desc, img) in enumerate(zip(descriptions, images_base64)):
#             normalized_steps.append({
#                 "description": desc,
#                 "image_base64": img
#             })
        
#         # Анализируем последовательность
#         result = await llm_client.analyze_agent_steps(
#             steps=normalized_steps
#         )
        
#         return result
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Ошибка при обработке запроса: {str(e)}"
#         )
        
#     except base64.binascii.Error:
#         raise HTTPException(status_code=400, detail="Невалидный base64 в одном из изображений")
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Ошибка при обработке запроса: {str(e)}"
#         )

class StepAnalysisRequest(BaseModel):
    descriptions: str  # "шаг1\nшаг2\nшаг3"
    images_base64: str # "img1\nimg2\nimg3"

@app.post("/analyze-sequence")
async def analyze_sequence(request: StepAnalysisRequest):
    """
    Анализирует последовательность шагов агента.
    Принимает прямые поля с переносами строк.
    """
    try:
        # Разделяем по переносам строк
        descriptions = [desc.strip() for desc in request.descriptions.split('\n') if desc.strip()]
        images_base64 = [img.strip() for img in request.images_base64.split('\n') if img.strip()]
        
        if len(descriptions) != len(images_base64):
            raise HTTPException(status_code=400, detail="Количество описаний и картинок не совпадает")
        
        # Проверяем base64
        for img_base64 in images_base64:
            base64.b64decode(img_base64, validate=True)
        
        # Создаем шаги
        normalized_steps = []
        for desc, img in zip(descriptions, images_base64):
            normalized_steps.append({
                "description": desc,
                "image_base64": img
            })
        
        result = await llm_client.analyze_agent_steps(steps=normalized_steps)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8300)