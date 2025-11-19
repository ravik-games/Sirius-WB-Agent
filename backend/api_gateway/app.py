import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json5
import json

from storage import Storage
from schemas import ChatRequest, ChatResponse, RunAgentRequest
from config import INTENT_FILTER_URL, AGENT_URL

app = FastAPI(title="API gateway")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: база данных
USER_ID = "user_1"
storage = Storage()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/agent/start")
async def start_agent():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{AGENT_URL}/agent/startup")
            resp.raise_for_status()
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Agent startup failed: {err}")

    return resp.json()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    user_id = USER_ID
    
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
    
    
@app.post("/agent/run")
async def run_agent(req: RunAgentRequest):

    user_id = req.user_id
    product = storage.pop_product(user_id)
    print(product)
    if not product:
        raise HTTPException(404, "no products")

    async def stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{AGENT_URL}/agent/query",
                json={"query": product, "user_id": user_id},
            ) as resp:
                
                async for chunk in resp.aiter_lines():     
                    line = chunk.strip()
                    if not line:
                        continue

                    try:
                        event = json5.loads(line)
                        safe_json = json.dumps(event, ensure_ascii=False)
                    
                    # Логика что при энд кандидат поступает
                    # if event["type"] == "end":
                        
                    except Exception as e:
                        print("JSON ERROR:", line, e)
                        continue
                    
                    yield safe_json + "\n"

    return StreamingResponse(stream(), media_type="application/x-jsonl")


@app.post("/agent/clarify")
async def agent_clarify(payload: dict):

    query = payload.get("query")
    user_id = payload.get("user_id")

    if not query:
        raise HTTPException(400, "query is required")

    async def stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{AGENT_URL}/agent/clarify",
                json={"query": query, "user_id": user_id},
            ) as resp:

                async for chunk in resp.aiter_lines():
                    line = chunk.strip()
                    if not line:
                        continue

                    try:
                        event = json5.loads(line)
                        safe_json = json.dumps(event, ensure_ascii=False)
                    except Exception as e:
                        print("JSON ERROR:", line, e)
                        continue

                    yield safe_json + "\n"

    return StreamingResponse(stream(), media_type="application/x-jsonl")


@app.post("/agent/next")
async def agent_next(req: RunAgentRequest):

    user_id = req.user_id
    product = storage.pop_product(user_id)
    print(product)
    if not product:
        raise HTTPException(404, "no products")

    # ✔ Перед следующим запросом сбрасываем агента
    async with httpx.AsyncClient() as client:
        await client.post(f"{AGENT_URL}/agent/startup")

    async def stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{AGENT_URL}/agent/query",
                json={"query": product, "user_id": user_id, "debug_print": True},
            ) as resp:
                
                async for chunk in resp.aiter_lines():     
                    line = chunk.strip()
                    if not line:
                        continue

                    try:
                        event = json5.loads(line)
                        safe_json = json.dumps(event, ensure_ascii=False)
                    
                    # Логика что при энд кандидат поступает
                    # if event["type"] == "end":
                        
                    except Exception as e:
                        print("JSON ERROR:", line, e)
                        continue
                    
                    yield safe_json + "\n"

    return StreamingResponse(stream(), media_type="application/x-jsonl")
