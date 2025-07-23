"""
Shared protocol definitions for the YouTube Transcript Extractor.

This module centralizes all protocol definitions to eliminate duplicates
and ensure consistent interfaces across the application.
"""

from typing import Protocol, Optional
from youtube_transcript_extractor.src.core.models import ProcessingProgress


class ProgressCallback(Protocol):
    """Protocol for progress callback functions using ProcessingProgress."""
    def __call__(self, progress: ProcessingProgress) -> None:
        """Handle progress updates.
        
        Args:
            progress: ProcessingProgress object containing current state
        """
        ...


class StatusCallback(Protocol):
    """Protocol for status callback functions."""
    def __call__(self, message: str) -> None:
        """Handle status updates.
        
        Args:
            message: Status message string
        """
        ...


class SimpleProgressCallback(Protocol):
    """Protocol for simple progress callback functions with counters."""
    def __call__(self, completed: int, total: int, current_task: Optional[str] = None) -> None:
        """Handle simple progress updates.
        
        Args:
            completed: Number of completed items
            total: Total number of items
            current_task: Optional description of current task
        """
        ...
