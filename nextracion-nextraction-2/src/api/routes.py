from fastapi import APIRouter, HTTPException
from src.api.schemas import IngestRequest, StatusResponse, AskRequest, HealthResponse
from src.services.rag_pipeline import ingest_data, get_status, ask_question, health_check

router = APIRouter()

@router.post("/ingest")
async def ingest(request: IngestRequest):
    try:
        job_id = await ingest_data(request)
        return {"job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str):
    status = await get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.post("/ask", response_model=str)
async def ask(request: AskRequest):
    try:
        answer = await ask_question(request.question)
        return answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def health():
    return await health_check()