"""
SQLite database setup.

SQLite stores everything in a single file (trusttrace.db) so you do not
need to install or start a separate database server.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# File-based SQLite database in the backend folder
DATABASE_URL = "sqlite:///./trusttrace.db"

# check_same_thread=False is required so FastAPI can use SQLite
# from more than one request at a time.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal is a factory: call it to get a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def get_db():
    """
    FastAPI dependency.

    Opens a database session for one request, then always closes it.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
