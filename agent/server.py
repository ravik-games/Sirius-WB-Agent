from fastapi import FastAPI
from starlette.responses import StreamingResponse

from agent import run_agent, init_agent

app = FastAPI()

@app.post("/agent/startup")
def startup():
    init_agent()
    return {"status": "ok"}

@app.post("/agent/query")
def agent_query(payload: dict):
    query = payload.get("query")
    messages = payload.get("messages")
    result_generator = run_agent(query=query, messages=messages)
    return StreamingResponse(result_generator, media_type="application/x-jsonl")

@app.get("/agent/health")
def health():
    return {"status": "ok"}
