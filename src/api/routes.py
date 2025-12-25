import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.api.schemas import IngestRequest, IngestResponse, StatusResponse, AskRequest, AskResponse, HealthResponse
from src.services.rag_pipeline import RAGPipeline
from src.services.job_queue import job_queue, JobState

logger = logging.getLogger(__name__)

router = APIRouter()
rag_pipeline = RAGPipeline()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest, background_tasks: BackgroundTasks):
    try:
        # Validate inputs
        if not request.seed_urls:
            raise HTTPException(status_code=400, detail="seed_urls cannot be empty")
        if not request.domain_allowlist:
            raise HTTPException(status_code=400, detail="domain_allowlist cannot be empty")
        
        # Create job
        job_id = job_queue.create_job()
        logger.info(f"Created ingest job {job_id}")
        
        # Queue background task
        background_tasks.add_task(
            rag_pipeline.ingest,
            job_id,
            request.seed_urls,
            request.domain_allowlist,
            request.max_pages,
            request.max_depth
        )
        
        return IngestResponse(job_id=job_id, accepted_pages=len(request.seed_urls))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str):
    try:
        job = job_queue.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return StatusResponse(
            state=job.state.value,
            pages_fetched=job.pages_fetched,
            pages_indexed=job.pages_indexed,
            errors=job.errors[:10]  # Return last 10 errors
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    try:
        if not request.question or len(request.question.strip()) < 3:
            raise HTTPException(status_code=400, detail="Question too short")
        
        # Check job exists and is done
        job = job_queue.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")
        
        if job.state != JobState.DONE:
            raise HTTPException(
                status_code=400,
                detail=f"Job state is {job.state.value}, must be 'done'"
            )
        
        # Generate answer
        result = rag_pipeline.answer(request.job_id, request.question)
        
        return AskResponse(
            answer=result["answer"],
            citations=result["citations"],
            confidence=result["confidence"],
            grounding_notes=result["grounding_notes"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", version="2.0")
