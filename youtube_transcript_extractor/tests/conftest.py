"""
Test configuration and fixtures for YouTube Transcript Extractor tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import os
import tempfile
import json
from typing import Generator, Dict, Any, List
from pathlib import Path

from youtube_transcript_extractor.src.core.models import (
    ProcessingConfig, ProcessingMode, RefinementStyle, TranscriptVideo, 
    ProcessingResult, ProcessingProgress
)
from youtube_transcript_extractor.src.utils.config import ConfigManager


# Test data and fixtures
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

This content has various formatting elements.
- Bullet points
- Multiple paragraphs
- Technical terms and explanations

Video URL: https://www.youtube.com/watch?v=example2
This is another sample transcript for the second video.
It also contains content that can be processed.

> Important quote or blockquote
> Multiple line quote

Some **bold text** and *italic text* formatting.
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
def sample_videos() -> List[TranscriptVideo]:
    """Sample transcript videos for testing."""
    return [
        TranscriptVideo(
            url="https://www.youtube.com/watch?v=example1",
            title="Test Video 1",
            content="This is the transcript content for video 1.",
            success=True
        ),
        TranscriptVideo(
            url="https://www.youtube.com/watch?v=example2", 
            title="Test Video 2",
            content="This is the transcript content for video 2.",
            success=True
        ),
        TranscriptVideo(
            url="https://www.youtube.com/watch?v=failed",
            title=None,
            content="",
            success=False,
            error_message="No transcript available"
        )
    ]


@pytest.fixture
def mock_env_file(temp_dir: str) -> str:
    """Create a mock .env file for testing."""
    env_file = os.path.join(temp_dir, ".env")
    with open(env_file, 'w') as f:
        f.write("""API_KEY=test_api_key_from_env
LANGUAGE=Spanish
REFINEMENT_STYLE=Summary
CHUNK_SIZE=5000
GEMINI_MODEL=gemini-1.5-pro
TRANSCRIPT_OUTPUT_FILE=custom_transcript.txt
GEMINI_OUTPUT_FILE=custom_output.txt
""")
    return env_file


@pytest.fixture
def config_manager_with_env(mock_env_file: str) -> ConfigManager:
    """ConfigManager instance with mock environment file."""
    return ConfigManager(mock_env_file)


# Mock fixtures for external dependencies
@pytest.fixture
def mock_youtube_api_response():
    """Mock YouTube API response data."""
    return {
        'items': [
            {
                'snippet': {
                    'title': 'Test Video 1',
                    'resourceId': {'videoId': 'example1'}
                }
            },
            {
                'snippet': {
                    'title': 'Test Video 2', 
                    'resourceId': {'videoId': 'example2'}
                }
            }
        ]
    }


@pytest.fixture
def mock_transcript_response():
    """Mock transcript API response."""
    return [
        {
            'text': 'This is the transcript content.',
            'start': 0.0,
            'duration': 5.0
        },
        {
            'text': 'More transcript content here.',
            'start': 5.0,
            'duration': 4.0
        }
    ]


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    return {
        'candidates': [{
            'content': {
                'parts': [{
                    'text': 'This is the refined transcript content with proper formatting and structure.'
                }]
            }
        }]
    }


@pytest.fixture
def mock_processing_progress():
    """Mock processing progress for testing."""
    return ProcessingProgress(
        current_item=2,
        total_items=10,
        current_operation="Processing video transcripts",
        percentage=20,
        message="Processing video 2 of 10"
    )


@pytest.fixture
def mock_processing_result():
    """Mock processing result for testing."""
    return ProcessingResult(
        success=True,
        output_file="test_output.txt",
        videos_processed=5,
        total_videos=5
    )


# Async testing utilities
@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Mock classes for complex objects
@pytest.fixture
def mock_transcript_fetcher():
    """Mock TranscriptFetcher for testing."""
    mock = MagicMock()
    mock.fetch_playlist_videos = AsyncMock(return_value=[
        TranscriptVideo(
            url="https://www.youtube.com/watch?v=example1",
            title="Test Video 1", 
            content="Sample transcript content 1",
            success=True
        )
    ])
    mock.fetch_single_video = AsyncMock(return_value=TranscriptVideo(
        url="https://www.youtube.com/watch?v=example1",
        title="Test Video 1",
        content="Sample transcript content",
        success=True
    ))
    return mock


@pytest.fixture  
def mock_gemini_processor():
    """Mock GeminiProcessor for testing."""
    mock = MagicMock()
    mock.process_transcript = AsyncMock(return_value="Refined transcript content")
    mock.process_transcript_chunks = AsyncMock(return_value="Refined transcript content")
    return mock


@pytest.fixture
def mock_export_manager():
    """Mock ExportManager for testing."""
    mock = MagicMock()
    mock.get_available_formats.return_value = ['markdown', 'html', 'pdf', 'docx']
    mock.export_content.return_value = True
    mock.export_to_multiple_formats.return_value = {
        'markdown': True,
        'html': True,
        'pdf': True
    }
    return mock


# File system mocking utilities
@pytest.fixture
def mock_file_operations(temp_dir):
    """Mock file operations with temporary directory."""
    test_files = {}
    
    def mock_write_file(path: str, content: str):
        """Mock file writing."""
        test_files[path] = content
        # Also create actual file for some tests
        full_path = Path(temp_dir) / Path(path).name
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def mock_read_file(path: str) -> str:
        """Mock file reading."""
        if path in test_files:
            return test_files[path]
        # Try to read from temp directory
        full_path = Path(temp_dir) / Path(path).name
        if full_path.exists():
            return full_path.read_text(encoding='utf-8')
        raise FileNotFoundError(f"File not found: {path}")
    
    return {
        'write_file': mock_write_file,
        'read_file': mock_read_file,
        'files': test_files,
        'temp_dir': temp_dir
    }


# Network mocking
@pytest.fixture
def mock_network_responses():
    """Mock network responses for testing."""
    def mock_get(url: str, **kwargs):
        """Mock GET request."""
        if 'youtube.com' in url:
            return Mock(
                status_code=200,
                json=lambda: {'items': []},
                text='<html>YouTube page</html>'
            )
        elif 'googleapis.com' in url:
            return Mock(
                status_code=200,
                json=lambda: {'candidates': [{'content': {'parts': [{'text': 'response'}]}}]}
            )
        return Mock(status_code=404)
    
    def mock_post(url: str, **kwargs):
        """Mock POST request."""
        return Mock(
            status_code=200,
            json=lambda: {'success': True}
        )
    
    return {
        'get': mock_get,
        'post': mock_post
    }


# Test markers and utilities
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "network: Tests requiring network")
    config.addinivalue_line("markers", "gui: Tests requiring GUI")
    config.addinivalue_line("markers", "async: Async tests")


# Utility functions for tests
def create_test_file(directory: str, filename: str, content: str) -> str:
    """Create a test file with given content."""
    file_path = os.path.join(directory, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def assert_file_exists(file_path: str) -> bool:
    """Assert that a file exists."""
    return os.path.exists(file_path)


def assert_file_content(file_path: str, expected_content: str) -> bool:
    """Assert file content matches expected."""
    if not os.path.exists(file_path):
        return False
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read() == expected_content
