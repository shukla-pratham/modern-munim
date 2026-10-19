"""
Model for tracking AI batch job runs.
Prevents concurrent execution and provides observability.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class JobStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRun(Base):
    """Tracks AI batch job execution history"""
    __tablename__ = "job_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, nullable=False, default="ai_batch_processing", index=True)
    status = Column(
        SQLEnum(
            JobStatus,
            name="jobstatus",
            values_callable=lambda x: [e.value for e in x],
            create_type=False,
        ),
        default=JobStatus.RUNNING,
        nullable=False,
        index=True,
    )
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Summary statistics
    products_processed = Column(Integer, default=0)
    forecasts_created = Column(Integer, default=0)
    predictions_created = Column(Integer, default=0)
    recommendations_created = Column(Integer, default=0)
    detections_created = Column(Integer, default=0)
    alerts_created = Column(Integer, default=0)
    
    # Error tracking
    error_count = Column(Integer, default=0)
    error_details = Column(Text)  # JSON string of errors
    
    # Lock mechanism
    lock_id = Column(String, unique=True, nullable=True, index=True)  # For preventing concurrent runs
