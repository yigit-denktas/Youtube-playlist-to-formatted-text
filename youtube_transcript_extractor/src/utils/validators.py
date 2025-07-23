"""
Validation utilities for the YouTube Transcript Extractor application.
"""

import os
import glob
from typing import Tuple, List, Optional, Union
from urllib.parse import urlparse, parse_qs


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Validates user input for the application."""
    
    @staticmethod
    def validate_youtube_url(url: str, return_tuple: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Validate YouTube URL.
        
        Args:
            url: YouTube URL to validate
            return_tuple: If False, returns only boolean for backward compatibility
            
        Returns:
            Tuple of (is_valid, error_message) or just boolean if return_tuple=False
        """
        if not url or not url.strip():
            result = (False, "URL cannot be empty")
        else:
            url = url.strip()
            
            # Check if it's a valid YouTube URL (including youtu.be short URLs)
            valid_patterns = [
                "https://www.youtube.com/playlist",
                "https://www.youtube.com/watch?v=",
                "https://youtube.com/playlist", 
                "https://youtube.com/watch?v=",
                "https://m.youtube.com/playlist",
                "https://m.youtube.com/watch?v=",
                "http://www.youtube.com/playlist",
                "http://www.youtube.com/watch?v=",
                "http://youtube.com/playlist",
                "http://youtube.com/watch?v=",
                "http://m.youtube.com/playlist",
                "http://m.youtube.com/watch?v=",
                "https://youtu.be/",
                "http://youtu.be/"
            ]
            
            if not any(url.startswith(pattern) for pattern in valid_patterns):
                result = (False, "Please enter a valid YouTube playlist or video URL")
            else:
                # Additional validation for playlist URLs
                if "playlist?list=" in url:
                    parsed = urlparse(url)
                    query_params = parse_qs(parsed.query)
                    if 'list' not in query_params or not query_params['list'][0]:
                        result = (False, "Invalid playlist URL: missing playlist ID")
                    else:
                        result = (True, "")
                
                # Additional validation for video URLs
                elif "watch?v=" in url or "youtu.be/" in url:
                    if "youtu.be/" in url:
                        # Extract video ID from youtu.be URLs
                        video_id = url.split("youtu.be/")[1].split("?")[0]
                        if not video_id:
                            result = (False, "Invalid video URL: missing video ID")
                        else:
                            result = (True, "")
                    else:
                        parsed = urlparse(url)
                        query_params = parse_qs(parsed.query)
                        if 'v' not in query_params or not query_params['v'][0]:
                            result = (False, "Invalid video URL: missing video ID")
                        else:
                            result = (True, "")
                else:
                    result = (True, "")
        
        return result if return_tuple else result[0]
    
    # Boolean-only wrapper methods for backward compatibility with tests
    @classmethod
    def validate_youtube_url_bool(cls, url: str) -> bool:
        """Boolean-only wrapper for validate_youtube_url."""
        result = cls.validate_youtube_url(url, return_tuple=True)
        return result[0] if isinstance(result, tuple) else result
    
    @classmethod  
    def validate_api_key_bool(cls, api_key: str) -> bool:
        """Boolean-only wrapper for validate_api_key."""
        result = cls.validate_api_key(api_key, return_tuple=True)
        return result[0] if isinstance(result, tuple) else result
        
    @classmethod
    def validate_language_bool(cls, language: str) -> bool:
        """Boolean-only wrapper for validate_language."""
        result = cls.validate_language(language, return_tuple=True)
        return result[0] if isinstance(result, tuple) else result
        
    @classmethod
    def validate_chunk_size_bool(cls, chunk_size: int) -> bool:
        """Boolean-only wrapper for validate_chunk_size."""
        result = cls.validate_chunk_size(chunk_size, return_tuple=True)
        return result[0] if isinstance(result, tuple) else result

    @classmethod
    def validate_file_path_bool(cls, file_path: str) -> bool:
        """Boolean-only wrapper for validate_file_path."""
        validator = cls()
        result = validator.validate_file_path(file_path, return_tuple=True)
        return result[0] if isinstance(result, tuple) else result

    @classmethod
    def validate_gemini_model_bool(cls, model: str) -> bool:
        """Boolean-only wrapper for validate_gemini_model."""
        result = cls.validate_gemini_model(model, return_tuple=True)
        return result[0] if isinstance(result, tuple) else result

    @classmethod
    def validate_export_format_bool(cls, format_name: str) -> bool:
        """Boolean-only wrapper for validate_export_format."""
        result = cls.validate_export_format(format_name, return_tuple=True)
        return result[0] if isinstance(result, tuple) else result

    @classmethod
    def validate_multiple_formats_bool(cls, formats: List[str]) -> bool:
        """Boolean-only wrapper for validate_multiple_formats."""
        result = cls.validate_multiple_formats(formats, return_tuple=True)
        return result[0] if isinstance(result, tuple) else result
    
    @staticmethod
    def validate_gemini_model(model: str, return_tuple: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Validate Gemini model name.
        
        Args:
            model: Model name to validate
            return_tuple: If False, returns only boolean for backward compatibility
            
        Returns:
            Tuple of (is_valid, error_message) or just boolean if return_tuple=False
        """
        if not model or not model.strip():
            result = (False, "Model name cannot be empty")
        else:
            model = model.strip()
            
            # Valid Gemini models
            valid_models = [
                "gemini-pro",
                "gemini-pro-vision", 
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-2.0-flash",
                "gemini-2.0-flash-exp",
                "gemini-2.5-flash"
            ]
            
            if model not in valid_models:
                result = (False, f"Invalid model name. Valid models: {', '.join(valid_models)}")
            else:
                result = (True, "")
        
        return result if return_tuple else result[0]
    
    @staticmethod
    def validate_export_format(format_name: str, return_tuple: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Validate export format.
        
        Args:
            format_name: Format name to validate
            return_tuple: If False, returns only boolean for backward compatibility
            
        Returns:
            Tuple of (is_valid, error_message) or just boolean if return_tuple=False
        """
        if not format_name or not format_name.strip():
            result = (False, "Export format cannot be empty")
        else:
            format_name = format_name.strip().lower()
            
            valid_formats = ["txt", "md", "markdown", "html", "pdf", "json"]
            
            if format_name not in valid_formats:
                result = (False, f"Invalid export format. Valid formats: {', '.join(valid_formats)}")
            else:
                result = (True, "")
        
        return result if return_tuple else result[0]
        return result if return_tuple else result[0]
    
    @staticmethod
    def validate_multiple_formats(formats: List[str], return_tuple: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Validate multiple export formats.
        
        Args:
            formats: List of format names to validate
            return_tuple: If False, returns only boolean for backward compatibility
            
        Returns:
            Tuple of (is_valid, error_message) or just boolean if return_tuple=False
        """
        if not formats or not isinstance(formats, list):
            result = (False, "Formats must be a non-empty list")
        else:
            for format_name in formats:
                format_result = InputValidator.validate_export_format(format_name, return_tuple=True)
                if isinstance(format_result, tuple) and not format_result[0]:
                    result = (False, f"Invalid format '{format_name}': {format_result[1]}")
                    break
            else:
                result = (True, "")
        
        return result if return_tuple else result[0]
    
    @staticmethod
    def validate_local_folder(folder_path: str) -> Tuple[bool, str, List[str]]:
        """Validate local folder and check for transcript files.
        
        Args:
            folder_path: Path to the folder to validate
            
        Returns:
            Tuple of (is_valid, error_message, list_of_txt_files)
        """
        if not folder_path or not folder_path.strip():
            return False, "Folder path cannot be empty", []
        
        folder_path = folder_path.strip()
        
        # Check if folder exists
        if not os.path.exists(folder_path):
            return False, "Selected folder does not exist", []
        
        if not os.path.isdir(folder_path):
            return False, "Selected path is not a folder", []
        
        # Find .txt files
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        
        if not txt_files:
            return False, "Selected folder does not contain any .txt transcript files", []
        
        return True, "", txt_files
    
    @staticmethod
    def validate_output_file(file_path: str, file_type: str = "file") -> Tuple[bool, str]:
        """Validate output file path.
        
        Args:
            file_path: File path to validate
            file_type: Type of file for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path or not file_path.strip():
            return False, f"{file_type} path cannot be empty"
        
        file_path = file_path.strip()
        
        # Check extension
        if not file_path.endswith(".txt"):
            return False, f"{file_type} must be a .txt file"
        
        # Check if directory exists (for the parent directory)
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            return False, f"Directory does not exist: {parent_dir}"
        
        # Check if we can write to the location
        try:
            # Try to create a temporary file to test write permissions
            test_file = file_path + ".temp"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except (OSError, PermissionError):
            return False, f"Cannot write to the specified location: {file_path}"
        
        return True, ""
    
    @staticmethod
    def validate_api_key(api_key: str, return_tuple: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Validate Gemini API key.
        
        Args:
            api_key: API key to validate
            return_tuple: If False, returns only boolean for backward compatibility
            
        Returns:
            Tuple of (is_valid, error_message) or just boolean if return_tuple=False
        """
        if not api_key or not api_key.strip():
            result = (False, "Please enter your Gemini API key")
        else:
            api_key = api_key.strip()
            
            # Basic format validation for Google API keys
            if len(api_key) < 20:
                result = (False, "API key appears to be too short")
            elif not any(char.isalnum() for char in api_key):
                result = (False, "API key format appears invalid")
            else:
                result = (True, "")
        
        return result if return_tuple else result[0]
    
    @staticmethod
    def validate_language(language: str, return_tuple: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Validate output language.
        
        Args:
            language: Language to validate
            return_tuple: If False, returns only boolean for backward compatibility
            
        Returns:
            Tuple of (is_valid, error_message) or just boolean if return_tuple=False
        """
        if not language or not language.strip():
            result = (False, "Please specify the output language")
        else:
            language = language.strip()
            
            # Basic validation - ensure it contains at least alphabetic characters
            if not any(char.isalpha() for char in language):
                result = (False, "Language must contain valid alphabetic characters")
            else:
                result = (True, "")
        
        return result if return_tuple else result[0]
    
    @staticmethod
    def validate_chunk_size(chunk_size: int, return_tuple: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Validate chunk size.
        
        Args:
            chunk_size: Chunk size to validate
            return_tuple: If False, returns only boolean for backward compatibility
            
        Returns:
            Tuple of (is_valid, error_message) or just boolean if return_tuple=False
        """
        if not isinstance(chunk_size, int):
            result = (False, "Chunk size must be a number")
        elif chunk_size < 500:
            result = (False, "Chunk size must be at least 500 words")
        elif chunk_size > 50000:
            result = (False, "Chunk size cannot exceed 50,000 words")
        else:
            result = (True, "")
        
        return result if return_tuple else result[0]
    
    def validate_file_path(self, file_path: str, return_tuple: bool = False) -> Union[bool, Tuple[bool, str]]:
        """Validate file path for safety and accessibility.
        
        Args:
            file_path: File path to validate
            return_tuple: If False, returns only boolean for backward compatibility
            
        Returns:
            Tuple of (is_valid, error_message) or just boolean if return_tuple=False
        """
        if not file_path or not file_path.strip():
            result = (False, "File path cannot be empty")
        else:
            file_path = file_path.strip()
            
            # Check if path is safe
            if not self._is_safe_path(file_path):
                result = (False, "File path contains unsafe elements")
            else:
                # Check if directory exists or can be created
                directory = os.path.dirname(file_path)
                if directory and not os.path.exists(directory):
                    try:
                        os.makedirs(directory, exist_ok=True)
                        result = (True, "")
                    except (OSError, PermissionError):
                        result = (False, "Cannot create directory for file path")
                else:
                    result = (True, "")
                    
        return result if return_tuple else result[0]
    
    @staticmethod
    def validate_processing_inputs(source_url: str, source_folder: str, 
                                 transcript_file: str, gemini_file: str,
                                 api_key: str, language: str,
                                 chunk_size: int) -> Tuple[bool, str]:
        """Validate all processing inputs.
        
        Args:
            source_url: YouTube URL
            source_folder: Local folder path
            transcript_file: Transcript output file path
            gemini_file: Gemini output file path
            api_key: Gemini API key
            language: Output language
            chunk_size: Chunk size for processing
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check that at least one source is provided
        has_url = source_url and source_url.strip()
        has_folder = source_folder and source_folder.strip()
        
        if not has_url and not has_folder:
            return False, "Please enter a YouTube URL or select a local folder containing transcript files"
        
        # If both are provided, that's also invalid
        if has_url and has_folder:
            return False, "Please choose either YouTube URL OR local folder, not both"
        
        # Validate the provided source
        if has_url:
            result = InputValidator.validate_youtube_url(source_url, return_tuple=True)
            if isinstance(result, tuple):
                is_valid, error = result
                if not is_valid:
                    return False, error
        
        if has_folder:
            is_valid, error, _ = InputValidator.validate_local_folder(source_folder)
            if not is_valid:
                return False, error
        
        # Validate output files
        is_valid, error = InputValidator.validate_output_file(transcript_file, "Transcript output file")
        if not is_valid:
            return False, error
        
        is_valid, error = InputValidator.validate_output_file(gemini_file, "Gemini output file")
        if not is_valid:
            return False, error
        
        # Validate API key
        result = InputValidator.validate_api_key(api_key, return_tuple=True)
        if isinstance(result, tuple):
            is_valid, error = result
            if not is_valid:
                return False, error
        
        # Validate language
        result = InputValidator.validate_language(language, return_tuple=True)
        if isinstance(result, tuple):
            is_valid, error = result
            if not is_valid:
                return False, error
        
        # Validate chunk size
        result = InputValidator.validate_chunk_size(chunk_size, return_tuple=True)
        if isinstance(result, tuple):
            is_valid, error = result
            if not is_valid:
                return False, error
        
        return True, ""
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID if found, None otherwise
        """
        if not url:
            return None
            
        parsed = urlparse(url)
        if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            if parsed.path == '/watch':
                query_params = parse_qs(parsed.query)
                return query_params.get('v', [None])[0]
        elif parsed.hostname == 'youtu.be':
            return parsed.path[1:]  # Remove leading slash
            
        return None
    
    def _extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Playlist ID if found, None otherwise
        """
        if not url:
            return None
            
        parsed = urlparse(url)
        if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            if 'list=' in url:
                query_params = parse_qs(parsed.query)
                return query_params.get('list', [None])[0]
                
        return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename or not filename.strip():
            return "default_filename"
            
        # Windows reserved names
        reserved_names = {'con', 'aux', 'nul', 'prn', 'com1', 'com2', 'com3', 'com4', 
                         'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 
                         'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
        
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = filename.strip()
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
            
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        
        # Check for reserved names
        if sanitized.lower() in reserved_names:
            sanitized = f"{sanitized}_file"
            
        return sanitized
    
    def _is_safe_path(self, path: str) -> bool:
        """Check if a file path is safe (no path traversal, etc.).
        
        Args:
            path: File path to check
            
        Returns:
            True if path is safe, False otherwise
        """
        if not path or not path.strip():
            return False
            
        # Check for null bytes
        if '\x00' in path:
            return False
            
        # Check for path traversal attempts
        if '..' in path:
            return False
            
        # Check for absolute paths to system directories (basic check)
        if path.startswith('/etc/') or path.startswith('C:\\Windows\\'):
            return False
            
        return True


class FileValidator:
    """Validates file operations and paths."""
    
    @staticmethod
    def ensure_directory_exists(file_path: str) -> None:
        """Ensure the directory for a file path exists.
        
        Args:
            file_path: File path to check
            
        Raises:
            OSError: If directory cannot be created
        """
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def is_file_writable(file_path: str) -> bool:
        """Check if a file path is writable.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file is writable, False otherwise
        """
        try:
            FileValidator.ensure_directory_exists(file_path)
            test_file = file_path + ".temp"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except (OSError, PermissionError):
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get a safe filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe_filename = filename
        for char in invalid_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        safe_filename = safe_filename.strip('. ')
        
        # Ensure it's not empty
        if not safe_filename:
            safe_filename = "output"
        
        return safe_filename


# Module-level functions for backward compatibility with tests
def validate_youtube_url(url: str) -> bool:
    """Module-level boolean validator for YouTube URLs."""
    return InputValidator.validate_youtube_url_bool(url)

def validate_api_key(api_key: str) -> bool:
    """Module-level boolean validator for API keys."""
    return InputValidator.validate_api_key_bool(api_key)

def validate_language(language: str) -> bool:
    """Module-level boolean validator for languages."""
    return InputValidator.validate_language_bool(language)

def validate_chunk_size(chunk_size: int) -> bool:
    """Module-level boolean validator for chunk sizes."""
    return InputValidator.validate_chunk_size_bool(chunk_size)

def validate_file_path(file_path: str) -> bool:
    """Module-level boolean validator for file paths."""
    return InputValidator.validate_file_path_bool(file_path)

def validate_gemini_model(model: str) -> bool:
    """Module-level boolean validator for Gemini models."""
    return InputValidator.validate_gemini_model_bool(model)

def validate_export_format(format_name: str) -> bool:
    """Module-level boolean validator for export formats."""
    return InputValidator.validate_export_format_bool(format_name)

def validate_multiple_formats(formats: List[str]) -> bool:
    """Module-level boolean validator for multiple export formats."""
    return InputValidator.validate_multiple_formats_bool(formats)
