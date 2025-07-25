"""
Configuration management utilities for the YouTube Transcript Extractor application.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from .secure_config import SecureConfigManager

# Use centralized dependency management for core models
from .dependencies import safe_import

# Import core models safely
ProcessingConfig, models_available = safe_import("core.models.ProcessingConfig")
ProcessingMode, _ = safe_import("core.models.ProcessingMode")
GeminiModels, _ = safe_import("core.models.GeminiModels")
RefinementStyle, _ = safe_import("core.models.RefinementStyle")

# Provide fallbacks if models can't be imported
if not models_available:
    ProcessingConfig = None
    ProcessingMode = None
    GeminiModels = None


class ConfigManager:
    """Manages application configuration from environment variables and defaults."""
    
    def __init__(self, env_file: str = ".env"):
        """Initialize configuration manager.
        
        Args:
            env_file: Path to the environment file
        """
        self.env_file = env_file
        self.secure_manager = SecureConfigManager()
        self.load_environment()
        
        # Attempt migration on first run if needed
        if self.secure_manager.is_setup_required():
            self.secure_manager.migrate_from_env(env_file)
    
    def load_environment(self) -> None:
        """Load environment variables from the .env file."""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file, override=True)
    
    def get_env_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value.
        
        Args:
            key: Environment variable key
            default: Default value if key not found
            
        Returns:
            Environment variable value or default
        """
        return os.environ.get(key, default)
    
    def get_language(self) -> str:
        """Get output language from environment or default."""
        return self.get_env_value("LANGUAGE", "English") or "English"
    
    def get_api_key(self) -> str:
        """Get Gemini API key from secure storage first, then environment."""
        # Try secure storage first
        api_key = self.secure_manager.get_api_key("gemini_api_key")
        
        # Fallback to environment variable
        if not api_key:
            api_key = self.get_env_value("API_KEY", "") or ""
            
            # If found in env and valid, migrate to secure storage
            if api_key and api_key.strip() and api_key != "your_api_key_here":
                self.secure_manager.store_api_key("gemini_api_key", api_key)
        
        return api_key or ""
    
    def set_api_key(self, api_key: str) -> bool:
        """Set API key in secure storage.
        
        Args:
            api_key: The API key to store
            
        Returns:
            True if stored successfully
        """
        return self.secure_manager.store_api_key("gemini_api_key", api_key)
    
    def get_transcript_output_file(self) -> str:
        """Get transcript output file from environment."""
        return self.get_env_value("TRANSCRIPT_OUTPUT_FILE", "") or ""
    
    def get_gemini_output_file(self) -> str:
        """Get Gemini output file from environment."""
        return self.get_env_value("GEMINI_OUTPUT_FILE", "") or ""
    
    def get_refinement_style(self):
        """Get refinement style from environment or default."""
        if not RefinementStyle:
            return "Balanced and Detailed"  # Fallback string
            
        style_name = self.get_env_value("REFINEMENT_STYLE", "Balanced and Detailed")
        
        # Try to match the environment value to a RefinementStyle
        for style in RefinementStyle:
            if style.value == style_name:
                return style
        
        return getattr(RefinementStyle, 'BALANCED_DETAILED', "Balanced and Detailed")
    
    def get_chunk_size(self) -> int:
        """Get chunk size from environment or default."""
        chunk_size_str = self.get_env_value("CHUNK_SIZE", "3000")
        if chunk_size_str:
            try:
                chunk_size = int(chunk_size_str)
                # Validate range
                if 2000 <= chunk_size <= 50000:
                    return chunk_size
            except (ValueError, TypeError):
                pass
        
        return 3000  # Default
    
    def get_gemini_model(self) -> str:
        """Get Gemini model from environment or default."""
        model_name = self.get_env_value("GEMINI_MODEL", "")
        
        # Validate model exists in available models
        if GeminiModels and hasattr(GeminiModels, 'get_models'):
            if model_name and model_name in GeminiModels.get_models():
                return model_name
            return GeminiModels.get_default_model()
        
        # Fallback if GeminiModels not available
        return model_name or "gemini-1.5-flash"
    
    def get_auto_fill_data(self) -> Dict[str, Any]:
        """Get all configuration data for auto-fill functionality.
        
        Returns:
            Dictionary containing all configuration values
        """
        return {
            "language": self.get_language(),
            "api_key": self.get_api_key(),
            "transcript_output_file": self.get_transcript_output_file(),
            "gemini_output_file": self.get_gemini_output_file(),
            "refinement_style": self.get_refinement_style(),
            "chunk_size": self.get_chunk_size(),
            "gemini_model": self.get_gemini_model()
        }
    
    def count_filled_fields(self) -> int:
        """Count how many fields have non-empty values from environment.
        
        Returns:
            Number of fields with values
        """
        data = self.get_auto_fill_data()
        count = 0
        
        # Count non-empty string values
        for key, value in data.items():
            if key in ["language", "api_key", "transcript_output_file", "gemini_output_file", "gemini_model"]:
                if value and value.strip():
                    count += 1
            elif key == "refinement_style":
                # Check if it's not the default
                default_check = getattr(RefinementStyle, 'BALANCED_DETAILED', "Balanced and Detailed") if RefinementStyle else "Balanced and Detailed"
                if value != default_check:
                    count += 1
            elif key == "chunk_size":
                # Check if it's not the default
                if value != 3000:
                    count += 1
        
        return count
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get security status information.
        
        Returns:
            Dictionary with security status
        """
        return self.secure_manager.get_security_status()
    
    def is_secure_storage_available(self) -> bool:
        """Check if secure storage is available.
        
        Returns:
            True if secure storage is available
        """
        status = self.get_security_status()
        return status.get("secure_storage_enabled", False)
    
    def save_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Save user preferences to secure storage.
        
        Args:
            preferences: Dictionary of preferences to save
            
        Returns:
            True if saved successfully
        """
        return self.secure_manager.save_config(preferences)
    
    def load_preferences(self) -> Dict[str, Any]:
        """Load user preferences from secure storage.
        
        Returns:
            Dictionary of preferences
        """
        return self.secure_manager.load_config()


class DefaultPaths:
    """Default file paths and naming conventions."""
    
    @staticmethod
    def get_default_transcript_filename() -> str:
        """Generate default transcript filename with timestamp."""
        from datetime import datetime
        return f"transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    @staticmethod
    def get_default_gemini_filename() -> str:
        """Generate default Gemini output filename with timestamp."""
        from datetime import datetime
        return f"gemini_output_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    @staticmethod
    def ensure_txt_extension(filename: str) -> str:
        """Ensure filename has .txt extension.
        
        Args:
            filename: Input filename
            
        Returns:
            Filename with .txt extension
        """
        if not filename.endswith(".txt"):
            return f"{filename}.txt"
        return filename
