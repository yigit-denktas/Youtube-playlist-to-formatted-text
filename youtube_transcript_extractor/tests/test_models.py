"""
Tests for the models module.
"""

import pytest
from youtube_transcript_extractor.src.core.models import (
    ProcessingConfig, ProcessingMode, RefinementStyle, 
    ProcessingPrompts, GeminiModels, TranscriptVideo, ProcessingResult
)


class TestProcessingConfig:
    """Tests for ProcessingConfig dataclass."""
    
    def test_config_creation(self):
        """Test creating a processing configuration."""
        config = ProcessingConfig(
            mode=ProcessingMode.YOUTUBE_URL,
            source_path="https://example.com",
            output_language="English",
            refinement_style=RefinementStyle.SUMMARY,
            chunk_size=3000,
            gemini_model="gemini-2.5-flash",
            api_key="test_key",
            transcript_output_file="transcript.txt",
            gemini_output_file="output.txt"
        )
        
        assert config.mode == ProcessingMode.YOUTUBE_URL
        assert config.source_path == "https://example.com"
        assert config.output_language == "English"
        assert config.refinement_style == RefinementStyle.SUMMARY
        assert config.chunk_size == 3000


class TestRefinementStyle:
    """Tests for RefinementStyle enum."""
    
    def test_all_styles_exist(self):
        """Test that all expected refinement styles exist."""
        expected_styles = [
            "Balanced and Detailed",
            "Summary", 
            "Educational",
            "Narrative Rewriting",
            "Q&A Generation"
        ]
        
        actual_styles = [style.value for style in RefinementStyle]
        
        for expected in expected_styles:
            assert expected in actual_styles


class TestProcessingPrompts:
    """Tests for ProcessingPrompts class."""
    
    def test_get_prompt(self):
        """Test getting prompts for different styles."""
        prompt = ProcessingPrompts.get_prompt(RefinementStyle.SUMMARY)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "summarize" in prompt.lower()
    
    def test_get_default_chunk_size(self):
        """Test getting default chunk sizes."""
        chunk_size = ProcessingPrompts.get_default_chunk_size(RefinementStyle.SUMMARY)
        assert isinstance(chunk_size, int)
        assert chunk_size > 0
        
        # Summary should have larger chunk size
        summary_size = ProcessingPrompts.get_default_chunk_size(RefinementStyle.SUMMARY)
        detailed_size = ProcessingPrompts.get_default_chunk_size(RefinementStyle.BALANCED_DETAILED)
        assert summary_size >= detailed_size


class TestGeminiModels:
    """Tests for GeminiModels class."""
    
    def test_get_models(self):
        """Test getting available models."""
        models = GeminiModels.get_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "gemini-2.5-flash" in models
    
    def test_get_default_model(self):
        """Test getting default model."""
        default_model = GeminiModels.get_default_model()
        assert isinstance(default_model, str)
        assert default_model in GeminiModels.get_models()


class TestTranscriptVideo:
    """Tests for TranscriptVideo dataclass."""
    
    def test_successful_video(self):
        """Test creating a successful transcript video."""
        video = TranscriptVideo(
            url="https://example.com/video1",
            title="Test Video",
            content="This is the transcript content.",
            success=True
        )
        
        assert video.success is True
        assert video.error_message is None
        assert video.content == "This is the transcript content."
    
    def test_failed_video(self):
        """Test creating a failed transcript video."""
        video = TranscriptVideo(
            url="https://example.com/video2",
            title=None,
            content="",
            success=False,
            error_message="No transcript available"
        )
        
        assert video.success is False
        assert video.error_message == "No transcript available"
        assert video.content == ""


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""
    
    def test_successful_result(self):
        """Test creating a successful processing result."""
        result = ProcessingResult(
            success=True,
            output_file="output.txt",
            videos_processed=5,
            total_videos=5
        )
        
        assert result.success is True
        assert result.error_message is None
        assert result.videos_processed == 5
        assert result.total_videos == 5
    
    def test_failed_result(self):
        """Test creating a failed processing result."""
        result = ProcessingResult(
            success=False,
            error_message="API key invalid"
        )
        
        assert result.success is False
        assert result.error_message == "API key invalid"
        assert result.output_file is None
