from pydantic import BaseModel, Field
from typing import List, Optional


class IngestRequest(BaseModel):
    """Request body for POST /ingest"""
    seed_urls: List[str] = Field(..., description="Starting URLs for crawling")
    domain_allowlist: List[str] = Field(..., description="Allowed domains for crawling")
    max_pages: int = Field(default=20, ge=1, le=500, description="Maximum pages to crawl")
    max_depth: int = Field(default=2, ge=0, le=5, description="Maximum crawl depth")
    user_notes: Optional[str] = Field(None, description="Optional metadata/tags")


class IngestResponse(BaseModel):
    """Response for POST /ingest"""
    job_id: str = Field(..., description="Unique job identifier")
    accepted_pages: int = Field(..., description="Number of pages queued for processing")


class StatusResponse(BaseModel):
    """Response for GET /status/{job_id}"""
    state: str = Field(..., description="Job state: queued|running|done|failed")
    pages_fetched: int = Field(default=0, description="Number of pages fetched")
    pages_indexed: int = Field(default=0, description="Number of chunks indexed")
    errors: List[str] = Field(default_factory=list, description="Error messages if any")


class Citation(BaseModel):
    """Citation for a fact in the answer"""
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Page title")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    quote: str = Field(..., description="Short excerpt (~25 words)")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance/similarity score")


class AskRequest(BaseModel):
    """Request body for POST /ask"""
    job_id: str = Field(..., description="Job ID from /ingest")
    question: str = Field(..., description="Question to answer")


class AskResponse(BaseModel):
    """Response for POST /ask"""
    answer: str = Field(..., description="Grounded answer")
    citations: List[Citation] = Field(default_factory=list, description="Supporting citations")
    confidence: str = Field(..., description="Confidence level: high|medium|low")
    grounding_notes: str = Field(..., description="Explanation of grounding/confidence")


class HealthResponse(BaseModel):
    """Response for GET /health"""
    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="2.0", description="API version")
