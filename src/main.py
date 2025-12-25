"""
NEXTRACION – Nextraction 2
Web-based Retrieval-Augmented Generation (RAG) microservice
"""

import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NEXTRACION – Nextraction 2",
    description="Web-based RAG pipeline for evidence-first insights",
    version="2.0",
    docs_url=None,  # Disable docs in production
    redoc_url=None
)

# Configure CORS - restrict to specific origins
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:8001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Disable credentials for security
    allow_methods=["GET", "POST"],  # Only allow necessary methods
    allow_headers=["Content-Type"],  # Only allow necessary headers
)

# Include routers
app.include_router(api_router)

# Mount static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/api")
def read_root():
    return {
        "message": "Welcome to NEXTRACION – Nextraction 2 API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port)
