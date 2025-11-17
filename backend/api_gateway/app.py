import uuid
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from storage import Storage
from schemas import ChatRequest, ChatResponse
from config import INTENT_FILTER_URL, PRODUCT_AGENT_URL


app = FastAPI(title="API gateway")

# для фронтенда разрешаем все источники
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: база данных
storage = Storage()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    user_id = request.user_id or str(uuid.uuid4())
    
    # сохраняем ответ пользователя
    storage.add_message(user_id, "user", request.text)
    
    # ---- Если intent уже завершён — игнорируем текст ----
    # if storage.has_products(user_id):
    #     # вместо ошибки начинаем выдавать товары автоматически
    #     next_item = storage.pop_product(user_id)
    #     return await process_product(user_id, next_item)

    state = storage.get_state(user_id)

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                INTENT_FILTER_URL,
                json={
                    "text": request.text,
                    "state": state
                }
            )
            
        response.raise_for_status()
        
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

    intent_reply = response.json()

    # сохраняем ответ тины
    storage.add_message(user_id, "tina", intent_reply)

    if "state" in intent_reply:
        storage.set_state(user_id, intent_reply["state"])

    # финальный ответ
    if intent_reply.get("type") == "final":
        storage.set_products(user_id, intent_reply)

    return ChatResponse(
        user_id=user_id,
        reply=intent_reply,
        history=storage.get_messages(user_id)
    )

