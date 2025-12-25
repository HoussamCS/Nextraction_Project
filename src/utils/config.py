from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "test-key")
    openai_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4-turbo"
    chroma_db_path: str = "./data/chroma_db"
    default_max_pages: int = 20
    default_max_depth: int = 2
    top_k_chunks: int = 5
    min_similarity_score: float = 0.3
    job_timeout: int = 300
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:8001"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

try:
    settings = Settings()
except Exception as e:
    settings = Settings(openai_api_key="test-key")