from typing import List, Optional, Literal
from pydantic import BaseModel



class IntentRequest(BaseModel):
    text: str
    

class Product(BaseModel):
    name: str
    attributes: dict
    missing_info: List[str]


class ClarificationResponse(BaseModel):
    type: Literal["clarification"]
    question: str
    products: List[Product]


class FinalResponse(BaseModel):
    type: Literal["final"]
    products: List[Product]
    message: Optional[str] = None
    forced: Optional[bool] = False


class NotRelevantResponse(BaseModel):
    type: Literal["not_relevant"]
    message: str


IntentResponse = ClarificationResponse | FinalResponse | NotRelevantResponse
