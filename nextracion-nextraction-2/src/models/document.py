from pydantic import BaseModel
from typing import Optional

class Document(BaseModel):
    url: str
    title: str
    chunk_id: Optional[str] = None
    content: str
    metadata: Optional[dict] = None