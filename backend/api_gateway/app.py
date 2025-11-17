import uuid
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json 

from storage import Storage
from schemas import ChatRequest, ChatResponse
from config import INTENT_FILTER_URL, AGENT_URL


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
    
    
@app.post("/chat/stream")
async def stream_all_products(payload: dict):
    
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(400, "user_id required")

    # стартуем агента (может быть уже запущен)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{AGENT_URL}/agent/startup")
    except:
        pass

    async def product_stream():

        # --- цикл по продуктам ---
        while storage.has_products(user_id):

            product = storage.pop_product(user_id)
            if not product:
                break

            yield (json.dumps({
                "event": "start_product",
                "product": product
            }) + "\n").encode()

            # --- вызов агента ---
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.post(
                    f"{AGENT_URL}/agent/query",
                    json={"query": product, "messages": []},
                    timeout=None
                )
                resp.raise_for_status()

                async for raw_line in resp.aiter_lines():
                    if not raw_line:
                        continue
                    try:
                        data = json.loads(raw_line)
                    except:
                        continue

                    # --- image ---
                    if data.get("type") == "image":
                        yield (json.dumps({
                            "event": "image",
                            "url": data["url"]
                        }) + "\n").encode()

                    # --- text ---
                    elif data.get("type") == "text":
                        yield (json.dumps({
                            "event": "text",
                            "content": data["content"]
                        }) + "\n").encode()

                    # --- конец продукта ---
                    elif data.get("status") == "end":

                        # сохраняем полноценного кандидата
                        storage.add_candidate(user_id, {
                            "product": product,
                            "result": data.get("result"),      # если есть
                        })

                        yield (json.dumps({
                            "event": "end_product",
                            "product": product
                        }) + "\n").encode()

                        # если накопилось 3 кандидата → прерываем стрим
                        if len(storage.get_candidates(user_id)) >= 3:
                            yield (json.dumps({
                                "event": "need_clarification",
                                "candidates": storage.get_candidates(user_id)
                            }) + "\n").encode()
                            return

                        break

        # --- если товары кончились, но кандидатов < 3 ---
        yield (json.dumps({
            "event": "all_done"
        }) + "\n").encode()

    return StreamingResponse(product_stream(), media_type="application/x-jsonl")



@app.post("/agent/start")
async def start_agent():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{AGENT_URL}/agent/startup")
            resp.raise_for_status()
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Agent startup failed: {err}")

    return resp.json()


@app.post("/agent/run")
async def run_agent(payload: dict):

    query = payload.get("query")
    messages = payload.get("messages", [])

    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(
            f"{AGENT_URL}/agent/query",
            json={"query": query, "messages": messages},
            timeout=None
        )
        resp.raise_for_status()

    return StreamingResponse(resp.aiter_raw(), media_type="application/x-jsonl")
