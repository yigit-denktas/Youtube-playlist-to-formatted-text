"""
High-performance concurrent transcript fetcher with rate limiting and retry logic.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Protocol
from datetime import datetime
import time

# Use centralized dependency management
import sys
from pathlib import Path
current_dir = Path(__file__).parent.parent  # Go up to src directory
sys.path.insert(0, str(current_dir))

from utils.dependencies import safe_import, is_available

# Import optional dependencies using the centralized system
aiohttp, AIOHTTP_AVAILABLE = safe_import("aiohttp", "aiohttp")
retry, TENACITY_AVAILABLE = safe_import("tenacity.retry", "tenacity")
if TENACITY_AVAILABLE:
    stop_after_attempt, _ = safe_import("tenacity.stop_after_attempt", "tenacity")
    wait_exponential, _ = safe_import("tenacity.wait_exponential", "tenacity")

from .models import TranscriptVideo
from .transcript_fetcher import TranscriptFetcher
from .protocols import SimpleProgressCallback


@dataclass
class ProcessingTask:
    """Represents a single video processing task."""
    video_id: str
    video_url: str
    title: Optional[str] = None
    priority: int = 0  # Higher number = higher priority
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.video_id:
            # Extract video_id from URL if not provided
            if "watch?v=" in self.video_url:
                self.video_id = self.video_url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in self.video_url:
                self.video_id = self.video_url.split("youtu.be/")[1].split("?")[0]


@dataclass
class ConcurrentProcessingResult:
    """Result of processing a single task in concurrent processing."""
    task: ProcessingTask
    transcript_video: Optional[TranscriptVideo] = None
    success: bool = False
    error_message: Optional[str] = None
    processing_time: float = 0.0
    retry_count: int = 0


class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, rate_per_second: float = 10.0):
        """Initialize rate limiter.
        
        Args:
            rate_per_second: Maximum requests per second
        """
        self.rate = rate_per_second
        self.tokens = rate_per_second
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token (wait if necessary)."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class ConcurrentTranscriptFetcher:
    """High-performance concurrent transcript fetcher."""
    
    def __init__(
        self, 
        max_workers: int = 5, 
        rate_limit_per_second: float = 10.0,
        enable_retry: bool = True
    ):
        """Initialize concurrent fetcher.
        
        Args:
            max_workers: Maximum number of concurrent workers
            rate_limit_per_second: Rate limit for API calls
            enable_retry: Whether to enable automatic retries
        """
        self.max_workers = max_workers
        self.rate_limiter = RateLimiter(rate_limit_per_second)
        self.enable_retry = enable_retry
        self.logger = logging.getLogger(__name__)
        self._fetcher = TranscriptFetcher()
        self._session: Optional[Any] = None
        self._cancelled = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        if AIOHTTP_AVAILABLE:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    def cancel(self) -> None:
        """Cancel all processing."""
        self._cancelled = True
        self.logger.info("Concurrent processing cancelled")
    
    def _apply_retry_decorator(self, func):
        """Apply retry decorator if tenacity is available."""
        if TENACITY_AVAILABLE and self.enable_retry:
            from tenacity import retry, stop_after_attempt, wait_exponential
            return retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=4, max=10)
            )(func)
        return func
    
    async def _fetch_single_transcript_async(self, task: ProcessingTask) -> ConcurrentProcessingResult:
        """Fetch single transcript asynchronously with rate limiting.
        
        Args:
            task: Processing task to execute
            
        Returns:
            ConcurrentProcessingResult with the outcome
        """
        if self._cancelled:
            return ConcurrentProcessingResult(
                task=task,
                success=False,
                error_message="Processing was cancelled"
            )
        
        start_time = time.time()
        
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Run the transcript fetching in a thread pool
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = loop.run_in_executor(
                    executor,
                    self._fetch_transcript_sync,
                    task
                )
                
                transcript_video = await future
                
            processing_time = time.time() - start_time
            
            if transcript_video and transcript_video.success:
                self.logger.debug(f"Successfully fetched transcript for {task.video_id}")
                return ConcurrentProcessingResult(
                    task=task,
                    transcript_video=transcript_video,
                    success=True,
                    processing_time=processing_time,
                    retry_count=task.retry_count
                )
            else:
                error_msg = transcript_video.error_message if transcript_video else "Unknown error"
                self.logger.warning(f"Failed to fetch transcript for {task.video_id}: {error_msg}")
                return ConcurrentProcessingResult(
                    task=task,
                    transcript_video=transcript_video,
                    success=False,
                    error_message=error_msg,
                    processing_time=processing_time,
                    retry_count=task.retry_count
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Exception during processing: {str(e)}"
            self.logger.error(f"Error processing {task.video_id}: {error_msg}")
            
            return ConcurrentProcessingResult(
                task=task,
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                retry_count=task.retry_count
            )
    
    def _fetch_transcript_sync(self, task: ProcessingTask) -> Optional[TranscriptVideo]:
        """Synchronous transcript fetching (runs in thread pool).
        
        Args:
            task: Processing task
            
        Returns:
            TranscriptVideo or None
        """
        try:
            # Use the existing TranscriptFetcher's single video extraction method
            from youtube_transcript_api._api import YouTubeTranscriptApi
            
            ytt_api = YouTubeTranscriptApi()
            result = self._fetcher._extract_single_video_transcript(
                video_url=task.video_url,
                index=1,
                total=1,
                ytt_api=ytt_api,
                status_callback=None
            )
            
            return result
                
        except Exception as e:
            return TranscriptVideo(
                url=task.video_url,
                title=task.title,
                content="",
                success=False,
                error_message=str(e)
            )
    
    async def fetch_batch(
        self,
        tasks: List[ProcessingTask],
        progress_callback: Optional[SimpleProgressCallback] = None
    ) -> List[ConcurrentProcessingResult]:
        """Fetch multiple transcripts concurrently.
        
        Args:
            tasks: List of processing tasks
            progress_callback: Optional progress callback function
            
        Returns:
            List of processing results
        """
        if not tasks:
            return []
        
        self.logger.info(f"Starting batch processing of {len(tasks)} tasks with {self.max_workers} workers")
        
        # Sort tasks by priority (highest first)
        sorted_tasks = sorted(tasks, key=lambda x: x.priority, reverse=True)
        
        results: List[ConcurrentProcessingResult] = []
        completed_count = 0
        
        # Create semaphore to limit concurrent workers
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_with_semaphore(task: ProcessingTask) -> ConcurrentProcessingResult:
            """Process task with semaphore control."""
            async with semaphore:
                return await self._fetch_single_transcript_async(task)
        
        # Create all coroutines
        coroutines = [process_with_semaphore(task) for task in sorted_tasks]
        
        # Process tasks with progress tracking
        for future in asyncio.as_completed(coroutines):
            if self._cancelled:
                break
                
            try:
                result = await future
                results.append(result)
                completed_count += 1
                
                # Call progress callback
                if progress_callback:
                    current_task = f"{result.task.title or result.task.video_id}"
                    progress_callback(completed_count, len(tasks), current_task)
                
                # Log progress
                if completed_count % 5 == 0 or completed_count == len(tasks):
                    success_count = sum(1 for r in results if r.success)
                    self.logger.info(
                        f"Progress: {completed_count}/{len(tasks)} completed, "
                        f"{success_count} successful"
                    )
                    
            except Exception as e:
                self.logger.error(f"Error in batch processing: {e}")
                # Create a failed result for this task
                failed_result = ConcurrentProcessingResult(
                    task=sorted_tasks[len(results)],  # Approximate task
                    success=False,
                    error_message=str(e)
                )
                results.append(failed_result)
                completed_count += 1
        
        # Sort results back to original order if needed
        self.logger.info(f"Batch processing completed: {len(results)} results")
        return results
    
    def get_statistics(self, results: List[ConcurrentProcessingResult]) -> Dict[str, Any]:
        """Get processing statistics.
        
        Args:
            results: List of processing results
            
        Returns:
            Dictionary with statistics
        """
        if not results:
            return {}
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_time = sum(r.processing_time for r in results)
        avg_time = total_time / len(results) if results else 0
        
        return {
            "total_tasks": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "total_processing_time": total_time,
            "average_processing_time": avg_time,
            "max_processing_time": max(r.processing_time for r in results) if results else 0,
            "min_processing_time": min(r.processing_time for r in results) if results else 0,
            "error_summary": self._get_error_summary(failed)
        }
    
    def _get_error_summary(self, failed_results: List[ConcurrentProcessingResult]) -> Dict[str, int]:
        """Get summary of errors.
        
        Args:
            failed_results: List of failed results
            
        Returns:
            Dictionary with error counts
        """
        error_counts: Dict[str, int] = {}
        
        for result in failed_results:
            error_msg = result.error_message or "Unknown error"
            # Simplify error message for grouping
            if "No transcript" in error_msg:
                key = "No transcript available"
            elif "rate limit" in error_msg.lower():
                key = "Rate limited"
            elif "timeout" in error_msg.lower():
                key = "Timeout"
            elif "cancelled" in error_msg.lower():
                key = "Cancelled"
            else:
                key = "Other error"
            
            error_counts[key] = error_counts.get(key, 0) + 1
        
        return error_counts


class ConcurrentPlaylistProcessor:
    """Specialized processor for YouTube playlists with concurrent fetching."""
    
    def __init__(self, max_workers: int = 5, rate_limit: float = 10.0):
        """Initialize playlist processor.
        
        Args:
            max_workers: Maximum concurrent workers
            rate_limit: Rate limit per second
        """
        self.concurrent_fetcher = ConcurrentTranscriptFetcher(max_workers, rate_limit)
        self.logger = logging.getLogger(__name__)
    
    async def process_playlist(
        self,
        playlist_url: str,
        progress_callback: Optional[SimpleProgressCallback] = None
    ) -> List[ConcurrentProcessingResult]:
        """Process entire playlist concurrently.
        
        Args:
            playlist_url: YouTube playlist URL
            progress_callback: Progress callback function
            
        Returns:
            List of processing results
        """
        try:
            # First, get all videos in the playlist
            from pytube import Playlist  # type: ignore
            
            self.logger.info(f"Extracting video list from playlist: {playlist_url}")
            playlist = Playlist(playlist_url)
            
            # Create processing tasks
            tasks = []
            for i, video_url in enumerate(playlist.video_urls):
                # Simple video title
                video_title = f"Video {i+1}"
                
                task = ProcessingTask(
                    video_id="",  # Will be extracted from URL
                    video_url=video_url,
                    title=video_title,
                    priority=len(playlist.video_urls) - i  # Earlier videos have higher priority
                )
                tasks.append(task)
            
            self.logger.info(f"Created {len(tasks)} processing tasks")
            
            # Process all tasks concurrently
            async with self.concurrent_fetcher:
                results = await self.concurrent_fetcher.fetch_batch(tasks, progress_callback)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing playlist: {e}")
            return []
