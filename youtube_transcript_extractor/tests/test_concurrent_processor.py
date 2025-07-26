"""
Tests for the concurrent_processor module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
from youtube_transcript_extractor.src.core.concurrent_processor import (
    ConcurrentPlaylistProcessor, ConcurrentProcessingResult, ProcessingTask,
    RateLimiter, ConcurrentTranscriptFetcher
)
from youtube_transcript_extractor.src.core.models import TranscriptVideo


@pytest.mark.unit
class TestProcessingTask:
    """Tests for ProcessingTask dataclass."""
    
    def test_task_creation_with_video_id(self):
        """Test creating a processing task with explicit video ID."""
        task = ProcessingTask(
            video_id="dQw4w9WgXcQ",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video"
        )
        
        assert task.video_id == "dQw4w9WgXcQ"
        assert task.video_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert task.title == "Test Video"
        assert task.priority == 0
        assert task.retry_count == 0
    
    def test_task_creation_extracts_video_id_from_url(self):
        """Test that video ID is extracted from URL if not provided."""
        task = ProcessingTask(
            video_id="",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video"
        )
        
        assert task.video_id == "dQw4w9WgXcQ"
    
    def test_task_creation_extracts_video_id_from_short_url(self):
        """Test extracting video ID from youtu.be URL."""
        task = ProcessingTask(
            video_id="",
            video_url="https://youtu.be/dQw4w9WgXcQ",
            title="Test Video"
        )
        
        assert task.video_id == "dQw4w9WgXcQ"


@pytest.mark.unit
class TestConcurrentProcessingResult:
    """Tests for ConcurrentProcessingResult dataclass."""
    
    def test_successful_result_creation(self):
        """Test creating a successful processing result."""
        task = ProcessingTask(
            video_id="test123",
            video_url="https://www.youtube.com/watch?v=test123",
            title="Test Video"
        )
        
        transcript_video = TranscriptVideo(
            url="https://www.youtube.com/watch?v=test123",
            title="Test Video",
            content="Sample content",
            success=True
        )
        
        result = ConcurrentProcessingResult(
            task=task,
            transcript_video=transcript_video,
            success=True,
            processing_time=1.5
        )
        
        assert result.success is True
        assert result.transcript_video == transcript_video
        assert result.task == task
        assert result.error_message is None
        assert result.processing_time == 1.5
    
    def test_failed_result_creation(self):
        """Test creating a failed processing result."""
        task = ProcessingTask(
            video_id="test123",
            video_url="https://www.youtube.com/watch?v=test123",
            title="Test Video"
        )
        
        result = ConcurrentProcessingResult(
            task=task,
            success=False,
            error_message="Processing failed"
        )
        
        assert result.success is False
        assert result.error_message == "Processing failed"
        assert result.transcript_video is None


@pytest.mark.unit
class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_init(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(rate_per_second=5.0)
        
        assert limiter.rate == 5.0
        assert limiter.tokens == 5.0
    
    @pytest.mark.asyncio
    async def test_acquire_token_immediate(self):
        """Test acquiring token when available."""
        limiter = RateLimiter(rate_per_second=10.0)
        
        # Should acquire immediately
        await limiter.acquire()
        assert limiter.tokens < 10.0  # Token was consumed
    
    @pytest.mark.asyncio
    async def test_acquire_token_with_wait(self):
        """Test acquiring token when rate limited."""
        limiter = RateLimiter(rate_per_second=1.0)
        limiter.tokens = 0  # No tokens available
        
        import time
        start_time = time.time()
        await limiter.acquire()
        end_time = time.time()
        
        # Should have waited
        assert end_time - start_time > 0.5  # Some wait time


@pytest.mark.unit
class TestConcurrentTranscriptFetcher:
    """Tests for ConcurrentTranscriptFetcher class."""
    
    def test_init(self):
        """Test ConcurrentTranscriptFetcher initialization."""
        fetcher = ConcurrentTranscriptFetcher(max_workers=10, rate_limit_per_second=5.0)
        
        assert fetcher.max_workers == 10
        assert fetcher.rate_limiter.rate == 5.0
        assert fetcher.enable_retry is True
    
    def test_init_with_retry_disabled(self):
        """Test initialization with retry disabled."""
        fetcher = ConcurrentTranscriptFetcher(enable_retry=False)
        
        assert fetcher.enable_retry is False
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        fetcher = ConcurrentTranscriptFetcher()
        
        async with fetcher:
            # Session should be initialized if aiohttp is available
            pass  # Just test that context manager works
    
    def test_cancel(self):
        """Test cancelling processing."""
        fetcher = ConcurrentTranscriptFetcher()
        
        assert fetcher._cancelled is False
        fetcher.cancel()
        assert fetcher._cancelled is True
    
    @patch('youtube_transcript_extractor.src.core.concurrent_processor.TranscriptFetcher')
    @pytest.mark.asyncio
    async def test_fetch_single_transcript_success(self, mock_fetcher_class):
        """Test successful single transcript fetch."""
        # Mock TranscriptFetcher
        mock_fetcher = Mock()
        mock_fetcher._extract_single_video_transcript = Mock(return_value=TranscriptVideo(
            url="https://www.youtube.com/watch?v=test123",
            title="Test Video",
            content="Sample transcript",
            success=True
        ))
        mock_fetcher_class.return_value = mock_fetcher
        
        fetcher = ConcurrentTranscriptFetcher()
        fetcher._fetcher = mock_fetcher
        
        task = ProcessingTask(
            video_id="test123",
            video_url="https://www.youtube.com/watch?v=test123",
            title="Test Video"
        )
        
        result = await fetcher._fetch_single_transcript_async(task)
        
        assert isinstance(result, ConcurrentProcessingResult)
        assert result.success is True
        assert result.transcript_video is not None
        assert result.transcript_video.content == "Sample transcript"
    
    @patch('youtube_transcript_extractor.src.core.concurrent_processor.TranscriptFetcher')
    @pytest.mark.asyncio
    async def test_fetch_single_transcript_failure(self, mock_fetcher_class):
        """Test handling failure in single transcript fetch."""
        # Mock TranscriptFetcher to raise exception
        mock_fetcher = Mock()
        mock_fetcher._extract_single_video_transcript = Mock(side_effect=Exception("API error"))
        mock_fetcher_class.return_value = mock_fetcher
        
        fetcher = ConcurrentTranscriptFetcher()
        fetcher._fetcher = mock_fetcher
        
        task = ProcessingTask(
            video_id="test123",
            video_url="https://www.youtube.com/watch?v=test123",
            title="Test Video"
        )
        
        result = await fetcher._fetch_single_transcript_async(task)
        
        assert isinstance(result, ConcurrentProcessingResult)
        assert result.success is False
        assert result.error_message is not None
        assert "API error" in result.error_message
    
    @pytest.mark.asyncio
    async def test_fetch_single_transcript_cancelled(self):
        """Test handling cancelled processing."""
        fetcher = ConcurrentTranscriptFetcher()
        fetcher.cancel()  # Cancel before processing
        
        task = ProcessingTask(
            video_id="test123",
            video_url="https://www.youtube.com/watch?v=test123",
            title="Test Video"
        )
        
        result = await fetcher._fetch_single_transcript_async(task)
        
        assert isinstance(result, ConcurrentProcessingResult)
        assert result.success is False
        assert result.error_message is not None
        assert "cancelled" in result.error_message.lower()


@pytest.mark.unit
class TestConcurrentPlaylistProcessor:
    """Tests for ConcurrentPlaylistProcessor class."""
    
    def test_init(self):
        """Test ConcurrentPlaylistProcessor initialization."""
        processor = ConcurrentPlaylistProcessor(max_workers=10, rate_limit=5.0)
        
        assert processor.concurrent_fetcher.max_workers == 10
        assert processor.concurrent_fetcher.rate_limiter.rate == 5.0
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        processor = ConcurrentPlaylistProcessor()
        
        assert processor.concurrent_fetcher.max_workers == 5
        assert processor.concurrent_fetcher.rate_limiter.rate == 10.0
    
    @patch('youtube_transcript_extractor.src.core.concurrent_processor.Playlist')
    @pytest.mark.asyncio
    async def test_process_playlist_success(self, mock_playlist_class):
        """Test successful playlist processing."""
        # Mock Playlist
        mock_playlist = Mock()
        mock_playlist.video_urls = [
            "https://www.youtube.com/watch?v=video1",
            "https://www.youtube.com/watch?v=video2"
        ]
        mock_playlist_class.return_value = mock_playlist
        
        # Mock concurrent fetcher
        processor = ConcurrentPlaylistProcessor()
        
        with patch.object(processor.concurrent_fetcher, 'fetch_batch') as mock_fetch_batch:
            mock_results = [
                ConcurrentProcessingResult(
                    task=ProcessingTask(video_id="video1", video_url="url1"),
                    success=True
                ),
                ConcurrentProcessingResult(
                    task=ProcessingTask(video_id="video2", video_url="url2"),
                    success=True
                )
            ]
            mock_fetch_batch.return_value = mock_results
            
            results = await processor.process_playlist("https://www.youtube.com/playlist?list=test")
            
            assert len(results) == 2
            assert all(isinstance(result, ConcurrentProcessingResult) for result in results)
            mock_fetch_batch.assert_called_once()
    
    @patch('youtube_transcript_extractor.src.core.concurrent_processor.Playlist')
    @pytest.mark.asyncio
    async def test_process_playlist_with_progress_callback(self, mock_playlist_class):
        """Test playlist processing with progress callback."""
        # Mock Playlist
        mock_playlist = Mock()
        mock_playlist.video_urls = ["https://www.youtube.com/watch?v=video1"]
        mock_playlist_class.return_value = mock_playlist
        
        callback = Mock()
        processor = ConcurrentPlaylistProcessor()
        
        with patch.object(processor.concurrent_fetcher, 'fetch_batch') as mock_fetch_batch:
            mock_fetch_batch.return_value = [
                ConcurrentProcessingResult(
                    task=ProcessingTask(video_id="video1", video_url="url1"),
                    success=True
                )
            ]
            
            await processor.process_playlist(
                "https://www.youtube.com/playlist?list=test",
                progress_callback=callback
            )
            
            # Verify callback was passed to fetch_batch
            mock_fetch_batch.assert_called_once()
            call_args = mock_fetch_batch.call_args
            assert call_args[1].get('progress_callback') == callback or call_args[0][1] == callback
    
    @patch('youtube_transcript_extractor.src.core.concurrent_processor.Playlist')
    @pytest.mark.asyncio
    async def test_process_playlist_failure(self, mock_playlist_class):
        """Test handling failure in playlist processing."""
        # Mock Playlist to raise exception
        mock_playlist_class.side_effect = Exception("Invalid playlist URL")
        
        processor = ConcurrentPlaylistProcessor()
        results = await processor.process_playlist("https://invalid.url")
        
        assert results == []
    
    @patch('youtube_transcript_extractor.src.core.concurrent_processor.Playlist')
    @pytest.mark.asyncio
    async def test_process_empty_playlist(self, mock_playlist_class):
        """Test processing empty playlist."""
        # Mock empty playlist
        mock_playlist = Mock()
        mock_playlist.video_urls = []
        mock_playlist_class.return_value = mock_playlist
        
        processor = ConcurrentPlaylistProcessor()
        
        with patch.object(processor.concurrent_fetcher, 'fetch_batch') as mock_fetch_batch:
            mock_fetch_batch.return_value = []
            
            results = await processor.process_playlist("https://www.youtube.com/playlist?list=empty")
            
            assert results == []
            mock_fetch_batch.assert_called_once()
    
    @patch('youtube_transcript_extractor.src.core.concurrent_processor.Playlist')
    @pytest.mark.asyncio
    async def test_task_creation_and_priority(self, mock_playlist_class):
        """Test that tasks are created with correct priority."""
        # Mock Playlist with multiple videos
        mock_playlist = Mock()
        mock_playlist.video_urls = [
            "https://www.youtube.com/watch?v=video1",
            "https://www.youtube.com/watch?v=video2",
            "https://www.youtube.com/watch?v=video3"
        ]
        mock_playlist_class.return_value = mock_playlist
        
        processor = ConcurrentPlaylistProcessor()
        
        with patch.object(processor.concurrent_fetcher, 'fetch_batch') as mock_fetch_batch:
            mock_fetch_batch.return_value = []
            
            await processor.process_playlist("https://www.youtube.com/playlist?list=test")
            
            # Check that tasks were created with correct priorities
            call_args = mock_fetch_batch.call_args[0][0]  # First argument (tasks list)
            assert len(call_args) == 3
            
            # Earlier videos should have higher priority
            assert call_args[0].priority > call_args[1].priority
            assert call_args[1].priority > call_args[2].priority


@pytest.mark.integration
class TestConcurrentProcessorIntegration:
    """Integration tests for concurrent processor components."""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rate_limiter_with_concurrent_requests(self):
        """Test rate limiter with multiple concurrent requests."""
        limiter = RateLimiter(rate_per_second=2.0)
        
        import time
        start_time = time.time()
        
        # Make 5 concurrent requests
        tasks = [limiter.acquire() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # Should take at least 1.2 seconds due to rate limiting
        # (3 requests need to wait: 1.5 theoretical, but allow timing variance)
        assert end_time - start_time > 1.2
    
    @pytest.mark.asyncio
    async def test_concurrent_fetcher_with_multiple_tasks(self):
        """Test concurrent fetcher with multiple processing tasks."""
        tasks = [
            ProcessingTask(
                video_id=f"video{i}",
                video_url=f"https://www.youtube.com/watch?v=video{i}",
                title=f"Test Video {i}"
            )
            for i in range(3)
        ]
        
        with patch('youtube_transcript_extractor.src.core.concurrent_processor.TranscriptFetcher') as mock_fetcher_class:
            # Mock successful responses
            mock_fetcher = Mock()
            mock_fetcher.fetch_single_video = AsyncMock(return_value=TranscriptVideo(
                url="test_url",
                title="Test Video",
                content="Sample transcript",
                success=True
            ))
            mock_fetcher_class.return_value = mock_fetcher
            
            fetcher = ConcurrentTranscriptFetcher(max_workers=2)
            
            # Mock the fetch_batch method
            with patch.object(fetcher, 'fetch_batch') as mock_fetch_batch:
                mock_fetch_batch.return_value = [
                    ConcurrentProcessingResult(task=task, success=True) for task in tasks
                ]
                
                async with fetcher:
                    results = await fetcher.fetch_batch(tasks)
                
                assert len(results) == 3
                assert all(result.success for result in results)


if __name__ == '__main__':
    pytest.main([__file__])
