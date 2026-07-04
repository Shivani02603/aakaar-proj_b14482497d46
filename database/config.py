"""Database configuration — single source of truth for engine/session/Base.

Modes:
  - TESTING=1  → SQLite file DB (hermetic: no server, no credentials needed)
  - otherwise  → DATABASE_URL (PostgreSQL in production)

Every model MUST import Base from here. init_db() creates all tables registered on THIS
Base — a second Base defined anywhere else means its tables silently never get created.
"""
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load .env from the project root so `cp .env.example .env` just works.
# Existing shell variables win (load_dotenv never overrides), so TESTING=1 in the
# environment still forces hermetic mode regardless of .env contents.
# Graceful if python-dotenv is absent: plain environment variables still work.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TESTING = os.getenv("TESTING") == "1"

if TESTING:
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set (or set TESTING=1).")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they register on Base before create_all.
    import database.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def check_db_health() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
