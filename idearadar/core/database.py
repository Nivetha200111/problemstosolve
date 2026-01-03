"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from core.config import settings

# Create engine with connection pooling optimized for serverless
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 10,
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session (use with context manager)."""
    return SessionLocal()
