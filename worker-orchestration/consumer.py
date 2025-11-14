"""Queue consumer for processing documents"""
import os
import logging
import redis
from rq import Queue, Worker
from db.connection import SessionLocal
from workers.orchestrator import process_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(redis_url)

# Create queue
q = Queue('document_processing', connection=redis_conn)


def process_document_task(doc_id: str):
    """Task wrapper for RQ"""
    db = SessionLocal()
    try:
        import uuid
        result = process_document(db, uuid.UUID(doc_id))
        return result
    finally:
        db.close()


if __name__ == "__main__":
    # Start worker
    worker = Worker([q], connection=redis_conn)
    worker.work()

