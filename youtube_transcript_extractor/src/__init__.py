"""
YouTube Transcript Extractor - Main package.
"""

__version__ = "2.0.0"
__author__ = "YouTube Transcript Extractor Team"
__description__ = "A modular application for extracting and refining YouTube transcripts using AI"

from .core import (
    ProcessingConfig, ProcessingMode, RefinementStyle, GeminiModels,
    TranscriptFetcher, GeminiProcessor
)
from .ui import MainWindow
from .utils import ConfigManager, InputValidator

__all__ = [
    'ProcessingConfig', 'ProcessingMode', 'RefinementStyle', 'GeminiModels',
    'TranscriptFetcher', 'GeminiProcessor', 'MainWindow', 'ConfigManager', 'InputValidator'
]
