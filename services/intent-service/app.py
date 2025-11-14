from fastapi import FastAPI
from models import IntentParseRequest, IntentParseResponse
from llm_client import LLMClient


app = FastAPI(title="Intent service")
llm = LLMClient()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/parse_intent", response_model=IntentParseResponse)
async def parse_intent(req: IntentParseRequest):

    parsed = await llm.parse_intent(req.text)

    return IntentParseResponse(
        parsed_intent=parsed
    )

