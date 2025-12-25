from pydantic import BaseModel
from typing import List, Optional

class Document(BaseModel):
    url: str
    title: str
    content: str
    chunk_id: Optional[int] = None

class IngestRequest(BaseModel):
    documents: List[Document]

class IngestResponse(BaseModel):
    message: str
    job_id: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[List[Document]] = None

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    source_documents: List[Document]