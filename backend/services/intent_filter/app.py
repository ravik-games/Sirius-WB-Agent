from fastapi import FastAPI
from pydantic import BaseModel

from model_client import llm_client
from classifier import IntentClassifier, DialogueState


app = FastAPI(title="Intent filter service")

state = DialogueState()
classifier = IntentClassifier(llm_client)


class UserMessage(BaseModel):
    text: str

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/dialogue")
async def dialogue(msg: UserMessage):

    return await classifier.classify(msg.text, state)




