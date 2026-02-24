from sqlmodel import create_engine, Session
from typing import Generator
from config import settings
import os


# Determine if we're using test database (for testing purposes)
TESTING = os.getenv("TESTING", "False").lower() == "true"

if TESTING:
    DATABASE_URL = "sqlite:///./test.db"
else:
    DATABASE_URL = settings.database_url


def _build_engine_kwargs(url: str) -> dict:
    """Build engine kwargs based on database type."""
    kwargs = {
        "echo": False,  # Set to True to see SQL queries for debugging
    }
    if "sqlite" in url:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # PostgreSQL (Neon) connection pooling configuration
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
        kwargs["pool_pre_ping"] = True  # Verify connections before use (Neon cold start resilience)
    return kwargs


# Create the database engine
engine = create_engine(DATABASE_URL, **_build_engine_kwargs(DATABASE_URL))


def get_session() -> Generator[Session, None, None]:
    """
    Dependency to get a database session
    """
    with Session(engine) as session:
        yield session
