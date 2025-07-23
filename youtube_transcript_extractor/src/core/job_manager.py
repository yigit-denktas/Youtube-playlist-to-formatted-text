"""
Job persistence and resume functionality for YouTube Transcript Extractor.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging


class JobStatus(Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobItemStatus(Enum):
    """Individual job item status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class JobManager:
    """Manages processing jobs with persistence and resume capability."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize job manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        if db_path is None:
            db_path = Path.home() / ".yte_jobs.db"
        
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the job database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        source_url TEXT NOT NULL,
                        source_title TEXT,
                        progress_data TEXT,
                        result_path TEXT,
                        error_message TEXT,
                        total_items INTEGER DEFAULT 0,
                        completed_items INTEGER DEFAULT 0,
                        failed_items INTEGER DEFAULT 0,
                        config_data TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS job_items (
                        id TEXT PRIMARY KEY,
                        job_id TEXT NOT NULL,
                        item_index INTEGER NOT NULL,
                        video_url TEXT NOT NULL,
                        video_title TEXT,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processing_time REAL DEFAULT 0.0,
                        retry_count INTEGER DEFAULT 0,
                        error_message TEXT,
                        result_data TEXT,
                        FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_job_items_job_id ON job_items(job_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_job_items_status ON job_items(status)")
                
                conn.commit()
                self.logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_job(
        self, 
        source_type: str, 
        source_url: str, 
        source_title: Optional[str] = None,
        config_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new processing job.
        
        Args:
            source_type: Type of source (playlist, single_video, local_folder)
            source_url: URL or path to the source
            source_title: Optional title for the source
            config_data: Optional configuration data for the job
            
        Returns:
            Job ID string
        """
        job_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO jobs (
                        id, status, source_type, source_url, source_title, config_data
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    job_id,
                    JobStatus.PENDING.value,
                    source_type,
                    source_url,
                    source_title,
                    json.dumps(config_data) if config_data else None
                ))
                conn.commit()
                
            self.logger.info(f"Created job {job_id} for {source_type}: {source_url}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"Failed to create job: {e}")
            raise
    
    def add_job_items(self, job_id: str, video_urls: List[Dict[str, Any]]) -> bool:
        """Add video items to a job.
        
        Args:
            job_id: Job ID
            video_urls: List of video dictionaries with 'url' and optional 'title'
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Add job items
                for index, video_data in enumerate(video_urls):
                    item_id = str(uuid.uuid4())
                    conn.execute("""
                        INSERT INTO job_items (
                            id, job_id, item_index, video_url, video_title, status
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        item_id,
                        job_id,
                        index,
                        video_data.get('url', ''),
                        video_data.get('title', f'Video {index + 1}'),
                        JobItemStatus.PENDING.value
                    ))
                
                # Update job total items count
                conn.execute("""
                    UPDATE jobs 
                    SET total_items = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (len(video_urls), job_id))
                
                conn.commit()
                
            self.logger.info(f"Added {len(video_urls)} items to job {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add job items: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM jobs WHERE id = ?
                """, (job_id,))
                
                row = cursor.fetchone()
                if row:
                    job_data = dict(row)
                    # Parse JSON fields
                    if job_data['config_data']:
                        job_data['config_data'] = json.loads(job_data['config_data'])
                    if job_data['progress_data']:
                        job_data['progress_data'] = json.loads(job_data['progress_data'])
                    
                    return job_data
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    def get_job_items(self, job_id: str, status_filter: Optional[JobItemStatus] = None) -> List[Dict[str, Any]]:
        """Get job items for a specific job.
        
        Args:
            job_id: Job ID
            status_filter: Optional status to filter by
            
        Returns:
            List of job item dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if status_filter:
                    cursor = conn.execute("""
                        SELECT * FROM job_items 
                        WHERE job_id = ? AND status = ?
                        ORDER BY item_index
                    """, (job_id, status_filter.value))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM job_items 
                        WHERE job_id = ?
                        ORDER BY item_index
                    """, (job_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get job items for {job_id}: {e}")
            return []
    
    def update_job_status(self, job_id: str, status: JobStatus, error_message: Optional[str] = None) -> bool:
        """Update job status.
        
        Args:
            job_id: Job ID
            status: New job status
            error_message: Optional error message
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE jobs 
                    SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status.value, error_message, job_id))
                conn.commit()
                
            self.logger.info(f"Updated job {job_id} status to {status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update job status: {e}")
            return False
    
    def update_job_item_status(
        self, 
        item_id: str, 
        status: JobItemStatus,
        processing_time: float = 0.0,
        error_message: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update job item status.
        
        Args:
            item_id: Job item ID
            status: New status
            processing_time: Time taken to process
            error_message: Optional error message
            result_data: Optional result data
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE job_items 
                    SET status = ?, processing_time = ?, error_message = ?, 
                        result_data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    status.value,
                    processing_time,
                    error_message,
                    json.dumps(result_data) if result_data else None,
                    item_id
                ))
                
                # Update job progress counters
                job_id_query = conn.execute("SELECT job_id FROM job_items WHERE id = ?", (item_id,))
                job_id = job_id_query.fetchone()[0]
                
                # Count completed and failed items
                stats_query = conn.execute("""
                    SELECT 
                        COUNT(CASE WHEN status = ? THEN 1 END) as completed,
                        COUNT(CASE WHEN status = ? THEN 1 END) as failed
                    FROM job_items 
                    WHERE job_id = ?
                """, (JobItemStatus.COMPLETED.value, JobItemStatus.FAILED.value, job_id))
                
                completed, failed = stats_query.fetchone()
                
                conn.execute("""
                    UPDATE jobs 
                    SET completed_items = ?, failed_items = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (completed, failed, job_id))
                
                conn.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update job item status: {e}")
            return False
    
    def get_resumable_jobs(self) -> List[Dict[str, Any]]:
        """Get jobs that can be resumed.
        
        Returns:
            List of job dictionaries that can be resumed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM jobs 
                    WHERE status IN (?, ?, ?)
                    ORDER BY updated_at DESC
                """, (JobStatus.PROCESSING.value, JobStatus.PAUSED.value, JobStatus.FAILED.value))
                
                jobs = []
                for row in cursor.fetchall():
                    job_data = dict(row)
                    if job_data['config_data']:
                        job_data['config_data'] = json.loads(job_data['config_data'])
                    jobs.append(job_data)
                
                return jobs
                
        except Exception as e:
            self.logger.error(f"Failed to get resumable jobs: {e}")
            return []
    
    def resume_job(self, job_id: str) -> Dict[str, Any]:
        """Get data needed to resume a job.
        
        Args:
            job_id: Job ID to resume
            
        Returns:
            Dictionary with job and remaining items data
        """
        try:
            job_data = self.get_job(job_id)
            if not job_data:
                return {"error": "Job not found"}
            
            # Get pending items
            pending_items = self.get_job_items(job_id, JobItemStatus.PENDING)
            failed_items = self.get_job_items(job_id, JobItemStatus.FAILED)
            
            # Items that need processing
            remaining_items = pending_items + failed_items
            
            # Get progress statistics
            completed_items = self.get_job_items(job_id, JobItemStatus.COMPLETED)
            
            return {
                "job": job_data,
                "remaining_items": remaining_items,
                "completed_count": len(completed_items),
                "total_count": job_data['total_items'],
                "can_resume": len(remaining_items) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to resume job {job_id}: {e}")
            return {"error": str(e)}
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job and all its items.
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete job items first (due to foreign key)
                conn.execute("DELETE FROM job_items WHERE job_id = ?", (job_id,))
                
                # Delete job
                result = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                conn.commit()
                
                if result.rowcount > 0:
                    self.logger.info(f"Deleted job {job_id}")
                    return True
                else:
                    self.logger.warning(f"Job {job_id} not found for deletion")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to delete job {job_id}: {e}")
            return False
    
    def get_jobs_by_status(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get jobs filtered by status.
        
        Args:
            status: Filter jobs by status (None for all jobs)
            
        Returns:
            List of job dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if status:
                    cursor = conn.execute("""
                        SELECT * FROM jobs 
                        WHERE status = ?
                        ORDER BY updated_at DESC
                    """, (status,))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM jobs 
                        ORDER BY updated_at DESC
                    """)
                
                jobs = []
                for row in cursor.fetchall():
                    job_dict = dict(row)
                    if job_dict['metadata']:
                        job_dict['metadata'] = json.loads(job_dict['metadata'])
                    jobs.append(job_dict)
                
                return jobs
                
        except Exception as e:
            self.logger.error(f"Failed to get jobs by status: {e}")
            return []
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get overall job statistics.
        
        Returns:
            Dictionary with job statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Job status counts
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count
                    FROM jobs
                    GROUP BY status
                """)
                status_counts = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Overall statistics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_jobs,
                        SUM(total_items) as total_items,
                        SUM(completed_items) as total_completed,
                        SUM(failed_items) as total_failed
                    FROM jobs
                """)
                overall_stats = cursor.fetchone()
                
                return {
                    "status_counts": status_counts,
                    "total_jobs": overall_stats[0] or 0,
                    "total_items": overall_stats[1] or 0,
                    "total_completed": overall_stats[2] or 0,
                    "total_failed": overall_stats[3] or 0,
                    "database_path": str(self.db_path)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get job statistics: {e}")
            return {"error": str(e)}
    
    def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed jobs.
        
        Args:
            days_old: Number of days old to consider for cleanup
            
        Returns:
            Number of jobs cleaned up
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete completed jobs older than specified days
                cursor = conn.execute("""
                    DELETE FROM jobs 
                    WHERE status = ? 
                    AND datetime(updated_at) < datetime('now', '-{} days')
                """.format(days_old), (JobStatus.COMPLETED.value,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old jobs")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old jobs: {e}")
            return 0
