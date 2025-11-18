from fastapi import FastAPI
from starlette.responses import StreamingResponse

from main_agent import run_new_search, clarify_search, init_agent

app = FastAPI()

@app.post("/agent/startup")
def startup():
    init_agent(show_browser=True)
    return {"status": "ok"}

@app.post("/agent/query")
def agent_query(payload: dict):
    query = payload.get("query")
    user_id = payload.get("user_id")
    result_generator = run_new_search(user_id=user_id, query=query)
    return StreamingResponse(result_generator, media_type="application/x-jsonl; charset=utf-8")

@app.post("/agent/clarify")
def agent_clarify(payload: dict):
    query = payload.get("query")
    user_id = payload.get("user_id")
    result_generator = clarify_search(user_id=user_id, query=query)
    return StreamingResponse(result_generator, media_type="application/x-jsonl; charset=utf-8")

@app.get("/agent/health")
def health():
    return {"status": "ok"}
