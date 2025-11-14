from typing import List, Optional
from pydantic import BaseModel, Field


class ItemSpec(BaseModel):
    """Один товар"""
    name: str = Field(..., description="Название")
    color: Optional[str] = Field(None, description="Цвет")
    size: Optional[str] = Field(None, description="Размер")


class Action(BaseModel):
    """Действие"""
    type: str = Field(..., description="Тип действия")
    url: Optional[str] = Field(None, description="URL")
    query: Optional[str] = Field(None, description="Запрос для поиска")
    index: Optional[int] = Field(None, description="Необходимый индекс")
    target: Optional[str] = Field(None, description="Куда кликать")


class ParsedIntent(BaseModel):
    """Результат анализа"""
    goal: str = Field(..., description="Цель пользователя")
    items: List[ItemSpec] = Field(..., description="Список найденных товаров")
    actions: List[Action] = Field(..., description="План действий для агента")
    

class IntentParseRequest(BaseModel):
    """Зарос пользователя"""
    text: str = Field(..., description="Запрос пользователя")
    user_id: Optional[str] = Field(None, description="ID пользователя")


class IntentParseResponse(BaseModel):
    """Ответ на запрос"""
    parsed_intent: ParsedIntent = Field(..., description="Ответ")
    



    