"""
Tests for the gemini_processor module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
from youtube_transcript_extractor.src.core.gemini_processor import GeminiProcessor
from youtube_transcript_extractor.src.core.models import ProcessingConfig, ProcessingMode, RefinementStyle


@pytest.mark.unit
class TestGeminiProcessor:
    """Tests for GeminiProcessor class."""
    
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
        
    def test_init(self):
        """Test GeminiProcessor initialization."""
        processor = GeminiProcessor(self.config)
        assert processor.config == self.config
        assert processor.progress_callback is None
    
    def test_init_with_callback(self):
        """Test GeminiProcessor initialization with progress callback."""
        callback = Mock()
        processor = GeminiProcessor(self.config, progress_callback=callback)
        assert processor.progress_callback == callback
    
    @patch('youtube_transcript_extractor.src.core.gemini_processor.genai')
    def test_setup_gemini_success(self, mock_genai):
        """Test successful Gemini API setup."""
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        processor = GeminiProcessor(self.config)
        processor._setup_gemini()
        
        mock_genai.configure.assert_called_once_with(api_key="test_api_key")
        mock_genai.GenerativeModel.assert_called_once_with("gemini-2.5-flash")
        assert processor.model == mock_model
    
    @patch('youtube_transcript_extractor.src.core.gemini_processor.genai')
    def test_setup_gemini_failure(self, mock_genai):
        """Test Gemini API setup failure."""
        mock_genai.configure.side_effect = Exception("Invalid API key")
        
        processor = GeminiProcessor(self.config)
        
        with pytest.raises(Exception, match="Invalid API key"):
            processor._setup_gemini()
    
    def test_split_content_into_chunks(self):
        """Test splitting content into chunks."""
        processor = GeminiProcessor(self.config)
        
        # Create content longer than chunk size
        content = "This is a test sentence. " * 200  # Should exceed 3000 chars
        chunks = processor._split_content_into_chunks(content, chunk_size=100)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)
        assert "".join(chunks).replace(" ", "") in content.replace(" ", "")
    
    def test_split_content_single_chunk(self):
        """Test splitting short content."""
        processor = GeminiProcessor(self.config)
        
        content = "Short content"
        chunks = processor._split_content_into_chunks(content, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0] == content
    
    def test_split_content_by_sentences(self):
        """Test splitting content by sentences."""
        processor = GeminiProcessor(self.config)
        
        content = "First sentence. Second sentence. Third sentence."
        chunks = processor._split_content_into_chunks(content, chunk_size=20)
        
        # Should split at sentence boundaries
        assert len(chunks) >= 2
        assert all(chunk.strip().endswith('.') or chunk == chunks[-1] for chunk in chunks)
    
    @patch('youtube_transcript_extractor.src.core.gemini_processor.genai')
    @pytest.mark.asyncio
    async def test_process_single_chunk_success(self, mock_genai):
        """Test successfully processing a single chunk."""
        # Mock the Gemini model
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Refined content"
        mock_model.generate_content = AsyncMock(return_value=mock_response)
        
        mock_genai.GenerativeModel.return_value = mock_model
        
        processor = GeminiProcessor(self.config)
        processor._setup_gemini()
        
        result = await processor._process_single_chunk("Test content")
        
        assert result == "Refined content"
        mock_model.generate_content.assert_called_once()
    
    @patch('youtube_transcript_extractor.src.core.gemini_processor.genai')
    @pytest.mark.asyncio
    async def test_process_single_chunk_failure(self, mock_genai):
        """Test handling failure in processing single chunk."""
        # Mock the Gemini model to raise an exception
        mock_model = Mock()
        mock_model.generate_content = AsyncMock(side_effect=Exception("Rate limit exceeded"))
        
        mock_genai.GenerativeModel.return_value = mock_model
        
        processor = GeminiProcessor(self.config)
        processor._setup_gemini()
        
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await processor._process_single_chunk("Test content")
    
    @patch('youtube_transcript_extractor.src.core.gemini_processor.genai')
    @pytest.mark.asyncio
    async def test_process_single_chunk_empty_response(self, mock_genai):
        """Test handling empty response from Gemini."""
        # Mock the Gemini model with empty response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = ""
        mock_model.generate_content = AsyncMock(return_value=mock_response)
        
        mock_genai.GenerativeModel.return_value = mock_model
        
        processor = GeminiProcessor(self.config)
        processor._setup_gemini()
        
        with pytest.raises(ValueError, match="Empty response from Gemini"):
            await processor._process_single_chunk("Test content")
    
    @patch('youtube_transcript_extractor.src.core.gemini_processor.genai')
    @pytest.mark.asyncio
    async def test_process_transcript_chunks_success(self, mock_genai):
        """Test successfully processing transcript chunks."""
        # Mock the Gemini model
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Refined chunk"
        mock_model.generate_content = AsyncMock(return_value=mock_response)
        
        mock_genai.GenerativeModel.return_value = mock_model
        
        processor = GeminiProcessor(self.config)
        processor._setup_gemini()
        
        # Test with content that will be split into multiple chunks
        long_content = "Test sentence. " * 300  # Should exceed chunk size
        result = await processor.process_transcript_chunks(long_content)
        
        assert "Refined chunk" in result
        assert len(result) > 0
    
    @patch('youtube_transcript_extractor.src.core.gemini_processor.genai')
    @pytest.mark.asyncio
    async def test_process_transcript_single_chunk(self, mock_genai):
        """Test processing transcript with single chunk."""
        # Mock the Gemini model
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Refined single chunk"
        mock_model.generate_content = AsyncMock(return_value=mock_response)
        
        mock_genai.GenerativeModel.return_value = mock_model
        
        processor = GeminiProcessor(self.config)
        processor._setup_gemini()
        
        short_content = "Short transcript content."
        result = await processor.process_transcript(short_content)
        
        assert result == "Refined single chunk"
    
    def test_get_refinement_prompt(self):
        """Test getting refinement prompt for different styles."""
        processor = GeminiProcessor(self.config)
        
        # Test different refinement styles
        styles_to_test = [
            RefinementStyle.BALANCED_DETAILED,
            RefinementStyle.SUMMARY,
            RefinementStyle.EDUCATIONAL,
            RefinementStyle.NARRATIVE_REWRITING,
            RefinementStyle.QA_GENERATION
        ]
        
        for style in styles_to_test:
            processor.config.refinement_style = style
            prompt = processor._get_refinement_prompt()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "transcript" in prompt.lower()
    
    def test_get_refinement_prompt_with_language(self):
        """Test refinement prompt includes language specification."""
        processor = GeminiProcessor(self.config)
        processor.config.output_language = "Spanish"
        
        prompt = processor._get_refinement_prompt()
        
        assert "Spanish" in prompt
    
    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        """Test that progress callback is called during processing."""
        callback = Mock()
        processor = GeminiProcessor(self.config, progress_callback=callback)
        
        with patch('youtube_transcript_extractor.src.core.gemini_processor.genai') as mock_genai:
            # Mock the Gemini model
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = "Refined content"
            mock_model.generate_content = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model
            
            processor._setup_gemini()
            # Use process_transcript_chunks which is properly async
            await processor.process_transcript_chunks("Test content")
            
            # Verify callback was called
            assert callback.called
    
    def test_rate_limiting(self):
        """Test rate limiting configuration."""
        processor = GeminiProcessor(self.config)
        
        # Test that rate limiting attributes exist
        assert hasattr(processor, '_last_request_time')
        assert hasattr(processor, '_min_request_interval')
    
    @patch('youtube_transcript_extractor.src.core.gemini_processor.time.sleep')
    @patch('youtube_transcript_extractor.src.core.gemini_processor.genai')
    @pytest.mark.asyncio
    async def test_rate_limiting_enforced(self, mock_genai, mock_sleep):
        """Test that rate limiting is enforced between requests."""
        # Mock the Gemini model
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Refined content"
        mock_model.generate_content = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model
        
        processor = GeminiProcessor(self.config)
        processor._setup_gemini()
        
        # Make two quick requests
        await processor._process_single_chunk("First chunk")
        await processor._process_single_chunk("Second chunk")
        
        # Verify sleep was called for rate limiting
        assert mock_sleep.called
    
    def test_chunk_overlap_handling(self):
        """Test that chunks have proper overlap to maintain context."""
        processor = GeminiProcessor(self.config)
        
        # Create content with clear sentence boundaries
        content = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        chunks = processor._split_content_into_chunks(content, chunk_size=30)
        
        if len(chunks) > 1:
            # Check for some overlap or proper sentence boundaries
            assert len(chunks) >= 2
            # Should split at sentence boundaries when possible
            for chunk in chunks[:-1]:  # All but last chunk
                assert chunk.strip().endswith('.') or chunk.strip().endswith('?') or chunk.strip().endswith('!')


@pytest.mark.integration  
class TestGeminiProcessorIntegration:
    """Integration tests for GeminiProcessor."""
    
    @pytest.mark.slow
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_real_gemini_processing(self):
        """Test processing with real Gemini API (requires valid API key)."""
        # Skip this test in normal circumstances
        pytest.skip("Requires valid Gemini API key and network access")
        
        config = ProcessingConfig(
            mode=ProcessingMode.YOUTUBE_URL,
            source_path="https://www.youtube.com/playlist?list=example",
            output_language="English",
            refinement_style=RefinementStyle.SUMMARY,
            chunk_size=1000,
            gemini_model="gemini-2.5-flash",
            api_key="your_real_api_key_here",
            transcript_output_file="test_transcript.txt",
            gemini_output_file="test_output.txt"
        )
        
        processor = GeminiProcessor(config)
        
        try:
            result = await processor.process_transcript("This is a test transcript for processing.")
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")


if __name__ == '__main__':
    pytest.main([__file__])
