"""
Test configuration and fixtures for YouTube Transcript Extractor tests.
"""

import pytest
from unittest.mock import Mock, patch
import os
import tempfile
from typing import Generator

from src.core.models import ProcessingConfig, ProcessingMode, RefinementStyle
from src.utils.config import ConfigManager


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_transcript_content() -> str:
    """Sample transcript content for testing."""
    return """Video URL: https://www.youtube.com/watch?v=example1
This is a sample transcript for the first video.
It contains multiple sentences and paragraphs.

Video URL: https://www.youtube.com/watch?v=example2
This is another sample transcript for the second video.
It also contains content that can be processed.
"""


@pytest.fixture
def sample_config() -> ProcessingConfig:
    """Sample processing configuration for testing."""
    return ProcessingConfig(
        mode=ProcessingMode.YOUTUBE_URL,
        source_path="https://www.youtube.com/playlist?list=example",
        output_language="English",
        refinement_style=RefinementStyle.BALANCED_DETAILED,
        chunk_size=3000,
        gemini_model="gemini-2.5-flash",
        api_key="test_api_key",
        transcript_output_file="test_transcript.txt",
        gemini_output_file="test_output.txt"
    )


@pytest.fixture
def mock_env_file(temp_dir: str) -> str:
    """Create a mock .env file for testing."""
    env_file = os.path.join(temp_dir, ".env")
    with open(env_file, 'w') as f:
        f.write("""
API_KEY=test_api_key_from_env
LANGUAGE=Spanish
REFINEMENT_STYLE=Summary
CHUNK_SIZE=5000
GEMINI_MODEL=gemini-1.5-pro
""")
    return env_file


@pytest.fixture
def config_manager_with_env(mock_env_file: str) -> ConfigManager:
    """ConfigManager instance with mock environment file."""
    return ConfigManager(mock_env_file)
