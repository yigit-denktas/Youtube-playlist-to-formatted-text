"""
Validation utilities for the YouTube Transcript Extractor application.
"""

import os
import glob
from typing import Tuple, List, Optional
from urllib.parse import urlparse, parse_qs


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Validates user input for the application."""
    
    @staticmethod
    def validate_youtube_url(url: str) -> Tuple[bool, str]:
        """Validate YouTube URL.
        
        Args:
            url: YouTube URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url or not url.strip():
            return False, "URL cannot be empty"
        
        url = url.strip()
        
        # Check if it's a valid YouTube URL
        if not (url.startswith("https://www.youtube.com/playlist") or
                url.startswith("https://www.youtube.com/watch?v=")):
            return False, "Please enter a valid YouTube playlist or video URL"
        
        # Additional validation for playlist URLs
        if "playlist?list=" in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 'list' not in query_params or not query_params['list'][0]:
                return False, "Invalid playlist URL: missing playlist ID"
        
        # Additional validation for video URLs
        elif "watch?v=" in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 'v' not in query_params or not query_params['v'][0]:
                return False, "Invalid video URL: missing video ID"
        
        return True, ""
    
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
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """Validate Gemini API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key or not api_key.strip():
            return False, "Please enter your Gemini API key"
        
        api_key = api_key.strip()
        
        # Basic format validation for Google API keys
        if len(api_key) < 20:
            return False, "API key appears to be too short"
        
        # Check for common API key format patterns
        if not any(char.isalnum() for char in api_key):
            return False, "API key format appears invalid"
        
        return True, ""
    
    @staticmethod
    def validate_language(language: str) -> Tuple[bool, str]:
        """Validate output language.
        
        Args:
            language: Language to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not language or not language.strip():
            return False, "Please specify the output language"
        
        language = language.strip()
        
        # Basic validation - ensure it contains at least alphabetic characters
        if not any(char.isalpha() for char in language):
            return False, "Language must contain valid alphabetic characters"
        
        return True, ""
    
    @staticmethod
    def validate_chunk_size(chunk_size: int) -> Tuple[bool, str]:
        """Validate chunk size.
        
        Args:
            chunk_size: Chunk size to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(chunk_size, int):
            return False, "Chunk size must be a number"
        
        if chunk_size < 500:
            return False, "Chunk size must be at least 500 words"
        
        if chunk_size > 50000:
            return False, "Chunk size cannot exceed 50,000 words"
        
        return True, ""
    
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
            is_valid, error = InputValidator.validate_youtube_url(source_url)
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
        is_valid, error = InputValidator.validate_api_key(api_key)
        if not is_valid:
            return False, error
        
        # Validate language
        is_valid, error = InputValidator.validate_language(language)
        if not is_valid:
            return False, error
        
        # Validate chunk size
        is_valid, error = InputValidator.validate_chunk_size(chunk_size)
        if not is_valid:
            return False, error
        
        return True, ""


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
