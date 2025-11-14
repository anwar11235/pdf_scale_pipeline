"""Database connection and session management"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql://user:pass@localhost:5432/docdb"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from db import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

