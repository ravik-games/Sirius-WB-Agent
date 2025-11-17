from pydantic import BaseModel, Field
from typing import List, Literal, Any


class ChatRequest(BaseModel):
    user_id: str | None = Field(None, description="ID пользователя")
    text: str = Field(..., description="Сообщение пользователя")


class MessageEntry(BaseModel):
    sender: Literal["user", "tina"]
    content: Any


class ChatResponse(BaseModel):
    user_id: str
    reply: Any
    history: List[MessageEntry]

class RunAgentRequest(BaseModel):
    user_id: str

