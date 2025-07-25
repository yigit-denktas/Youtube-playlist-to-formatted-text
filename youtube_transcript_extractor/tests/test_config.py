"""
Tests for the config utilities.
"""

import pytest
import os
from unittest.mock import patch, mock_open

from youtube_transcript_extractor.src.utils.config import ConfigManager, DefaultPaths
from youtube_transcript_extractor.src.core.models import GeminiModels, RefinementStyle


class TestConfigManager:
    """Tests for ConfigManager class."""
    
    def test_init_with_env_file(self, config_manager_with_env):
        """Test initialization with environment file."""
        config = config_manager_with_env
        assert config.env_file.endswith(".env")
    
    def test_get_language_from_env(self, config_manager_with_env):
        """Test getting language from environment."""
        language = config_manager_with_env.get_language()
        assert language == "Spanish"
    
    def test_get_language_default(self, monkeypatch, temp_dir):
        """Test getting default language when not set in environment."""
        monkeypatch.delenv("LANGUAGE", raising=False)
        config = ConfigManager(env_file=os.path.join(temp_dir, "non_existent.env"))
        assert config.get_language() == "English"
    
    def test_get_api_key_from_env(self, config_manager_with_env):
        """Test getting API key from environment."""
        # Mock secure storage to return empty so it falls back to env file
        with patch.object(config_manager_with_env.secure_manager, 'get_api_key', return_value=""):
            api_key = config_manager_with_env.get_api_key()
            assert api_key == "test_api_key_from_env"
    
    def test_get_refinement_style_from_env(self, config_manager_with_env):
        """Test getting refinement style from environment."""
        # Mock get_env_value to return the expected value
        with patch.object(config_manager_with_env, 'get_env_value') as mock_get_env:
            mock_get_env.return_value = "Summary"
            style = config_manager_with_env.get_refinement_style()
            
            # Check that it returns the correct enum value
            assert style.value == "Summary"
            assert style.name == "SUMMARY"
            mock_get_env.assert_called_with("REFINEMENT_STYLE", "Balanced and Detailed")
    
    def test_get_refinement_style_default(self, temp_dir):
        """Test getting default refinement style when not in env."""
        empty_env = os.path.join(temp_dir, "empty.env")
        with open(empty_env, 'w') as f:
            f.write("")
        
        config = ConfigManager(empty_env)
        style = config.get_refinement_style()
        assert style == RefinementStyle.SUMMARY
    
    def test_get_chunk_size_from_env(self, config_manager_with_env):
        """Test getting chunk size from environment."""
        chunk_size = config_manager_with_env.get_chunk_size()
        assert chunk_size == 5000
    
    def test_get_chunk_size_invalid(self, temp_dir):
        """Test getting chunk size with invalid value."""
        env_file = os.path.join(temp_dir, "invalid.env")
        with open(env_file, 'w') as f:
            f.write("CHUNK_SIZE=invalid_number")
        
        config = ConfigManager(env_file)
        chunk_size = config.get_chunk_size()
        assert chunk_size == 3000  # Default value
    
    def test_get_chunk_size_out_of_range(self, temp_dir):
        """Test getting chunk size with out of range value."""
        env_file = os.path.join(temp_dir, "outofrange.env")
        with open(env_file, 'w') as f:
            f.write("CHUNK_SIZE=100")  # Too small
        
        config = ConfigManager(env_file)
        chunk_size = config.get_chunk_size()
        assert chunk_size == 3000  # Default value
    
    def test_get_gemini_model_from_env(self, config_manager_with_env):
        """Test getting Gemini model from environment."""
        model = config_manager_with_env.get_gemini_model()
        assert model == "gemini-1.5-pro"
    
    def test_get_gemini_model_invalid(self, temp_dir):
        """Test getting Gemini model with invalid value."""
        env_file = os.path.join(temp_dir, "invalid_model.env")
        with open(env_file, 'w') as f:
            f.write("GEMINI_MODEL=invalid_model")
        
        config = ConfigManager(env_file)
        model = config.get_gemini_model()
        assert model == GeminiModels.get_default_model()
    
    def test_get_auto_fill_data(self, config_manager_with_env):
        """Test getting auto-fill data."""
        # Mock secure storage to return empty so it falls back to env file
        with patch.object(config_manager_with_env.secure_manager, 'get_api_key', return_value=""):
            data = config_manager_with_env.get_auto_fill_data()
            
            assert isinstance(data, dict)
            assert data["language"] == "Spanish"
            assert data["api_key"] == "test_api_key_from_env"
            assert data["refinement_style"].value == "Summary"
            assert data["refinement_style"].name == "SUMMARY"
            assert data["chunk_size"] == 5000
            assert data["gemini_model"] == "gemini-1.5-pro"
    
    def test_count_filled_fields(self, config_manager_with_env):
        """Test counting filled fields."""
        count = config_manager_with_env.count_filled_fields()
        assert count >= 4  # At least language, api_key, refinement_style, chunk_size


class TestDefaultPaths:
    """Tests for DefaultPaths class."""
    
    def test_get_default_transcript_filename(self):
        """Test generating default transcript filename."""
        filename = DefaultPaths.get_default_transcript_filename()
        assert filename.startswith("transcript_")
        assert filename.endswith(".txt")
        assert len(filename) > 15  # Should include timestamp
    
    def test_get_default_gemini_filename(self):
        """Test generating default Gemini filename."""
        filename = DefaultPaths.get_default_gemini_filename()
        assert filename.startswith("gemini_output_")
        assert filename.endswith(".txt")
        assert len(filename) > 20  # Should include timestamp
    
    def test_ensure_txt_extension(self):
        """Test ensuring .txt extension."""
        # Test file without extension
        result = DefaultPaths.ensure_txt_extension("myfile")
        assert result == "myfile.txt"
        
        # Test file with .txt extension
        result = DefaultPaths.ensure_txt_extension("myfile.txt")
        assert result == "myfile.txt"
        
        # Test file with other extension
        result = DefaultPaths.ensure_txt_extension("myfile.doc")
        assert result == "myfile.doc.txt"
