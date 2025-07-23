"""
Tests for the validators module.
"""

import os
import pytest
from unittest.mock import Mock, patch
from youtube_transcript_extractor.src.utils.validators import InputValidator


@pytest.mark.unit
class TestInputValidator:
    """Tests for InputValidator class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.validator = InputValidator()
    
    def test_init(self):
        """Test InputValidator initialization."""
        assert self.validator is not None
    
    def test_validate_youtube_url_valid_watch_url(self):
        """Test validation of valid YouTube watch URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=123",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            assert self.validator.validate_youtube_url(url) is True
    
    def test_validate_youtube_url_valid_short_url(self):
        """Test validation of valid YouTube short URLs."""
        valid_urls = [
            "https://youtu.be/dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ?t=30"
        ]
        
        for url in valid_urls:
            assert self.validator.validate_youtube_url(url) is True
    
    def test_validate_youtube_url_valid_playlist_url(self):
        """Test validation of valid YouTube playlist URLs."""
        valid_urls = [
            "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy4XM6YsJfxrxXgT6KqA0",
            "https://youtube.com/playlist?list=PLrAXtmRdnEQy4XM6YsJfxrxXgT6KqA0",
            "https://m.youtube.com/playlist?list=PLrAXtmRdnEQy4XM6YsJfxrxXgT6KqA0",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest"
        ]
        
        for url in valid_urls:
            assert self.validator.validate_youtube_url(url) is True
    
    def test_validate_youtube_url_invalid_url(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            "https://www.google.com",
            "https://vimeo.com/123456",
            "https://www.facebook.com/video",
            "not_a_url",
            "",
            "https://youtube.com",  # No video or playlist
            "https://www.youtube.com/channel/UCtest",  # Channel URL
            "https://www.youtube.com/user/testuser"  # User URL
        ]
        
        for url in invalid_urls:
            assert self.validator.validate_youtube_url(url) is False
    
    def test_validate_youtube_url_malformed_url(self):
        """Test validation of malformed URLs."""
        malformed_urls = [
            "htp://www.youtube.com/watch?v=test",  # Typo in protocol
            "https://youtub.com/watch?v=test",  # Typo in domain
            "https://www.youtube.com/wach?v=test",  # Typo in path
            "https://www.youtube.com/watch?=test",  # Missing parameter
            "https://www.youtube.com/watch?v=",  # Empty video ID
        ]
        
        for url in malformed_urls:
            assert self.validator.validate_youtube_url(url) is False
    
    def test_validate_api_key_valid(self):
        """Test validation of valid API keys."""
        valid_keys = [
            "AIzaSyDummyApiKey1234567890abcdef",
            "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
            "AIzaSy" + "a" * 32  # 39 characters total
        ]
        
        for key in valid_keys:
            assert self.validator.validate_api_key(key) is True
    
    def test_validate_api_key_invalid(self):
        """Test validation of invalid API keys."""
        invalid_keys = [
            "",  # Empty
            "short",  # Too short
            "NotStartingWithAIzaSy1234567890abcdef",  # Wrong prefix
            "AIzaSy" + "a" * 50,  # Too long
            "AIzaSy123456789",  # Too short even with prefix
            None  # None value
        ]
        
        for key in invalid_keys:
            assert self.validator.validate_api_key(key) is False
    
    def test_validate_file_path_valid(self, temp_dir):
        """Test validation of valid file paths."""
        import os
        
        # Create a test file
        test_file = os.path.join(temp_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        valid_paths = [
            test_file,  # Existing file
            os.path.join(temp_dir, "new_file.txt"),  # Valid directory, new file
            os.path.join(temp_dir, "subdir", "file.txt")  # Nested path
        ]
        
        for path in valid_paths:
            assert self.validator.validate_file_path(path) is True
    
    def test_validate_file_path_invalid(self):
        """Test validation of invalid file paths."""
        invalid_paths = [
            "",  # Empty path
            "/nonexistent/directory/file.txt",  # Non-existent directory
            "con.txt",  # Reserved name on Windows
            "file?.txt",  # Invalid character
            "a" * 300 + ".txt"  # Path too long
        ]
        
        for path in invalid_paths:
            assert self.validator.validate_file_path(path) is False
    
    def test_validate_chunk_size_valid(self):
        """Test validation of valid chunk sizes."""
        valid_sizes = [
            500,   # Minimum
            1000,  # Common size
            5000,  # Large but valid
            10000  # Maximum
        ]
        
        for size in valid_sizes:
            assert self.validator.validate_chunk_size(size) is True
    
    def test_validate_chunk_size_invalid(self):
        """Test validation of invalid chunk sizes."""
        invalid_sizes = [
            0,      # Zero
            -100,   # Negative  
            400,    # Below minimum
            15000,  # Above maximum
            "1000", # String instead of int
            None    # None value
        ]
        
        for size in invalid_sizes:
            assert self.validator.validate_chunk_size(size) is False
    
    def test_validate_language_valid(self):
        """Test validation of valid languages."""
        valid_languages = [
            "English",
            "Spanish", 
            "French",
            "German",
            "Chinese",
            "Japanese",
            "Korean",
            "Portuguese",
            "Russian",
            "Arabic"
        ]
        
        for language in valid_languages:
            assert self.validator.validate_language(language) is True
    
    def test_validate_language_invalid(self):
        """Test validation of invalid languages."""
        invalid_languages = [
            "",  # Empty
            "NotALanguage",  # Made up
            "123",  # Numbers
            "En",  # Too short
            None  # None value
        ]
        
        for language in invalid_languages:
            assert self.validator.validate_language(language) is False
    
    def test_validate_gemini_model_valid(self):
        """Test validation of valid Gemini models."""
        # Mock the GeminiModels.get_models() call
        with patch('youtube_transcript_extractor.src.utils.validators.GeminiModels') as mock_gemini:
            mock_gemini.get_models.return_value = [
                "gemini-2.5-flash", 
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ]
            
            valid_models = [
                "gemini-2.5-flash",
                "gemini-1.5-pro", 
                "gemini-1.5-flash"
            ]
            
            for model in valid_models:
                assert self.validator.validate_gemini_model(model) is True
    
    def test_validate_gemini_model_invalid(self):
        """Test validation of invalid Gemini models."""
        # Mock the GeminiModels.get_models() call
        with patch('youtube_transcript_extractor.src.utils.validators.GeminiModels') as mock_gemini:
            mock_gemini.get_models.return_value = [
                "gemini-2.5-flash",
                "gemini-1.5-pro"
            ]
            
            invalid_models = [
                "",  # Empty
                "gpt-4",  # Wrong model family
                "gemini-3.0",  # Non-existent version
                "invalid-model",  # Completely wrong
                None  # None value
            ]
            
            for model in invalid_models:
                assert self.validator.validate_gemini_model(model) is False
    
    def test_validate_export_format_valid(self):
        """Test validation of valid export formats."""
        # Mock the ExportManager
        with patch('youtube_transcript_extractor.src.utils.validators.ExportManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.get_available_formats.return_value = ['markdown', 'html', 'pdf', 'docx']
            mock_manager.return_value = mock_instance
            
            valid_formats = ['markdown', 'html', 'pdf', 'docx']
            
            for format_name in valid_formats:
                assert self.validator.validate_export_format(format_name) is True
    
    def test_validate_export_format_invalid(self):
        """Test validation of invalid export formats."""
        # Mock the ExportManager
        with patch('youtube_transcript_extractor.src.utils.validators.ExportManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.get_available_formats.return_value = ['markdown', 'html']
            mock_manager.return_value = mock_instance
            
            invalid_formats = [
                "",  # Empty
                "xml",  # Not available
                "json",  # Not available
                "invalid",  # Completely wrong
                None  # None value
            ]
            
            for format_name in invalid_formats:
                assert self.validator.validate_export_format(format_name) is False
    
    def test_validate_multiple_formats_valid(self):
        """Test validation of multiple export formats."""
        # Mock the ExportManager
        with patch('youtube_transcript_extractor.src.utils.validators.ExportManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.get_available_formats.return_value = ['markdown', 'html', 'pdf', 'docx']
            mock_manager.return_value = mock_instance
            
            valid_format_lists = [
                ['markdown'],
                ['markdown', 'html'],
                ['markdown', 'html', 'pdf'],
                ['html', 'docx']
            ]
            
            for formats in valid_format_lists:
                assert self.validator.validate_multiple_formats(formats) is True
    
    def test_validate_multiple_formats_invalid(self):
        """Test validation of invalid multiple export formats."""
        # Mock the ExportManager
        with patch('youtube_transcript_extractor.src.utils.validators.ExportManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.get_available_formats.return_value = ['markdown', 'html']
            mock_manager.return_value = mock_instance
            
            invalid_format_lists = [
                [],  # Empty list
                ['invalid'],  # Invalid format
                ['markdown', 'invalid'],  # Mix of valid and invalid
                ['pdf'],  # Not available
                None  # None value
            ]
            
            for formats in invalid_format_lists:
                assert self.validator.validate_multiple_formats(formats) is False
    
    def test_extract_video_id_from_valid_urls(self):
        """Test extracting video ID from various URL formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ&list=123", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            video_id = self.validator._extract_video_id(url)
            assert video_id == expected_id
    
    def test_extract_video_id_from_invalid_urls(self):
        """Test extracting video ID from invalid URLs."""
        invalid_urls = [
            "https://www.google.com",
            "https://vimeo.com/123456",
            "not_a_url",
            ""
        ]
        
        for url in invalid_urls:
            video_id = self.validator._extract_video_id(url)
            assert video_id is None
    
    def test_extract_playlist_id_from_valid_urls(self):
        """Test extracting playlist ID from valid URLs."""
        test_cases = [
            ("https://www.youtube.com/playlist?list=PLtest123", "PLtest123"),
            ("https://youtube.com/playlist?list=PLtest123&index=1", "PLtest123"),
            ("https://m.youtube.com/playlist?list=PLtest123", "PLtest123"),
        ]
        
        for url, expected_id in test_cases:
            playlist_id = self.validator._extract_playlist_id(url)
            assert playlist_id == expected_id
    
    def test_extract_playlist_id_from_invalid_urls(self):
        """Test extracting playlist ID from invalid URLs."""
        invalid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.google.com",
            "not_a_url"
        ]
        
        for url in invalid_urls:
            playlist_id = self.validator._extract_playlist_id(url)
            assert playlist_id is None
    
    def test_sanitize_filename_valid(self):
        """Test filename sanitization with valid inputs."""
        test_cases = [
            ("normal_filename", "normal_filename"),
            ("file with spaces", "file_with_spaces"),
            ("file-with-dashes", "file-with-dashes"),
            ("file.with.dots", "file.with.dots"),
        ]
        
        for input_name, expected in test_cases:
            result = self.validator._sanitize_filename(input_name)
            assert result == expected
    
    def test_sanitize_filename_invalid_characters(self):
        """Test filename sanitization with invalid characters."""
        test_cases = [
            ("file<>name", "file__name"),
            ("file|name", "file_name"),
            ("file?name", "file_name"),
            ("file*name", "file_name"),
            ("file\"name", "file_name"),
            ("file/name", "file_name"),
            ("file\\name", "file_name"),
        ]
        
        for input_name, expected in test_cases:
            result = self.validator._sanitize_filename(input_name)
            assert result == expected
    
    def test_sanitize_filename_empty_or_reserved(self):
        """Test filename sanitization with empty or reserved names."""
        test_cases = [
            ("", "default_filename"),
            ("con", "con_file"),
            ("aux", "aux_file"),
            ("nul", "nul_file"),
            ("COM1", "COM1_file"),
        ]
        
        for input_name, expected in test_cases:
            result = self.validator._sanitize_filename(input_name)
            assert result == expected
    
    def test_is_safe_path_valid(self, temp_dir):
        """Test path safety validation with valid paths."""
        import os
        
        valid_paths = [
            os.path.join(temp_dir, "file.txt"),
            os.path.join(temp_dir, "subdir", "file.txt"),
            os.path.join(temp_dir, "normal-filename.txt"),
        ]
        
        for path in valid_paths:
            assert self.validator._is_safe_path(path) is True
    
    def test_is_safe_path_invalid(self):
        """Test path safety validation with invalid paths."""
        invalid_paths = [
            "../../../etc/passwd",  # Path traversal
            "/etc/passwd",  # Absolute system path
            "C:\\Windows\\System32\\file.txt",  # Windows system path
            "file\x00.txt",  # Null byte
            "",  # Empty path
        ]
        
        for path in invalid_paths:
            assert self.validator._is_safe_path(path) is False


@pytest.mark.integration
class TestInputValidatorIntegration:
    """Integration tests for InputValidator."""
    
    def test_comprehensive_validation_workflow(self, temp_dir):
        """Test a complete validation workflow."""
        validator = InputValidator()
        
        # Test a complete validation scenario
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        api_key = "AIzaSyDummyApiKey1234567890abcdef"
        output_file = os.path.join(temp_dir, "output.txt")
        chunk_size = 3000
        language = "English"
        
        # All validations should pass
        assert validator.validate_youtube_url(youtube_url) is True
        assert validator.validate_api_key(api_key) is True
        assert validator.validate_file_path(output_file) is True
        assert validator.validate_chunk_size(chunk_size) is True
        assert validator.validate_language(language) is True
        
        # Test with invalid values
        assert validator.validate_youtube_url("https://google.com") is False
        assert validator.validate_api_key("invalid") is False
        assert validator.validate_chunk_size(50000) is False


if __name__ == '__main__':
    pytest.main([__file__])
