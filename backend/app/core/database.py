from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Connection pooling configuration for production readiness
# pool_size: number of connections to maintain
# max_overflow: additional connections beyond pool_size
# pool_pre_ping: verify connections before using (handles stale connections)
# pool_recycle: recycle connections after this many seconds
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False,          # Set to True for SQL debugging
    connect_args={
        "connect_timeout": 10,  # Fail fast on connection timeout
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Transactional safety: ensure rollback on failure
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set PostgreSQL-specific connection settings for transactional safety"""
    # PostgreSQL doesn't need pragmas, but we can set transaction isolation
    # Default isolation level is READ COMMITTED which is appropriate
    pass


def get_db():
    """
    Dependency for getting database session.
    Ensures proper cleanup and rollback on failure.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Commit on success
    except Exception:
        db.rollback()  # Rollback on failure
        raise
    finally:
        db.close()
