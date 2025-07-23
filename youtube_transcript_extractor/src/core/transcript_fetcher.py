"""
Transcript fetching service for YouTube videos and local files.
"""

import os
import glob
import time
import random
import logging
from typing import List, Optional, Callable, Protocol, Dict, Any
from pytube import Playlist
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound

from .models import TranscriptVideo, ProcessingProgress, ProcessingResult, ProcessingMode
from .protocols import ProgressCallback, StatusCallback


class TranscriptFetcher:
    """Service for fetching transcripts from various sources."""
    
    def __init__(self, config=None, progress_callback: Optional[ProgressCallback] = None):
        """Initialize the transcript fetcher.
        
        Args:
            config: Optional processing configuration
            progress_callback: Optional progress callback function
        """
        self.config = config
        self.progress_callback = progress_callback
        self.is_cancelled = False
        self.logger = logging.getLogger(__name__)
    
    def cancel(self) -> None:
        """Cancel the current operation."""
        self.is_cancelled = True
    
    def fetch_from_youtube(self, url: str, output_file: str,
                          progress_callback: Optional[ProgressCallback] = None,
                          status_callback: Optional[StatusCallback] = None) -> ProcessingResult:
        """Fetch transcripts from YouTube URL.
        
        Args:
            url: YouTube playlist or video URL
            output_file: Output file path for transcripts
            progress_callback: Optional callback for progress updates
            status_callback: Optional callback for status messages
            
        Returns:
            ProcessingResult with operation outcome
        """
        try:
            self.is_cancelled = False
            
            if status_callback:
                status_callback("Using direct connection for transcript access...")
            
            # Initialize YouTube Transcript API
            ytt_api = YouTubeTranscriptApi()
            
            # Determine if it's a playlist or single video
            if "playlist?list=" in url:
                playlist = Playlist(url)
                video_urls = playlist.video_urls
                total_videos = len(video_urls)
                playlist_name = playlist.title
                
                if status_callback:
                    status_callback(f"Found playlist: {playlist_name} with {total_videos} videos")
            elif "watch?v=" in url:
                video_urls = [url]
                total_videos = 1
                playlist_name = "Single Video"
                
                if status_callback:
                    status_callback("Processing single video")
            else:
                return ProcessingResult(
                    success=False,
                    error_message="Invalid URL provided. Please use a valid YouTube video or playlist URL."
                )
            
            # Process videos and write transcripts
            videos_processed = 0
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Playlist Name: {playlist_name}\n\n")
                
                for index, video_url in enumerate(video_urls, 1):
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
                            current_item=index,
                            total_items=total_videos,
                            current_operation="Extracting transcript",
                            percentage=int((index / total_videos) * 100),
                            message=f"Processing video {index}/{total_videos}"
                        )
                        progress_callback(progress)
                    
                    # Extract transcript for this video
                    video_result = self._extract_single_video_transcript(
                        video_url, index, total_videos, ytt_api, status_callback
                    )
                    
                    if video_result.success:
                        f.write(f"Video URL: {video_url}\n")
                        f.write(video_result.content + '\n\n')
                        videos_processed += 1
                        
                        if status_callback:
                            status_callback(f"✅ Extracted transcript for video {index}/{total_videos}")
                    else:
                        if status_callback:
                            status_callback(f"⚠️ {video_result.error_message}")
                    
                    # Add delay between videos to avoid rate limiting
                    if index < total_videos:
                        time.sleep(random.uniform(1, 2))
            
            return ProcessingResult(
                success=True,
                output_file=output_file,
                videos_processed=videos_processed,
                total_videos=total_videos
            )
            
        except Exception as e:
            error_message = f"Extraction error: {str(e)}"
            self.logger.error(error_message)
            return ProcessingResult(
                success=False,
                error_message=error_message
            )
    
    def fetch_from_local_folder(self, folder_path: str, output_file: str,
                               progress_callback: Optional[ProgressCallback] = None,
                               status_callback: Optional[StatusCallback] = None) -> ProcessingResult:
        """Fetch transcripts from local folder.
        
        Args:
            folder_path: Path to folder containing transcript files
            output_file: Output file path for combined transcripts
            progress_callback: Optional callback for progress updates
            status_callback: Optional callback for status messages
            
        Returns:
            ProcessingResult with operation outcome
        """
        try:
            self.is_cancelled = False
            
            # Find all .txt files in the folder
            txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
            
            if not txt_files:
                return ProcessingResult(
                    success=False,
                    error_message=f"No .txt files found in the selected folder: {folder_path}"
                )
            
            if status_callback:
                status_callback(f"Found {len(txt_files)} transcript files in folder")
                status_callback(f"Folder: {folder_path}")
            
            total_files = len(txt_files)
            files_processed = 0
            
            # Create combined transcript file
            with open(output_file, 'w', encoding='utf-8') as combined_file:
                combined_file.write(f"Local Transcript Files from: {folder_path}\n\n")
                
                for i, file_path in enumerate(txt_files, 1):
                    if self.is_cancelled:
                        if status_callback:
                            status_callback("Operation cancelled by user")
                        return ProcessingResult(
                            success=False,
                            error_message="Operation cancelled by user",
                            videos_processed=files_processed,
                            total_videos=total_files
                        )
                    
                    filename = os.path.basename(file_path)
                    
                    # Update progress
                    if progress_callback:
                        progress = ProcessingProgress(
                            current_item=i,
                            total_items=total_files,
                            current_operation="Processing file",
                            percentage=int((i / total_files) * 100),
                            message=f"Processing file {i}/{total_files}: {filename}"
                        )
                        progress_callback(progress)
                    
                    try:
                        if status_callback:
                            status_callback(f"Processing file {i}/{total_files}: {filename}")
                        
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        # Write in the same format as YouTube transcripts
                        combined_file.write(f"Video URL: Local File - {filename}\n")
                        combined_file.write(content + '\n\n')
                        
                        files_processed += 1
                        
                    except Exception as file_error:
                        if status_callback:
                            status_callback(f"⚠️ Error reading {filename}: {str(file_error)}")
                        continue
            
            if status_callback:
                status_callback(f"✅ Successfully combined {files_processed} files into {output_file}")
            
            return ProcessingResult(
                success=True,
                output_file=output_file,
                videos_processed=files_processed,
                total_videos=total_files
            )
            
        except Exception as e:
            error_message = f"Error processing local transcripts: {str(e)}"
            self.logger.error(error_message)
            return ProcessingResult(
                success=False,
                error_message=error_message
            )
    
    def _extract_single_video_transcript(self, video_url: str, index: int, total: int,
                                       ytt_api: YouTubeTranscriptApi,
                                       status_callback: Optional[StatusCallback] = None) -> TranscriptVideo:
        """Extract transcript from a single video.
        
        Args:
            video_url: YouTube video URL
            index: Current video index
            total: Total number of videos
            ytt_api: YouTube Transcript API instance
            status_callback: Optional callback for status messages
            
        Returns:
            TranscriptVideo with extraction result
        """
        try:
            video_id = video_url.split("?v=")[1].split("&")[0]
            fetched_transcript = None
            
            # Enhanced transcript extraction with retry logic
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        if status_callback:
                            status_callback(f"Retry attempt {attempt + 1}/{max_retries} for video {index}/{total}")
                        time.sleep(retry_delay + random.uniform(1, 3))
                    
                    # Get the list of all available transcripts
                    transcript_list_obj = ytt_api.list(video_id)
                    
                    # Try to find and fetch English first
                    try:
                        transcript_object = transcript_list_obj.find_transcript(['en'])
                        if status_callback:
                            status_callback(f"Found English transcript for video {index}/{total}. Fetching...")
                        fetched_transcript = transcript_object.fetch()
                        break  # Success, exit retry loop
                    
                    # If English is not found, fallback to the first available transcript
                    except NoTranscriptFound:
                        if status_callback:
                            status_callback(f"English not found for video {index}/{total}. Trying fallback...")
                        # Get the first transcript object from the list
                        first_transcript_object = next(iter(transcript_list_obj))
                        if status_callback:
                            status_callback(f"Found fallback: '{first_transcript_object.language}'. Fetching...")
                        fetched_transcript = first_transcript_object.fetch()
                        break  # Success, exit retry loop
                
                except Exception as fetch_error:
                    error_msg = str(fetch_error)
                    if "blocking requests" in error_msg or "IP" in error_msg:
                        if attempt < max_retries - 1:
                            if status_callback:
                                status_callback(f"IP blocked for video {index}/{total}, waiting before retry...")
                            time.sleep(retry_delay * (attempt + 2))  # Exponential backoff
                            continue
                        else:
                            if status_callback:
                                status_callback(f"Failed after {max_retries} attempts for video {index}/{total}: IP blocked")
                            return TranscriptVideo(
                                url=video_url,
                                title=None,
                                content="",
                                success=False,
                                error_message=f"Failed after {max_retries} attempts: IP blocked"
                            )
                    else:
                        # Other error, don't retry
                        raise fetch_error
            
            # Process the transcript if we got one
            if fetched_transcript:
                transcript_text = ' '.join([segment.text for segment in fetched_transcript])
                return TranscriptVideo(
                    url=video_url,
                    title=None,
                    content=transcript_text,
                    success=True
                )
            else:
                return TranscriptVideo(
                    url=video_url,
                    title=None,
                    content="",
                    success=False,
                    error_message=f"Could not extract transcript for video {index}/{total}"
                )
        
        except NoTranscriptFound:
            return TranscriptVideo(
                url=video_url,
                title=None,
                content="",
                success=False,
                error_message=f"No transcripts available for video {index}/{total}"
            )
        
        except Exception as video_error:
            error_msg = str(video_error)
            if "blocking requests" in error_msg:
                if status_callback:
                    status_callback(f"🚫 IP blocked for video {index}/{total} - Consider waiting longer between batches")
                
                # If we're getting blocked after processing several videos, suggest stopping
                if "blocking requests" in error_msg and index > 5:
                    if status_callback:
                        status_callback("⚠️ Multiple IP blocks detected. Consider stopping and waiting 30+ minutes before continuing.")
                        status_callback("💡 Tip: Process videos in smaller batches (10-20 at a time) with longer delays between batches.")
            
            return TranscriptVideo(
                url=video_url,
                title=None,
                content="",
                success=False,
                error_message=f"Error processing {video_url}: {error_msg}"
            )

    # Additional methods expected by tests
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        if not url:
            return None
            
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(url)
        if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            if parsed.path == '/watch':
                query_params = parse_qs(parsed.query)
                return query_params.get('v', [None])[0]
        elif parsed.hostname == 'youtu.be':
            return parsed.path[1:]  # Remove leading slash
            
        return None

    def _extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from YouTube URL."""
        if not url:
            return None
            
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(url)
        if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            if 'list=' in url:
                query_params = parse_qs(parsed.query)
                return query_params.get('list', [None])[0]
                
        return None

    def fetch_single_video(self, video_url: str, progress_callback: Optional[ProgressCallback] = None,
                          status_callback: Optional[StatusCallback] = None) -> ProcessingResult:
        """Fetch transcript from a single video."""
        try:
            if status_callback:
                status_callback(f"Fetching transcript from single video: {video_url}")
                
            ytt_api = YouTubeTranscriptApi()
            
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return ProcessingResult(
                    success=False,
                    error_message="Could not extract video ID from URL"
                )
            
            # Fetch transcript
            transcript_data = ytt_api.get_transcript(video_id)
            
            # Format transcript content
            content = self._format_transcript_content(transcript_data)
            
            if status_callback:
                status_callback("✅ Single video transcript fetched successfully")
                
            return ProcessingResult(
                success=True,
                output_file="",  # Single video doesn't need output file
                videos_processed=1,
                total_videos=1
            )
            
        except Exception as e:
            error_msg = f"Failed to fetch single video transcript: {str(e)}"
            self.logger.error(error_msg)
            return ProcessingResult(
                success=False,
                error_message=error_msg
            )

    def fetch_playlist_videos(self, playlist_url: str, progress_callback: Optional[ProgressCallback] = None,
                             status_callback: Optional[StatusCallback] = None) -> ProcessingResult:
        """Fetch video URLs from a playlist."""
        try:
            if status_callback:
                status_callback(f"Fetching videos from playlist: {playlist_url}")
                
            playlist = Playlist(playlist_url)
            video_urls = list(playlist.video_urls)
            
            if status_callback:
                status_callback(f"Found {len(video_urls)} videos in playlist")
                
            return ProcessingResult(
                success=True,
                output_file="",  # Playlist videos doesn't need output file
                videos_processed=len(video_urls),
                total_videos=len(video_urls)
            )
            
        except Exception as e:
            error_msg = f"Failed to fetch playlist videos: {str(e)}"
            self.logger.error(error_msg)
            return ProcessingResult(
                success=False,
                error_message=error_msg
            )

    def _format_transcript_content(self, transcript_data: List[Dict[str, Any]]) -> str:
        """Format transcript data into readable content."""
        if not transcript_data:
            return ""
            
        formatted_lines = []
        for entry in transcript_data:
            text = entry.get('text', '').strip()
            if text:
                # Optional: include timestamps
                if 'start' in entry:
                    timestamp = int(entry['start'])
                    minutes = timestamp // 60
                    seconds = timestamp % 60
                    formatted_lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")
                else:
                    formatted_lines.append(text)
        
        return '\n'.join(formatted_lines)
