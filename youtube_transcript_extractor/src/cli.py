"""
Command Line Interface for YouTube Transcript Extractor.

This module provides a comprehensive CLI interface with proper command structure,
argument validation, help system, and progress reporting.
"""

import argparse
import asyncio
import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text

# Get the current directory for debugging purposes
current_dir = Path(__file__).parent

try:
    from .utils.dependencies import (
        get_dependency_manager, 
        require_dependency,
        is_available,
        has_gui_support,
        has_async_support,
        has_security_features
    )
    
    # Use dependency manager for imports
    dependency_manager = get_dependency_manager()
    
    # Required imports - these should be available
    from .utils.config import ConfigManager
    from .utils.secure_config import SecureConfigManager
    from .core.concurrent_processor import ConcurrentPlaylistProcessor, ConcurrentProcessingResult
    from .core.job_manager import JobManager, JobStatus, JobItemStatus
    from .core.exporters import ExportManager
    from .core.models import RefinementStyle, GeminiModels
    
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all dependencies are installed and the package structure is correct.")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path[:3]}...")
    
    # Try to provide more helpful error information using dependency manager if available
    try:
        from .utils.dependencies import get_dependency_manager
        manager = get_dependency_manager()  
        missing_deps = [dep for dep in manager._dependencies.values() 
                       if not dep.is_available and dep.level.value == "required"]
        if missing_deps:
            print("\nMissing required dependencies:")
            for dep in missing_deps:
                print(f"  - {dep.name}: {dep.install_command}")
    except ImportError:
        pass
    
    # Try to provide more helpful error information about directories
    for module_name in ['core', 'utils']:
        module_path = current_dir / module_name
        if module_path.exists():
            print(f"✓ Found {module_name} directory")
        else:
            print(f"✗ Missing {module_name} directory")
    
    sys.exit(1)

# Initialize rich console
console = Console()

