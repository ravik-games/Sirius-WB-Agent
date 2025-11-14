from pydantic import BaseModel, Field


class LocateRequest(BaseModel):
    """Запрос для скриншота"""
    image: str = Field(..., description="Скриншот")
    action: str = Field(..., description="Команда для поиска")


class BBox(BaseModel):
    """координаты BBox"""
    x1: int = Field(..., description="Левая координата")
    y1: int = Field(..., description="Верхняя координата")
    x2: int = Field(..., description="Правая координата")
    y2: int = Field(..., description="Нижняя координата")


class LocateResponse(BaseModel):
    bbox: BBox = Field(..., description="Координаты найденного элемента")