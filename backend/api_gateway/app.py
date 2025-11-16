import uuid
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import ChatRequest, ChatResponse
from session_manager import SessionManager
from config import INTENT_FILTER_URL


app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


sessions = SessionManager()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    user_id = request.user_id or str(uuid.uuid4())

    # Добавляем сообщение пользователя
    sessions.add(user_id, "user", request.text)

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(INTENT_FILTER_URL, json={"text": request.text})
            
        response.raise_for_status()
        
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

    intent_reply = response.json()

    # Сохраняем ответ сервиса
    sessions.add(user_id, "tina", intent_reply)

    return ChatResponse(
        user_id=user_id,
        reply=intent_reply,
        history=sessions.get(user_id)
    )
    