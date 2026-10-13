from typing import List, Literal
from pydantic import BaseModel


class IntentRequest(BaseModel):
    text: str
    state: dict  # {original_text, awaiting_clarification}


class Product(BaseModel):
    name: str
    attributes: dict
    missing_info: List[str]


class ClarificationResponse(BaseModel):
    type: Literal["clarification"]
    question: str
    state: dict


class FinalResponse(BaseModel):
    type: Literal["final"]
    products: List[Product]
    state: dict


class NotRelevantResponse(BaseModel):
    type: Literal["not_relevant"]
    message: str
    state: dict
    
    
IntentResponse = ClarificationResponse | FinalResponse | NotRelevantResponse
