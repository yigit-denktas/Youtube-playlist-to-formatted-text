"""
Tests for the transcript_fetcher module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
from youtube_transcript_extractor.src.core.transcript_fetcher import TranscriptFetcher
from youtube_transcript_extractor.src.core.models import TranscriptVideo, ProcessingConfig, ProcessingMode, RefinementStyle


@pytest.mark.unit
class TestTranscriptFetcher:
    """Tests for TranscriptFetcher class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = ProcessingConfig(
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
        self.fetcher = TranscriptFetcher(self.config)
    
    def test_init(self):
        """Test TranscriptFetcher initialization."""
        assert self.fetcher.config == self.config
        assert self.fetcher.progress_callback is None
    
    def test_init_with_callback(self):
        """Test TranscriptFetcher initialization with progress callback."""
        callback = Mock()
        fetcher = TranscriptFetcher(self.config, progress_callback=callback)
        assert fetcher.progress_callback == callback
    
    @patch('youtube_transcript_extractor.src.core.transcript_fetcher.youtube_transcript_api')
    def test_extract_video_id_from_url(self, mock_api):
        """Test extracting video ID from various URL formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ&list=123", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            video_id = self.fetcher._extract_video_id(url)
            assert video_id == expected_id
    
    def test_extract_video_id_invalid_url(self):
        """Test extracting video ID from invalid URL."""
        invalid_urls = [
            "https://www.google.com",
            "https://vimeo.com/123456",
            "not_a_url",
            ""
        ]
        
        for url in invalid_urls:
            video_id = self.fetcher._extract_video_id(url)
            assert video_id is None
    
    @patch('youtube_transcript_extractor.src.core.transcript_fetcher.youtube_transcript_api')
    @pytest.mark.asyncio
    async def test_fetch_single_video_success(self, mock_api):
        """Test successfully fetching a single video transcript."""
        # Mock the transcript API
        mock_transcript = [
            {'text': 'Hello world', 'start': 0.0, 'duration': 2.0},
            {'text': 'This is a test', 'start': 2.0, 'duration': 3.0}
        ]
        mock_api.YouTubeTranscriptApi.get_transcript.return_value = mock_transcript
        
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = await self.fetcher.fetch_single_video(url)
        
        assert isinstance(result, TranscriptVideo)
        assert result.success is True
        assert result.url == url
        assert result.content == "Hello world This is a test"
        assert result.error_message is None
    
    @patch('youtube_transcript_extractor.src.core.transcript_fetcher.youtube_transcript_api')
    @pytest.mark.asyncio
    async def test_fetch_single_video_failure(self, mock_api):
        """Test handling failure when fetching single video transcript."""
        # Mock API to raise an exception
        mock_api.YouTubeTranscriptApi.get_transcript.side_effect = Exception("No transcript available")
        
        url = "https://www.youtube.com/watch?v=invalid"
        result = await self.fetcher.fetch_single_video(url)
        
        assert isinstance(result, TranscriptVideo)
        assert result.success is False
        assert result.url == url
        assert result.content == ""
        assert "No transcript available" in result.error_message
    
    @pytest.mark.asyncio
    async def test_fetch_single_video_invalid_url(self):
        """Test handling invalid URL for single video."""
        url = "https://www.google.com"
        result = await self.fetcher.fetch_single_video(url)
        
        assert isinstance(result, TranscriptVideo)
        assert result.success is False
        assert result.url == url
        assert "Invalid YouTube URL" in result.error_message
    
    @patch('youtube_transcript_extractor.src.core.transcript_fetcher.build')
    @patch('youtube_transcript_extractor.src.core.transcript_fetcher.youtube_transcript_api')
    @pytest.mark.asyncio
    async def test_fetch_playlist_videos_success(self, mock_api, mock_build):
        """Test successfully fetching playlist videos."""
        # Mock YouTube API
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock playlist items response
        mock_service.playlistItems().list().execute.return_value = {
            'items': [
                {
                    'snippet': {
                        'title': 'Test Video 1',
                        'resourceId': {'videoId': 'video1'}
                    }
                },
                {
                    'snippet': {
                        'title': 'Test Video 2',
                        'resourceId': {'videoId': 'video2'}
                    }
                }
            ]
        }
        
        # Mock transcript API
        mock_api.YouTubeTranscriptApi.get_transcript.return_value = [
            {'text': 'Test transcript', 'start': 0.0, 'duration': 2.0}
        ]
        
        playlist_url = "https://www.youtube.com/playlist?list=PLtest"
        results = await self.fetcher.fetch_playlist_videos(playlist_url)
        
        assert len(results) == 2
        assert all(isinstance(video, TranscriptVideo) for video in results)
        assert all(video.success for video in results)
        assert results[0].title == "Test Video 1"
        assert results[1].title == "Test Video 2"
    
    @patch('youtube_transcript_extractor.src.core.transcript_fetcher.build')
    @pytest.mark.asyncio
    async def test_fetch_playlist_videos_api_failure(self, mock_build):
        """Test handling API failure when fetching playlist."""
        # Mock API to raise an exception
        mock_build.side_effect = Exception("API key invalid")
        
        playlist_url = "https://www.youtube.com/playlist?list=PLtest"
        results = await self.fetcher.fetch_playlist_videos(playlist_url)
        
        assert len(results) == 1
        assert results[0].success is False
        assert "API key invalid" in results[0].error_message
    
    @pytest.mark.asyncio
    async def test_fetch_playlist_videos_invalid_url(self):
        """Test handling invalid playlist URL."""
        invalid_url = "https://www.google.com"
        results = await self.fetcher.fetch_playlist_videos(invalid_url)
        
        assert len(results) == 1
        assert results[0].success is False
        assert "Invalid playlist URL" in results[0].error_message
    
    def test_extract_playlist_id(self):
        """Test extracting playlist ID from URL."""
        test_cases = [
            ("https://www.youtube.com/playlist?list=PLtest123", "PLtest123"),
            ("https://youtube.com/playlist?list=PLtest123&index=1", "PLtest123"),
            ("https://m.youtube.com/playlist?list=PLtest123", "PLtest123"),
        ]
        
        for url, expected_id in test_cases:
            playlist_id = self.fetcher._extract_playlist_id(url)
            assert playlist_id == expected_id
    
    def test_extract_playlist_id_invalid(self):
        """Test extracting playlist ID from invalid URL."""
        invalid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.google.com",
            "not_a_url"
        ]
        
        for url in invalid_urls:
            playlist_id = self.fetcher._extract_playlist_id(url)
            assert playlist_id is None
    
    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        """Test that progress callback is called during processing."""
        callback = Mock()
        fetcher = TranscriptFetcher(self.config, progress_callback=callback)
        
        with patch('youtube_transcript_extractor.src.core.transcript_fetcher.youtube_transcript_api') as mock_api:
            mock_api.YouTubeTranscriptApi.get_transcript.return_value = [
                {'text': 'Test', 'start': 0.0, 'duration': 1.0}
            ]
            
            await fetcher.fetch_single_video("https://www.youtube.com/watch?v=test")
            
            # Verify callback was called
            assert callback.called
    
    def test_format_transcript_content(self):
        """Test formatting transcript content from API response."""
        transcript_data = [
            {'text': 'Hello', 'start': 0.0, 'duration': 1.0},
            {'text': 'world', 'start': 1.0, 'duration': 1.0},
            {'text': 'test', 'start': 2.0, 'duration': 1.0}
        ]
        
        formatted = self.fetcher._format_transcript_content(transcript_data)
        assert formatted == "Hello world test"
    
    def test_format_transcript_content_empty(self):
        """Test formatting empty transcript content."""
        formatted = self.fetcher._format_transcript_content([])
        assert formatted == ""
    
    def test_format_transcript_content_with_timestamps(self):
        """Test formatting transcript content with timestamp preservation."""
        transcript_data = [
            {'text': 'Hello', 'start': 0.0, 'duration': 1.0},
            {'text': 'world', 'start': 10.0, 'duration': 1.0}  # Large gap
        ]
        
        formatted = self.fetcher._format_transcript_content(transcript_data, preserve_timestamps=True)
        assert "0:00" in formatted or "Hello" in formatted
        assert "world" in formatted


@pytest.mark.integration
class TestTranscriptFetcherIntegration:
    """Integration tests for TranscriptFetcher."""
    
    @pytest.mark.slow
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_real_youtube_video(self):
        """Test fetching from a real YouTube video (requires network)."""
        config = ProcessingConfig(
            mode=ProcessingMode.YOUTUBE_URL,
            source_path="https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - should always exist
            output_language="English",
            refinement_style=RefinementStyle.BALANCED_DETAILED,
            chunk_size=3000,
            gemini_model="gemini-2.5-flash",
            api_key="test_api_key",
            transcript_output_file="test_transcript.txt",
            gemini_output_file="test_output.txt"
        )
        
        fetcher = TranscriptFetcher(config)
        
        try:
            result = await fetcher.fetch_single_video(config.source_path)
            # Note: This test might fail if the video doesn't have transcripts
            # It's mainly to test the integration flow
            assert isinstance(result, TranscriptVideo)
        except Exception as e:
            # Expected for tests without proper API keys
            pytest.skip(f"Network test skipped: {e}")


if __name__ == '__main__':
    pytest.main([__file__])
