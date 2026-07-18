"""
Background job for running AI/ML batch processing.
Can be scheduled to run daily/weekly using cron or task scheduler.
Includes locking mechanism to prevent concurrent execution.
"""
import sys
import os
import uuid
import json
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import SessionLocal
from app.services.ai_persistence_service import run_ai_batch_processing
from app.models.job_run import JobRun, JobStatus
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def acquire_job_lock(db, lock_id: str) -> bool:
    """
    Try to acquire a lock for the job.
    Returns True if lock acquired, False if another job is running.
    """
    # Check if there's a running job
    running_job = db.query(JobRun).filter(
        JobRun.job_type == "ai_batch_processing",
        JobRun.status == JobStatus.RUNNING
    ).first()
    
    if running_job:
        # Check if it's stale (older than 2 hours - likely crashed)
        if (datetime.utcnow() - running_job.started_at).total_seconds() > 7200:
            logger.warning(f"Found stale job run {running_job.id}, marking as failed")
            running_job.status = JobStatus.FAILED
            running_job.completed_at = datetime.utcnow()
            db.commit()
        else:
            logger.info(f"Job already running (ID: {running_job.id}), skipping")
            return False
    
    # Create new job run with lock
    try:
        job_run = JobRun(
            job_type="ai_batch_processing",
            status=JobStatus.RUNNING,
            lock_id=lock_id
        )
        db.add(job_run)
        db.commit()
        db.refresh(job_run)
        logger.info(f"Acquired job lock (Job ID: {job_run.id}, Lock ID: {lock_id})")
        return True
    except IntegrityError:
        # Lock ID collision or concurrent attempt
        db.rollback()
        logger.warning("Failed to acquire lock (concurrent execution detected)")
        return False


def release_job_lock(db, job_run: JobRun, status: JobStatus, summary: dict = None):
    """Release the job lock and update job status"""
    job_run.status = status
    job_run.completed_at = datetime.utcnow()
    
    if summary:
        job_run.products_processed = summary.get('products_processed', 0)
        job_run.forecasts_created = summary.get('forecasts_created', 0)
        job_run.predictions_created = summary.get('predictions_created', 0)
        job_run.recommendations_created = summary.get('recommendations_created', 0)
        job_run.detections_created = summary.get('detections_created', 0)
        job_run.alerts_created = summary.get('alerts_created', 0)
        job_run.error_count = len(summary.get('errors', []))
        
        if summary.get('errors'):
            job_run.error_details = json.dumps(summary['errors'], default=str)
    
    job_run.lock_id = None  # Release lock
    db.commit()
    logger.info(f"Released job lock (Job ID: {job_run.id}, Status: {status.value})")


def run_ai_job():
    """
    Main entry point for AI batch job.
    Can be called from cron, scheduler, or manually.
    Includes locking to prevent concurrent execution.
    """
    lock_id = str(uuid.uuid4())
    logger.info(f"Starting AI batch processing job (Lock ID: {lock_id})")
    
    db = SessionLocal()
    job_run = None
    
    try:
        # Acquire lock
        if not acquire_job_lock(db, lock_id):
            logger.warning("Could not acquire job lock, another job may be running")
            return
        
        # Get the job run we just created
        job_run = db.query(JobRun).filter(JobRun.lock_id == lock_id).first()
        
        # Run batch processing
        summary = run_ai_batch_processing(db)
        
        # Log results
        logger.info(f"AI batch processing completed:")
        logger.info(f"  - Products processed: {summary['products_processed']}")
        logger.info(f"  - Forecasts created: {summary['forecasts_created']}")
        logger.info(f"  - Predictions created: {summary['predictions_created']}")
        logger.info(f"  - Recommendations created: {summary['recommendations_created']}")
        logger.info(f"  - Detections created: {summary['detections_created']}")
        logger.info(f"  - Alerts created: {summary['alerts_created']}")
        
        if summary['errors']:
            logger.warning(f"  - Errors: {len(summary['errors'])}")
            for error in summary['errors']:
                logger.warning(f"    Product {error['product_id']}: {error['error']}")
        
        # Release lock and mark as completed
        release_job_lock(db, job_run, JobStatus.COMPLETED, summary)
        
    except Exception as e:
        logger.error(f"Error running AI batch job: {e}", exc_info=True)
        if job_run:
            try:
                release_job_lock(db, job_run, JobStatus.FAILED)
            except Exception as release_error:
                logger.error(f"Error releasing lock: {release_error}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_ai_job()
