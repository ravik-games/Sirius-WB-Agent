from fastapi import FastAPI
from .agent import run_agent, init_agent

app = FastAPI()

@app.post("/agent/startup")
async def startup():
    init_agent()
    return {"status": "ok"}

@app.post("/agent/query")
async def agent_query(payload: dict):
    query = payload.get("query")
    messages = payload.get("messages")
    result = run_agent(query=query, messages=messages)
    return {"result": result}

@app.get("/agent/health")
def health():
    return {"status": "ok"}
