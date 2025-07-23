#!/usr/bin/env python3
"""
YouTube Transcript Extractor - GUI Application Launcher

This script provides a simple entry point to launch the GUI application.
For CLI usage, run: python -m youtube_transcript_extractor
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add package to path if running from development
if os.path.exists('youtube_transcript_extractor'):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from youtube_transcript_extractor.src.ui.main_window import main
    from youtube_transcript_extractor.src.utils.config import ConfigManager
    from youtube_transcript_extractor.src.utils.secure_config import SecureConfigManager
    from youtube_transcript_extractor.src.core.job_manager import JobManager, JobStatus
    from youtube_transcript_extractor.src.core.exporters import ExportManager
    from youtube_transcript_extractor.src.core.models import RefinementStyle
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r youtube_transcript_extractor/requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    main()