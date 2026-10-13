from fastapi import FastAPI
from model_client import LLMClient
from classifier import IntentClassifier, DialogueState

from schemas import IntentRequest, IntentResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Intent filter service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или конкретные домены
    allow_credentials=True,
    allow_methods=["*"],  # важно!
    allow_headers=["*"],
)

state = DialogueState()
llm_client = LLMClient()
classifier = IntentClassifier(llm_client)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/intent", response_model=IntentResponse)
async def intent_endpoint(request: IntentRequest):
    state = DialogueState(
        original_text=request.state.get("original_text"),
        awaiting_clarification=request.state.get("awaiting_clarification")
    )

    result = await classifier.classify(request.text, state)

    return {
        **result,
        "state": {
            "original_text": state.original_text,
            "awaiting_clarification": state.awaiting_clarification
        }
    }
