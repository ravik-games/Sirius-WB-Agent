from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import tempfile
import os
from pathlib import Path

from classificator import LLMClassificator

app = FastAPI(title="Image Analysis Service")

llm_client = LLMClassificator()

class HealthResponse(BaseModel):
    status: str

class AnalysisResponse(BaseModel):
    result: str
    status: str

@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}

# @app.post("/analyze-img", response_model=AnalysisResponse)
# async def analyze_image(
#     image: UploadFile = File(..., description="Изображение для анализа"),
#     user_query: str = Form(..., description="JSON-строка с запросом пользователя")
# ):
#     """
#     Анализирует соответствие изображения запросу пользователя.
    
#     Args:
#         image: файл изображения (PNG, JPG, JPEG)
#         user_query: JSON-строка с категорией товара и атрибутами
    
#     Returns:
#         AnalysisResponse с результатом анализа ("OK" или "ERROR")
#     """
#     # Проверяем тип файла
#     allowed_extensions = {'.png', '.jpg', '.jpeg'}
#     file_extension = Path(image.filename).suffix.lower() if image.filename else ''
    
#     if file_extension not in allowed_extensions:
#         raise HTTPException(
#             status_code=400, 
#             detail="Неподдерживаемый формат файла. Разрешены: PNG, JPG, JPEG"
#         )
    
#     # Создаем временный файл для изображения
#     try:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
#             # Читаем и записываем содержимое файла
#             content = await image.read()
#             temp_file.write(content)
#             temp_file_path = temp_file.name
        
#         # Анализируем изображение
#         result = await llm_client.analyze_image(temp_file_path, user_query)
        
#         return {
#             "result": result,
#             "status": "success"
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Ошибка при обработке изображения: {str(e)}"
#         )
#     finally:
#         # Удаляем временный файл
#         if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
#             os.unlink(temp_file_path)

@app.post("/analyze")
async def analyze_image_base64(
    image_path: str = Form(..., description="Изображение в формате base64"),
    user_query: str = Form(..., description="JSON-строка с запросом пользователя")
):
    """
    Анализирует соответствие изображения (в base64) запросу пользователя.
    """

    try:
        # Проверяем что это валидный base64
        base64.b64decode(image_base64, validate=True)
        
        result = await llm_client.analyze_image(image_base64, user_query)
        
        return {
            "result": result,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Ошибка при обработке изображения: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)