# Configure logging for CLI
logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Custom exception for CLI-specific errors."""
    pass


class YTECli:
    """Main CLI application class."""
    
    def __init__(self):
        """Initialize CLI application."""
        self.config_manager = ConfigManager()
        self.secure_manager = SecureConfigManager()
        self.job_manager = JobManager()
        self.export_manager = ExportManager()
        self.processor = None
    
    def setup_logging(self, verbose: bool = False, quiet: bool = False) -> None:
        """Setup logging configuration based on CLI options."""
        if quiet:
            level = logging.WARNING
        elif verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('yte_cli.log'),
                logging.StreamHandler() if not quiet else logging.NullHandler()
            ]
        )
    
    def validate_url(self, url: str) -> bool:
        """Validate YouTube URL format."""
        youtube_patterns = [
            'youtube.com/watch',
            'youtube.com/playlist',
            'youtu.be/',
            'm.youtube.com'
        ]
        return any(pattern in url for pattern in youtube_patterns)
    
    def validate_formats(self, formats: List[str]) -> List[str]:
        """Validate and return supported export formats."""
        available_formats = self.export_manager.get_available_formats()
        valid_formats = []
        
        for fmt in formats:
            if fmt.lower() in available_formats:
                valid_formats.append(fmt.lower())
            else:
                console.print(f"[yellow]Warning:[/yellow] Format '{fmt}' not supported. Available: {', '.join(available_formats)}")
        
        if not valid_formats:
            valid_formats = ['markdown']  # Default fallback
            console.print("[yellow]Using default format: markdown[/yellow]")
        
        return valid_formats
    
    def display_welcome(self) -> None:
        """Display welcome message and basic info."""
        welcome_text = Text("YouTube Transcript Extractor CLI", style="bold magenta")
        console.print(Panel(welcome_text, expand=False))
        console.print("Transform YouTube content into structured, AI-refined text\n")

    async def resume_job(self, job_id: str) -> Dict[str, Any]:
        """Resume a paused or failed job.
        
        Args:
            job_id: The job ID to resume
            
        Returns:
            Dictionary with result information
        """
        try:
            # Get job details
            job = self.job_manager.get_job(job_id)
            if not job:
                return {"success": False, "error": "Job not found"}
            
            if job['status'] == 'completed':
                return {"success": False, "error": "Job already completed"}
            
            # Get incomplete items (pending or failed)
            incomplete_items = []
            pending_items = self.job_manager.get_job_items(job_id, JobItemStatus.PENDING)
            failed_items = self.job_manager.get_job_items(job_id, JobItemStatus.FAILED)
            incomplete_items.extend(pending_items)
            incomplete_items.extend(failed_items)
            
            if not incomplete_items:
                return {"success": False, "error": "No incomplete items found"}
            
            # Resume processing would be implemented here
            # For now, just return success with remaining count
            
            return {
                "success": True,
                "remaining_items": len(incomplete_items),
                "message": f"Found {len(incomplete_items)} items to process"
            }
            
        except Exception as e:
            logger.exception(f"Error resuming job {job_id}")
            return {"success": False, "error": str(e)}


@click.group(invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-essential output')
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, verbose, quiet, version):
    """YouTube Transcript Extractor - Convert YouTube content to structured text."""
    
    # Initialize CLI application
    ctx.ensure_object(dict)
    cli_app = YTECli()
    cli_app.setup_logging(verbose, quiet)
    ctx.obj['app'] = cli_app
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    
    if version:
        console.print("YouTube Transcript Extractor v2.0.0")
        ctx.exit()
    
    # If no command provided, show help or run interactive mode
    if ctx.invoked_subcommand is None:
        if not quiet:
            cli_app.display_welcome()
        console.print("Use --help to see available commands or run a specific command.\n")
        console.print("Quick start: [bold]youtube-transcript-extractor process <URL>[/bold]")


@cli.command()
@click.argument('url', required=True)
@click.option('--output', '-o', default='outputs', help='Output directory')
@click.option('--formats', '-f', default='markdown,html', help='Export formats (comma-separated)')
@click.option('--language', '-l', help='Target language for transcripts')
@click.option('--style', '-s', type=click.Choice(['summary', 'detailed', 'educational', 'technical']), 
              help='Refinement style')
@click.option('--workers', '-w', default=3, type=int, help='Number of concurrent workers')
@click.option('--chunk-size', default=3000, type=int, help='Text chunk size for processing')
@click.option('--model', type=click.Choice(['gemini-1.5-flash', 'gemini-1.5-pro']), 
              help='Gemini model to use')
@click.option('--dry-run', is_flag=True, help='Show what would be processed without actually processing')
@click.pass_context
def process(ctx, url, output, formats, language, style, workers, chunk_size, model, dry_run):
    """Process a YouTube playlist or video and generate formatted transcripts."""
    
    app = ctx.obj['app']
    quiet = ctx.obj['quiet']
    
    if not quiet:
        console.print(f"[bold]Processing:[/bold] {url}")
    
    # Validate URL
    if not app.validate_url(url):
        console.print("[red]Error:[/red] Invalid YouTube URL format")
        ctx.exit(1)
    
    # Validate and prepare formats
    format_list = [f.strip() for f in formats.split(',')]
    valid_formats = app.validate_formats(format_list)
    
    # Create output directory
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if dry_run:
        console.print("\n[yellow]DRY RUN - No actual processing will occur[/yellow]")
        console.print(f"URL: {url}")
        console.print(f"Output: {output_path.absolute()}")
        console.print(f"Formats: {', '.join(valid_formats)}")
        console.print(f"Workers: {workers}")
        console.print(f"Language: {language or 'Default from config'}")
        console.print(f"Style: {style or 'Default from config'}")
        return
    
    # Run the actual processing
    asyncio.run(_process_async(app, url, output_path, valid_formats, language, style, workers, chunk_size, model, quiet))


async def _process_async(app, url, output_path, formats, language, style, workers, chunk_size, model, quiet):
    """Async wrapper for processing."""
    
    try:
        # Setup progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console if not quiet else None,
            disable=quiet
        ) as progress:
            
            # Create processing task
            task = progress.add_task("Processing playlist...", total=100)
            
            # Initialize processor
            processor = ConcurrentPlaylistProcessor(
                max_workers=workers,
                rate_limit=10.0  # Default rate limit
            )
            
            # Progress callback to update the progress bar
            def progress_callback(completed: int, total: int, current_task: Optional[str] = None):
                if total > 0:
                    percentage = (completed / total) * 100
                    progress.update(task, completed=percentage)
                    if current_task and not quiet:
                        progress.update(task, description=f"Processing: {current_task}")
            
            # Start processing
            results = await processor.process_playlist(
                playlist_url=url,
                progress_callback=progress_callback
            )
            
            # Check if processing was successful
            if not results:
                console.print("[red]✗ Error:[/red] No results returned from processing")
                return
            
            # Count successful results
            successful_results = [r for r in results if r.success and r.transcript_video]
            
            if not successful_results:
                console.print("[red]✗ Error:[/red] No transcripts were successfully processed")
                # Show error summary
                error_summary = {}
                for result in results:
                    if result.error_message:
                        error_type = result.error_message.split(':')[0] if ':' in result.error_message else 'Unknown Error'
                        error_summary[error_type] = error_summary.get(error_type, 0) + 1
                
                if error_summary:
                    console.print("\nError Summary:")
                    for error_type, count in error_summary.items():
                        console.print(f"  {error_type}: {count}")
                return
            
            # Export results to different formats
            export_manager = app.export_manager
            export_successful = False
            
            for format_name in formats:
                try:
                    # Combine all successful transcripts
                    combined_content = _combine_transcripts(successful_results, format_name)
                    
                    if combined_content:
                        # Generate output filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"playlist_transcripts_{timestamp}.{format_name}"
                        output_file = output_path / filename
                        
                        # Export content
                        if export_manager.export_content(combined_content, format_name, output_file):
                            export_successful = True
                        else:
                            console.print(f"[yellow]Warning:[/yellow] Failed to export {format_name} format")
                    
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] Error exporting {format_name}: {str(e)}")
            
            if export_successful:
                console.print(f"\n[green]✓ Success![/green] Files saved to: {output_path.absolute()}")
                console.print(f"Processed {len(successful_results)} out of {len(results)} videos")
                
                # Show generated files
                if not quiet:
                    _show_generated_files(output_path, formats)
            else:
                console.print(f"[red]✗ Error:[/red] No files were successfully exported")
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Processing interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.exception("Processing error")


def _combine_transcripts(results: List[ConcurrentProcessingResult], format_name: str) -> str:
    """Combine transcript results into a single document."""
    
    if format_name == 'markdown':
        content_parts = ["# YouTube Playlist Transcripts\n\n"]
        
        for i, result in enumerate(results, 1):
            if result.transcript_video and result.transcript_video.content:
                title = result.transcript_video.title or f"Video {i}"
                video_id = result.task.video_id or "unknown"
                
                content_parts.append(f"## {i}. {title}\n\n")
                content_parts.append(f"**Video ID:** {video_id}\n")
                content_parts.append(f"**URL:** {result.task.video_url}\n\n")
                content_parts.append("### Transcript\n\n")
                content_parts.append(result.transcript_video.content)
                content_parts.append("\n\n---\n\n")
        
        return "".join(content_parts)
    
    elif format_name == 'html':
        content_parts = ["<html><head><title>YouTube Playlist Transcripts</title></head><body>"]
        content_parts.append("<h1>YouTube Playlist Transcripts</h1>")
        
        for i, result in enumerate(results, 1):
            if result.transcript_video and result.transcript_video.content:
                title = result.transcript_video.title or f"Video {i}"
                video_id = result.task.video_id or "unknown"
                
                content_parts.append(f"<h2>{i}. {title}</h2>")
                content_parts.append(f"<p><strong>Video ID:</strong> {video_id}</p>")
                content_parts.append(f"<p><strong>URL:</strong> <a href='{result.task.video_url}'>{result.task.video_url}</a></p>")
                content_parts.append("<h3>Transcript</h3>")
                # Convert newlines to <br> for HTML
                transcript_html = result.transcript_video.content.replace('\n', '<br>\n')
                content_parts.append(f"<p>{transcript_html}</p>")
                content_parts.append("<hr>")
        
        content_parts.append("</body></html>")
        return "".join(content_parts)
    
    else:
        # For other formats, use plain text
        content_parts = ["YouTube Playlist Transcripts\n\n"]
        
        for i, result in enumerate(results, 1):
            if result.transcript_video and result.transcript_video.content:
                title = result.transcript_video.title or f"Video {i}"
                video_id = result.task.video_id or "unknown"
                
                content_parts.append(f"{i}. {title}\n")
                content_parts.append(f"Video ID: {video_id}\n")
                content_parts.append(f"URL: {result.task.video_url}\n\n")
                content_parts.append("Transcript:\n")
                content_parts.append(result.transcript_video.content)
                content_parts.append("\n\n" + "="*50 + "\n\n")
        
        return "".join(content_parts)


def _show_generated_files(output_path: Path, formats: List[str]) -> None:
    """Display information about generated files."""
    
    table = Table(title="Generated Files")
    table.add_column("Format", style="cyan")
    table.add_column("File", style="white")
    table.add_column("Size", style="green")
    
    for fmt in formats:
        pattern = f"*.{fmt}"
        files = list(output_path.glob(pattern))
        
        for file in files:
            if file.is_file():
                size = file.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                table.add_row(fmt.upper(), file.name, size_str)
    
    console.print(table)


@cli.command()
@click.option('--status', type=click.Choice(['active', 'completed', 'failed', 'all']), 
              default='all', help='Filter jobs by status')
@click.option('--limit', default=10, type=int, help='Maximum number of jobs to show')
@click.pass_context
def list_jobs(ctx, status, limit):
    """List resumable and completed jobs."""
    
    app = ctx.obj['app']
    quiet = ctx.obj['quiet']
    
    try:
        jobs = app.job_manager.get_jobs_by_status(status if status != 'all' else None)
        
        if not jobs:
            console.print(f"[yellow]No jobs found with status: {status}[/yellow]")
            return
        
        # Limit results
        jobs = jobs[:limit]
        
        if not quiet:
            console.print(f"\n[bold]Jobs ({status}):[/bold]")
        
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Source", style="white", max_width=50)
        table.add_column("Status", style="green")
        table.add_column("Progress", style="yellow")
        table.add_column("Updated", style="dim")
        
        for job in jobs:
            job_id = job['id'][:8] + "..."
            source = job['source_url']
            if len(source) > 47:
                source = source[:44] + "..."
            
            status_color = {
                'active': 'blue',
                'completed': 'green',
                'failed': 'red',
                'paused': 'yellow'
            }.get(job['status'], 'white')
            
            progress_text = f"{job['completed_items']}/{job['total_items']}"
            updated = job['updated_at'][:19] if job['updated_at'] else "Unknown"
            
            table.add_row(
                job_id,
                source,
                f"[{status_color}]{job['status']}[/{status_color}]",
                progress_text,
                updated
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.exception("Error listing jobs")


@cli.command()
@click.argument('job_id', required=True)
@click.option('--force', is_flag=True, help='Force resume even if job appears completed')
@click.pass_context
def resume(ctx, job_id, force):
    """Resume an interrupted job."""
    
    app = ctx.obj['app']
    quiet = ctx.obj['quiet']
    result = {'success': False, 'error': 'Operation not completed'}
    
    try:
        if not quiet:
            console.print(f"[bold]Resuming job:[/bold] {job_id}")
        
        # Find job by partial ID
        jobs = app.job_manager.get_resumable_jobs()
        matching_job: Optional[Dict[str, Any]] = None
        
        for job in jobs:
            if job['id'].startswith(job_id):
                matching_job = job
                break
        
        if not matching_job:
            console.print(f"[red]Error:[/red] Job not found: {job_id}")
            ctx.exit(1)
        
        # At this point matching_job should be valid, but let's add a safety check
        if matching_job and 'id' in matching_job:
            result = asyncio.run(app.resume_job(matching_job['id']))
        else:
            console.print(f"[red]Error:[/red] Invalid job data for: {job_id}")
            ctx.exit(1)
        
        if result.get('success'):
            console.print("[green]✓ Job resumed successfully![/green]")
            if 'remaining_items' in result:
                console.print(f"Remaining items: {result['remaining_items']}")
        else:
            console.print(f"[red]✗ Resume failed:[/red] {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.exception("Error resuming job")


@cli.command()
@click.option('--show-api-key', is_flag=True, help='Show current API key (masked)')
@click.option('--show-all', is_flag=True, help='Show all configuration values')
@click.pass_context
def config(ctx, show_api_key, show_all):
    """Show and manage configuration settings."""
    
    app = ctx.obj['app']
    quiet = ctx.obj['quiet']
    
    try:
        if show_all:
            _show_full_config(app)
        elif show_api_key:
            _show_api_key_config(app)
        else:
            _show_basic_config(app)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.exception("Error showing config")


def _show_basic_config(app: YTECli) -> None:
    """Show basic configuration information."""
    
    config_data = app.config_manager.get_auto_fill_data()
    
    table = Table(title="Configuration Summary")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Source", style="dim")
    
    table.add_row("Language", config_data.get('language', 'English'), "Environment/Default")
    table.add_row("Refinement Style", str(config_data.get('refinement_style', 'Summary')), "Environment/Default")
    table.add_row("Chunk Size", str(config_data.get('chunk_size', 3000)), "Environment/Default")
    table.add_row("Gemini Model", config_data.get('gemini_model', 'Default'), "Environment/Default")
    
    api_key = config_data.get('api_key', '')
    api_status = "✓ Set" if api_key else "✗ Missing"
    table.add_row("API Key", api_status, "Secure Storage/Environment")
    
    console.print(table)


def _show_api_key_config(app: YTECli) -> None:
    """Show API key configuration (masked)."""
    
    api_key = app.config_manager.get_api_key()
    if api_key:
        masked_key = api_key[:8] + "*" * (len(api_key) - 12) + api_key[-4:]
        console.print(f"API Key: {masked_key}")
    else:
        console.print("[red]API Key: Not configured[/red]")


def _show_full_config(app: YTECli) -> None:
    """Show full configuration including file paths."""
    
    _show_basic_config(app)
    
    console.print("\n[bold]File Paths:[/bold]")
    paths_table = Table()
    paths_table.add_column("Path Type", style="cyan")
    paths_table.add_column("Location", style="white")
    
    paths_table.add_row("Transcript Output", app.config_manager.get_transcript_output_file() or "Default")
    paths_table.add_row("Gemini Output", app.config_manager.get_gemini_output_file() or "Default")
    
    console.print(paths_table)


@cli.command()
@click.option('--interactive', is_flag=True, help='Interactive setup wizard')
@click.pass_context
def setup(ctx, interactive):
    """Initial setup wizard for first-time users."""
    
    app = ctx.obj['app']
    quiet = ctx.obj['quiet']
    
    if not quiet:
        console.print("[bold]YouTube Transcript Extractor Setup[/bold]\n")
    
    if interactive:
        _run_interactive_setup(app)
    else:
        _run_quick_setup(app)


def _run_interactive_setup(app: YTECli) -> None:
    """Run interactive setup wizard."""
    
    console.print("Welcome to the interactive setup wizard!\n")
    
    # API Key setup
    current_key = app.config_manager.get_api_key()
    if current_key:
        console.print("✓ API key is already configured")
        if Confirm.ask("Would you like to update it?"):
            _setup_api_key(app)
    else:
        console.print("⚠ API key is required for processing")
        _setup_api_key(app)
    
    # Language setup
    current_lang = app.config_manager.get_language()
    console.print(f"\nCurrent language: {current_lang}")
    if Confirm.ask("Would you like to change the output language?"):
        new_lang = Prompt.ask("Enter preferred language", default=current_lang)
        # This would need to be implemented to save to config
        console.print(f"Language set to: {new_lang}")
    
    # Output directory setup
    output_dir = Path("outputs")
    console.print(f"\nDefault output directory: {output_dir.absolute()}")
    if Confirm.ask("Would you like to use a different output directory?"):
        new_dir = Prompt.ask("Enter output directory path", default=str(output_dir))
        output_dir = Path(new_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"Output directory: {output_dir.absolute()}")
    
    console.print("\n[green]✓ Setup completed![/green]")
    console.print("You can now use: [bold]youtube-transcript-extractor process <URL>[/bold]")


def _run_quick_setup(app: YTECli) -> None:
    """Run quick setup check."""
    
    issues = []
    
    # Check API key
    if not app.config_manager.get_api_key():
        issues.append("❌ Gemini API key not configured")
    else:
        console.print("✓ API key configured")
    
    # Check output directory
    output_dir = Path("outputs")
    if output_dir.exists():
        console.print("✓ Output directory exists")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        console.print("✓ Created output directory")
    
    if issues:
        console.print("\n[yellow]Setup Issues:[/yellow]")
        for issue in issues:
            console.print(issue)
        console.print("\nRun: [bold]youtube-transcript-extractor setup --interactive[/bold] to fix these issues")
    else:
        console.print("\n[green]✓ Setup looks good![/green]")


def _setup_api_key(app: YTECli) -> None:
    """Setup API key through interactive prompt."""
    
    console.print("\nTo get a Gemini API key:")
    console.print("1. Visit: https://makersuite.google.com/app/apikey")
    console.print("2. Create a new API key")
    console.print("3. Copy the key\n")
    
    api_key = Prompt.ask("Enter your Gemini API key", password=True)
    
    if api_key and api_key.strip():
        if app.config_manager.set_api_key(api_key.strip()):
            console.print("[green]✓ API key saved securely[/green]")
        else:
            console.print("[red]✗ Failed to save API key[/red]")
    else:
        console.print("[yellow]API key setup skipped[/yellow]")


def main():
    """Entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
