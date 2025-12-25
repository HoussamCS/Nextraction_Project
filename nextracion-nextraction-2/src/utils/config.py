from pydantic import BaseSettings

class Settings(BaseSettings):
    api_key: str
    api_base_url: str
    allowed_domains: list
    max_crawl_depth: int

    class Config:
        env_file = ".env"

settings = Settings()