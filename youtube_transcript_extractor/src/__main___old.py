"""
Enhanced YouTube Transcript Extractor with all Phase 2 improvements.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Ensure the youtube_transcript_extractor is in the path
current_dir = Path(__file__).parent
yte_path = current_dir / "youtube_transcript_extractor"
sys.path.insert(0, str(yte_path))

try:
    from youtube_transcript_extractor.src.utils.config import ConfigManager
    from youtube_transcript_extractor.src.utils.secure_config import SecureConfigManager
    from youtube_transcript_extractor.src.core.concurrent_processor import ConcurrentPlaylistProcessor
    from youtube_transcript_extractor.src.core.job_manager import JobManager, JobStatus
    from youtube_transcript_extractor.src.core.exporters import ExportManager
    from youtube_transcript_extractor.src.core.models import RefinementStyle
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r youtube_transcript_extractor/requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yte_enhanced.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class EnhancedYouTubeTranscriptExtractor:
    """Enhanced YouTube Transcript Extractor with all Phase 2 improvements."""
    
    def __init__(self):
        """Initialize the enhanced extractor."""
        self.config_manager = ConfigManager()
        self.secure_manager = SecureConfigManager()
        self.job_manager = JobManager()
        self.export_manager = ExportManager()
        
        # Check setup
        self._check_setup()
        
    def _check_setup(self) -> None:
        """Check if the application is properly set up."""
        logger.info("🔍 Checking application setup...")
        
        # Check API key
        api_key = self.config_manager.get_api_key()
        if not api_key:
            logger.warning("⚠️ No API key configured. Please run setup first.")
            self._prompt_api_key_setup()
        else:
            logger.info("✅ API key configured securely")
        
        # Check available export formats
        available_formats = self.export_manager.get_available_formats()
        logger.info(f"📄 Available export formats: {', '.join(available_formats)}")
        
        missing_deps = self.export_manager.get_missing_dependencies()
        if missing_deps:
            logger.info("ℹ️ Optional dependencies missing for:")
            for format_name, packages in missing_deps.items():
                logger.info(f"   {format_name}: {', '.join(packages)}")
        
        # Security status
        security_status = self.config_manager.get_security_status()
        if security_status.get('secure_storage_enabled'):
            logger.info("🔐 Secure storage enabled")
        else:
            logger.warning("⚠️ Secure storage not available - using fallback")
    
    def _prompt_api_key_setup(self) -> None:
        """Prompt user to set up API key."""
        print("\n🔑 API Key Setup Required")
        print("=" * 50)
        print("To use this application, you need a Google Gemini API key.")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        print()
        
        api_key = input("Enter your Gemini API key (will be stored securely): ").strip()
        if api_key and api_key != "":
            if self.secure_manager.store_api_key("gemini_api_key", api_key):
                print("✅ API key stored securely!")
                logger.info("API key configured successfully")
            else:
                print("❌ Failed to store API key securely")
                logger.error("Failed to store API key")
        else:
            print("❌ No API key provided")
            sys.exit(1)
    
    async def process_playlist(
        self,
        playlist_url: str,
        output_formats: Optional[List[str]] = None,
        max_workers: int = 5,
        refinement_style: RefinementStyle = RefinementStyle.BALANCED_DETAILED
    ) -> Dict[str, Any]:
        """Process a YouTube playlist with all enhancements.
        
        Args:
            playlist_url: YouTube playlist URL
            output_formats: List of output formats (default: ['markdown', 'html'])
            max_workers: Number of concurrent workers (default: 5)
            refinement_style: Processing style for content refinement
            
        Returns:
            Dictionary with processing results and statistics
        """
        if output_formats is None:
            output_formats = ['markdown', 'html']
        
        logger.info(f"🚀 Starting enhanced playlist processing")
        logger.info(f"📋 Playlist: {playlist_url}")
        logger.info(f"⚡ Workers: {max_workers}")
        logger.info(f"📄 Formats: {', '.join(output_formats)}")
        logger.info(f"🎨 Style: {refinement_style.value}")
        
        # Create job for persistence
        job_id = self.job_manager.create_job(
            source_type="playlist",
            source_url=playlist_url,
            source_title=f"Playlist processed on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            config_data={
                "formats": output_formats,
                "max_workers": max_workers,
                "refinement_style": refinement_style.value
            }
        )
        
        logger.info(f"📝 Created job: {job_id}")
        
        try:
            # Initialize concurrent processor
            processor = ConcurrentPlaylistProcessor(
                max_workers=max_workers,
                rate_limit=10.0  # Conservative rate limiting
            )
            
            # Progress tracking
            progress_data = {"completed": 0, "total": 0, "current": ""}
            
            def progress_callback(completed: int, total: int, current_task: Optional[str] = None):
                progress_data.update({
                    "completed": completed,
                    "total": total,
                    "current": current_task if current_task is not None else ""
                })
                percentage = (completed / total) * 100 if total > 0 else 0
                print(f"\r📊 Progress: {completed}/{total} ({percentage:.1f}%) - {current_task if current_task is not None else ''}", end="", flush=True)
            
            # Process playlist
            self.job_manager.update_job_status(job_id, JobStatus.PROCESSING)
            
            results = await processor.process_playlist(playlist_url, progress_callback)
            print()  # New line after progress
            
            # Combine successful results
            combined_content = self._combine_results(results)
            
            if not combined_content.strip():
                logger.error("❌ No content was successfully processed")
                self.job_manager.update_job_status(job_id, JobStatus.FAILED, "No content processed")
                return {"success": False, "error": "No content processed"}
            
            # Generate metadata
            metadata = self._generate_metadata(playlist_url, results, refinement_style)
            
            # Export to multiple formats
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            base_filename = f"playlist_{timestamp}"
            base_path = output_dir / base_filename
            
            logger.info(f"📄 Exporting to {len(output_formats)} formats...")
            
            export_results = self.export_manager.export_to_multiple_formats(
                content=combined_content,
                base_output_path=base_path,
                formats=output_formats,
                metadata=metadata
            )
            
            # Update job with results
            successful_exports = [fmt for fmt, success in export_results.items() if success]
            failed_exports = [fmt for fmt, success in export_results.items() if not success]
            
            if successful_exports:
                self.job_manager.update_job_status(job_id, JobStatus.COMPLETED)
                logger.info("🎉 Processing completed successfully!")
                
                # Display results
                print("\n" + "=" * 60)
                print("🎉 PROCESSING COMPLETED SUCCESSFULLY!")
                print("=" * 60)
                
                # Statistics
                successful_videos = sum(1 for r in results if r.success)
                total_videos = len(results)
                success_rate = (successful_videos / total_videos) * 100 if total_videos > 0 else 0
                
                print(f"📊 Statistics:")
                print(f"   • Total Videos: {total_videos}")
                print(f"   • Successful: {successful_videos}")
                print(f"   • Success Rate: {success_rate:.1f}%")
                print(f"   • Job ID: {job_id}")
                
                # Output files
                print(f"\n📄 Generated Files:")
                for format_name in successful_exports:
                    exporter = self.export_manager.exporters[format_name]
                    output_file = base_path.with_suffix(exporter.get_file_extension())
                    print(f"   ✅ {format_name.upper()}: {output_file}")
                
                if failed_exports:
                    print(f"\n⚠️ Failed Exports:")
                    for format_name in failed_exports:
                        print(f"   ❌ {format_name.upper()}")
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "statistics": {
                        "total_videos": total_videos,
                        "successful_videos": successful_videos,
                        "success_rate": success_rate
                    },
                    "exports": export_results,
                    "output_files": {
                        fmt: str(base_path.with_suffix(self.export_manager.exporters[fmt].get_file_extension()))
                        for fmt in successful_exports
                    }
                }
            else:
                self.job_manager.update_job_status(job_id, JobStatus.FAILED, "All exports failed")
                logger.error("❌ All export formats failed")
                return {"success": False, "error": "All exports failed"}
        
        except KeyboardInterrupt:
            logger.info("⚠️ Processing interrupted by user")
            self.job_manager.update_job_status(job_id, JobStatus.CANCELLED)
            return {"success": False, "error": "Interrupted by user"}
        
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            self.job_manager.update_job_status(job_id, JobStatus.FAILED, str(e))
            return {"success": False, "error": str(e)}
    
    def _combine_results(self, results) -> str:
        """Combine processing results into a single content string."""
        combined = []
        
        for result in results:
            if result.success and result.transcript_video:
                video = result.transcript_video
                combined.append(f"Video URL: {video.url}")
                if video.title:
                    combined.append(f"Title: {video.title}")
                combined.append("")
                combined.append(video.content)
                combined.append("")
                combined.append("-" * 80)
                combined.append("")
        
        return "\n".join(combined)
    
    def _generate_metadata(self, playlist_url: str, results, refinement_style: RefinementStyle) -> Dict[str, Any]:
        """Generate metadata for exports."""
        successful_videos = sum(1 for r in results if r.success)
        total_videos = len(results)
        
        return {
            "source_url": playlist_url,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_videos": total_videos,
            "successful_videos": successful_videos,
            "success_rate": f"{(successful_videos/total_videos)*100:.1f}%" if total_videos > 0 else "0%",
            "processing_style": refinement_style.value,
            "generator": "Enhanced YouTube Transcript Extractor v2.0"
        }
    
    def list_resumable_jobs(self) -> None:
        """List jobs that can be resumed."""
        jobs = self.job_manager.get_resumable_jobs()
        
        if not jobs:
            print("📋 No resumable jobs found.")
            return
        
        print("\n📋 RESUMABLE JOBS")
        print("=" * 50)
        
        for job in jobs:
            print(f"🆔 Job ID: {job['id'][:8]}...")
            print(f"📺 Source: {job['source_url']}")
            print(f"📅 Updated: {job['updated_at']}")
            print(f"📊 Progress: {job['completed_items']}/{job['total_items']}")
            print(f"🔄 Status: {job['status']}")
            print("-" * 30)
    
    async def resume_job(self, job_id: str) -> Dict[str, Any]:
        """Resume a previously interrupted job."""
        logger.info(f"🔄 Attempting to resume job: {job_id}")
        
        resume_data = self.job_manager.resume_job(job_id)
        
        if "error" in resume_data:
            logger.error(f"❌ Cannot resume job: {resume_data['error']}")
            return {"success": False, "error": resume_data["error"]}
        
        if not resume_data["can_resume"]:
            logger.info("✅ Job already completed")
            return {"success": True, "message": "Job already completed"}
        
        job_data = resume_data["job"]
        remaining_items = resume_data["remaining_items"]
        
        logger.info(f"📋 Resuming job with {len(remaining_items)} remaining items")
        
        # Continue processing with remaining items
        # Implementation would depend on the specific job type
        # For now, return the resume data
        
        return {
            "success": True,
            "job_data": job_data,
            "remaining_items": len(remaining_items),
            "completed_items": resume_data["completed_count"]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall application statistics."""
        return self.job_manager.get_job_statistics()
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up old completed jobs."""
        return self.job_manager.cleanup_old_jobs(days)


async def main():
    """Main application entry point."""
    print("🚀 Enhanced YouTube Transcript Extractor v2.0")
    print("=" * 60)
    
    try:
        extractor = EnhancedYouTubeTranscriptExtractor()
        
        # Example usage - replace with your playlist URL
        playlist_url = input("\n📺 Enter YouTube playlist URL: ").strip()
        
        if not playlist_url:
            print("❌ No URL provided")
            return
        
        # Choose export formats
        available_formats = extractor.export_manager.get_available_formats()
        print(f"\n📄 Available formats: {', '.join(available_formats)}")
        
        format_input = input("Enter formats (comma-separated, or press Enter for markdown,html): ").strip()
        if format_input:
            export_formats = [f.strip() for f in format_input.split(",")]
        else:
            export_formats = ["markdown", "html"]
        
        # Process the playlist
        result = await extractor.process_playlist(
            playlist_url=playlist_url,
            output_formats=export_formats,
            max_workers=5
        )
        
        if result["success"]:
            print(f"\n🎉 Success! Files generated in outputs/ directory")
        else:
            print(f"\n❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        logger.exception("Application error")


if __name__ == "__main__":
    asyncio.run(main())
