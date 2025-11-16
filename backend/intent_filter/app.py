from fastapi import FastAPI
from model_client import llm_client
from classifier import IntentClassifier, DialogueState

from schemas import IntentRequest, IntentResponse


app = FastAPI(title="Intent filter service")

state = DialogueState()
classifier = IntentClassifier(llm_client)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/intent", response_model=IntentResponse)
async def intent_endpoint(msg: IntentRequest):
    result = await classifier.classify(msg.text, state)
    return result

