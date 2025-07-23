"""
Gemini AI processing service for refining transcripts.
"""

import os
import re
import time
import logging
from typing import List, Optional, Callable, Protocol

# Use centralized dependency management
import sys
from pathlib import Path
current_dir = Path(__file__).parent.parent  # Go up to src directory
sys.path.insert(0, str(current_dir))

from utils.dependencies import safe_import, require_dependency

# Import required dependency using the centralized system
genai, GENAI_AVAILABLE = safe_import("google.generativeai", "google-generativeai")

from .models import ProcessingProgress, ProcessingResult, RefinementStyle, ProcessingPrompts
from .protocols import ProgressCallback, StatusCallback


class GeminiProcessor:
    """Service for processing transcripts using Google's Gemini AI."""
    
    DEFAULT_CHUNK_SIZE = 3000
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """Initialize the Gemini processor.
        
        Args:
            api_key: Google Gemini API key
            model_name: Name of the Gemini model to use
            
        Raises:
            ImportError: If google.generativeai is not installed
            ValueError: If API key is invalid
        """
        if not GENAI_AVAILABLE:
            raise ImportError("google.generativeai package is required but not installed")
        
        if not api_key or not api_key.strip():
            raise ValueError("API key is required")
        
        self.api_key = api_key.strip()
        self.model_name = model_name
        self.is_cancelled = False
        self.logger = logging.getLogger(__name__)
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)  # type: ignore
        
        # Set up logging
        logging.basicConfig(
            filename='gemini_processing.log', 
            level=logging.ERROR, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def cancel(self) -> None:
        """Cancel the current operation."""
        self.is_cancelled = True
    
    def process_transcripts(self, input_file: str, output_file: str,
                          output_language: str, refinement_style: RefinementStyle,
                          chunk_size: int = DEFAULT_CHUNK_SIZE,
                          progress_callback: Optional[ProgressCallback] = None,
                          status_callback: Optional[StatusCallback] = None) -> ProcessingResult:
        """Process transcripts using Gemini AI.
        
        Args:
            input_file: Path to the input transcript file
            output_file: Path to the output file
            output_language: Target language for output
            refinement_style: Style of refinement to apply
            chunk_size: Size of text chunks for processing
            progress_callback: Optional callback for progress updates
            status_callback: Optional callback for status messages
            
        Returns:
            ProcessingResult with operation outcome
        """
        try:
            self.is_cancelled = False
            
            if status_callback:
                status_callback("Starting Gemini AI processing...")
            
            # Split the input file into video chunks
            video_chunks = self._split_videos(input_file)
            
            if not video_chunks:
                return ProcessingResult(
                    success=False,
                    error_message="No content found in the input file"
                )
            
            # Skip the first chunk if it's empty (header)
            video_chunks_to_process = video_chunks[1:] if len(video_chunks) > 1 else video_chunks
            total_videos = len(video_chunks_to_process)
            
            if status_callback:
                status_callback(f"Found {total_videos} video(s) to process")
            
            # Get the prompt for the selected refinement style
            prompt_template = ProcessingPrompts.get_prompt(refinement_style)
            
            # Create response file paths
            response_file_path = output_file.replace(".txt", "_temp_response.txt")
            
            # Initialize the output file
            with open(output_file, "w", encoding="utf-8") as final_output_file:
                final_output_file.write("")
            
            # Process each video
            videos_processed = 0
            
            for video_index, video_chunk in enumerate(video_chunks_to_process):
                if self.is_cancelled:
                    if status_callback:
                        status_callback("Operation cancelled by user")
                    return ProcessingResult(
                        success=False,
                        error_message="Operation cancelled by user",
                        videos_processed=videos_processed,
                        total_videos=total_videos
                    )
                
                # Update progress
                if progress_callback:
                    progress = ProcessingProgress(
                        current_item=video_index + 1,
                        total_items=total_videos,
                        current_operation="Processing with Gemini AI",
                        percentage=int(((video_index + 1) / total_videos) * 100),
                        message=f"Processing video {video_index + 1}/{total_videos}"
                    )
                    progress_callback(progress)
                
                if status_callback:
                    preview = video_chunk[:50].replace('\n', ' ')
                    status_callback(f"Processing Video {video_index + 1}/{total_videos}: {preview}...")
                    
                    word_count = len(video_chunk.split())
                    status_callback(f"Word Count: {word_count} words")
                    status_callback(f"Chunk Size: {chunk_size} words")
                
                # Process this video
                result = self._process_single_video(
                    video_chunk, prompt_template, output_language, chunk_size,
                    video_index + 1, total_videos, response_file_path, output_file,
                    status_callback
                )
                
                if result.success:
                    videos_processed += 1
                    if status_callback:
                        status_callback(f"✅ Video {video_index + 1} processed successfully")
                else:
                    if status_callback:
                        status_callback(f"⚠️ Error processing video {video_index + 1}: {result.error_message}")
            
            # Clean up temporary file
            if os.path.exists(response_file_path):
                try:
                    os.remove(response_file_path)
                except OSError:
                    pass  # Ignore cleanup errors
            
            if status_callback:
                status_callback(f"✅ Processing complete! {videos_processed}/{total_videos} videos processed successfully")
            
            return ProcessingResult(
                success=True,
                output_file=output_file,
                videos_processed=videos_processed,
                total_videos=total_videos
            )
            
        except Exception as e:
            error_message = f"Gemini processing error: {str(e)}"
            self.logger.error(error_message)
            return ProcessingResult(
                success=False,
                error_message=error_message
            )
    
    def _process_single_video(self, video_chunk: str, prompt_template: str,
                            output_language: str, chunk_size: int,
                            video_number: int, total_videos: int,
                            response_file_path: str, final_output_path: str,
                            status_callback: Optional[StatusCallback] = None) -> ProcessingResult:
        """Process a single video's transcript.
        
        Args:
            video_chunk: The video transcript content
            prompt_template: The prompt template to use
            output_language: Target output language
            chunk_size: Size of text chunks
            video_number: Current video number
            total_videos: Total number of videos
            response_file_path: Path for temporary responses
            final_output_path: Path for final output
            status_callback: Optional callback for status messages
            
        Returns:
            ProcessingResult for this video
        """
        try:
            # Clear the temporary response file
            with open(response_file_path, "w", encoding="utf-8") as response_file:
                response_file.write("")
            
            # Split the video transcript into chunks
            video_transcript_chunks = self._split_text_into_chunks(video_chunk, chunk_size)
            
            if status_callback:
                status_callback(f"Video split into {len(video_transcript_chunks)} chunks")
            
            # Process each chunk
            previous_response = ""
            
            for chunk_index, chunk in enumerate(video_transcript_chunks):
                if self.is_cancelled:
                    return ProcessingResult(
                        success=False,
                        error_message="Operation cancelled by user"
                    )
                
                # Build the prompt
                if previous_response:
                    context_prompt = (
                        "The following text is a continuation... "
                        f"Previous response:\n{previous_response}\n\nNew text to process (Do Not Repeat the Previous response):\n"
                    )
                else:
                    context_prompt = ""
                
                # Replace [Language] placeholder with actual language
                formatted_prompt = prompt_template.replace("[Language]", output_language)
                full_prompt = f"{context_prompt}{formatted_prompt}\n\n{chunk}"
                
                # Generate response using Gemini
                if status_callback:
                    status_callback(f"Generating Gemini response for Video {video_number}/{total_videos}, Chunk {chunk_index + 1}/{len(video_transcript_chunks)}")
                
                try:
                    model = genai.GenerativeModel(model_name=self.model_name)  # type: ignore
                    response = model.generate_content(full_prompt)  # type: ignore
                    
                    if not response.text:
                        raise ValueError("Empty response from Gemini")
                    
                    # Save the response to temporary file
                    with open(response_file_path, "a", encoding="utf-8") as response_file:
                        response_file.write(response.text + "\n\n")
                    
                    previous_response = response.text
                    
                    if status_callback:
                        status_callback(f"✅ Chunk {chunk_index + 1}/{len(video_transcript_chunks)} processed")
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as api_error:
                    error_msg = f"Gemini API error for chunk {chunk_index + 1}: {str(api_error)}"
                    self.logger.error(error_msg)
                    if status_callback:
                        status_callback(f"⚠️ {error_msg}")
                    
                    # Continue with the next chunk rather than failing completely
                    continue
            
            # Read the complete video response and append to final output
            try:
                with open(response_file_path, "r", encoding="utf-8") as response_file:
                    video_response_content = response_file.read()
                
                with open(final_output_path, "a", encoding="utf-8") as final_output_file:
                    # Extract video URL from the chunk (first line)
                    video_lines = video_chunk.splitlines()
                    video_url_line = ""
                    for line in video_lines:
                        if line.startswith("Video URL:"):
                            video_url_line = line
                            break
                    
                    if video_url_line:
                        final_output_file.write(f"{video_url_line}\n")
                    
                    final_output_file.write(video_response_content + "\n\n")
                
                if status_callback:
                    status_callback(f"Final output for video {video_number} appended to {final_output_path}")
                
                return ProcessingResult(success=True)
                
            except Exception as file_error:
                error_msg = f"Error writing final output for video {video_number}: {str(file_error)}"
                self.logger.error(error_msg)
                return ProcessingResult(
                    success=False,
                    error_message=error_msg
                )
            
        except Exception as e:
            error_msg = f"Error processing video {video_number}: {str(e)}"
            self.logger.error(error_msg)
            return ProcessingResult(
                success=False,
                error_message=error_msg
            )
    
    def _split_text_into_chunks(self, text: str, chunk_size: int, min_chunk_size: int = 500) -> List[str]:
        """Split text into chunks of specified size.
        
        Args:
            text: Text to split
            chunk_size: Maximum size of each chunk in words
            min_chunk_size: Minimum size for the last chunk
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        # Merge small last chunk with previous chunk
        if len(chunks) > 1 and len(chunks[-1].split()) < min_chunk_size:
            chunks[-2] += " " + chunks[-1]
            chunks.pop()
        
        return chunks
    
    def _split_videos(self, file_path: str) -> List[str]:
        """Split the transcript file into individual video chunks.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            List of video transcript chunks
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Split by "Video URL:" marker
            video_chunks = re.split(r'(?=Video URL:)', content)
            video_chunks = [chunk.strip() for chunk in video_chunks if chunk.strip()]
            
            return video_chunks
            
        except Exception as e:
            self.logger.error(f"Error splitting video file {file_path}: {str(e)}")
            return []


class GeminiModelValidator:
    """Validates Gemini model availability and settings."""
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate Gemini API key by making a test call.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not api_key or not api_key.strip():
            return False
        
        try:
            if not GENAI_AVAILABLE:
                return False
            
            genai.configure(api_key=api_key.strip())  # type: ignore
            
            # Try to list models as a validation test
            models = genai.list_models()  # type: ignore
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available Gemini models.
        
        Returns:
            List of model names
        """
        try:
            if not GENAI_AVAILABLE:
                return []
            
            models = genai.list_models()  # type: ignore
            return [model.name for model in models if 'generateContent' in model.supported_generation_methods]  # type: ignore
            
        except Exception:
            # Return default list if API call fails
            from .models import GeminiModels
            return GeminiModels.get_models()
