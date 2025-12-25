"""
In-memory job queue for managing background ingestion tasks.
"""

import uuid
import logging
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class JobState(str, Enum):
    """Job lifecycle states."""
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    """Represents an ingestion job."""
    job_id: str
    state: JobState = JobState.QUEUED
    pages_fetched: int = 0
    pages_indexed: int = 0
    errors: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    result: Optional[Dict] = None  # Final result/error


class JobQueue:
    """Simple in-memory job queue for tracking ingestion tasks."""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
    
    def create_job(self) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = Job(job_id=job_id)
        logger.info(f"Created job {job_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def set_running(self, job_id: str) -> bool:
        """Mark job as running."""
        job = self.get_job(job_id)
        if job:
            job.state = JobState.RUNNING
            job.updated_at = datetime.utcnow()
            logger.info(f"Job {job_id} now running")
            return True
        return False
    
    def update_progress(self, job_id: str, pages_fetched: int, pages_indexed: int) -> bool:
        """Update job progress."""
        job = self.get_job(job_id)
        if job:
            job.pages_fetched = pages_fetched
            job.pages_indexed = pages_indexed
            job.updated_at = datetime.utcnow()
            return True
        return False
    
    def add_error(self, job_id: str, error: str) -> bool:
        """Add error to job."""
        job = self.get_job(job_id)
        if job:
            job.errors.append(error)
            job.updated_at = datetime.utcnow()
            return True
        return False
    
    def set_done(self, job_id: str, result: Optional[Dict] = None) -> bool:
        """Mark job as done."""
        job = self.get_job(job_id)
        if job:
            job.state = JobState.DONE
            job.result = result or {}
            job.updated_at = datetime.utcnow()
            logger.info(f"Job {job_id} completed successfully")
            return True
        return False
    
    def set_failed(self, job_id: str, error: str) -> bool:
        """Mark job as failed."""
        job = self.get_job(job_id)
        if job:
            job.state = JobState.FAILED
            job.errors.append(error)
            job.result = {"error": error}
            job.updated_at = datetime.utcnow()
            logger.error(f"Job {job_id} failed: {error}")
            return True
        return False


# Global job queue instance
job_queue = JobQueue()
