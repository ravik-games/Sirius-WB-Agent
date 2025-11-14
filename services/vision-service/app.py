from fastapi import FastAPI
from models import LocateRequest, LocateResponse
from vlm_client import VLMClient

app = FastAPI(title="Vision service")
vlm = VLMClient()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/locate", response_model=LocateResponse)
async def locate(req: LocateRequest):
    
    bbox = await vlm.locate(req.image, req.action)
    return bbox
