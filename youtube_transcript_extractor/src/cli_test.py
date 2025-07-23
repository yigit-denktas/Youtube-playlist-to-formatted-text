"""
Minimal CLI test to verify basic functionality.
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

@click.group(invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-essential output')
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, verbose, quiet, version):
    """YouTube Transcript Extractor - Convert YouTube content to structured text."""
    
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    
    if version:
        console.print("YouTube Transcript Extractor v2.0.0")
        ctx.exit()
    
    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        if not quiet:
            welcome_text = Text("YouTube Transcript Extractor CLI", style="bold magenta")
            console.print(Panel(welcome_text, expand=False))
            console.print("Transform YouTube content into structured, AI-refined text\n")
        console.print("Use --help to see available commands or run a specific command.\n")
        console.print("Quick start: [bold]youtube-transcript-extractor process <URL>[/bold]")


@cli.command()
@click.argument('url', required=True)
@click.option('--output', '-o', default='outputs', help='Output directory')
@click.option('--formats', '-f', default='markdown,html', help='Export formats (comma-separated)')
@click.pass_context
def process(ctx, url, output, formats):
    """Process a YouTube playlist or video and generate formatted transcripts."""
    
    quiet = ctx.obj['quiet']
    
    if not quiet:
        console.print(f"[bold]Processing:[/bold] {url}")
    
    # Basic validation
    youtube_patterns = ['youtube.com/watch', 'youtube.com/playlist', 'youtu.be/', 'm.youtube.com']
    if not any(pattern in url for pattern in youtube_patterns):
        console.print("[red]Error:[/red] Invalid YouTube URL format")
        ctx.exit(1)
    
    console.print(f"[green]✓ URL validation passed[/green]")
    console.print(f"Output directory: {output}")
    console.print(f"Export formats: {formats}")
    console.print("[yellow]Note:[/yellow] This is a test version - actual processing not implemented yet")


@cli.command()
def deps():
    """Check dependency status and availability."""
    console.print("[bold]Dependency Status Check[/bold]\n")
    
    try:
        # Import the dependency manager
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from utils.dependencies import get_dependency_manager, FeatureArea
        
        manager = get_dependency_manager()
        
        # Group dependencies by feature area
        by_feature = {}
        for dep in manager._dependencies.values():
            area = dep.feature_area.value
            if area not in by_feature:
                by_feature[area] = []
            by_feature[area].append(dep)
        
        # Display status for each feature area
        for area, deps in sorted(by_feature.items()):
            console.print(f"[bold cyan]📦 {area.upper()} Dependencies[/bold cyan]")
            
            for dep in sorted(deps, key=lambda x: x.name):
                status = "[green]✓[/green]" if dep.is_available else "[red]✗[/red]"
                level_color = {
                    "required": "red",
                    "optional": "yellow", 
                    "development": "blue"
                }.get(dep.level.value, "white")
                
                console.print(f"  {status} {dep.name} [{level_color}]({dep.level.value})[/{level_color}] - {dep.description}")
                
                if not dep.is_available:
                    console.print(f"    [dim]Install: {dep.install_command}[/dim]")
                    if dep.fallback_message:
                        console.print(f"    [dim]Fallback: {dep.fallback_message}[/dim]")
            
            console.print()
        
        # Show feature availability summary
        console.print("[bold]Feature Availability Summary[/bold]")
        
        try:
            from utils.dependencies import (
                has_async_support, has_security_features, 
                has_pdf_export, has_docx_export, has_gui_support,
                get_available_export_formats
            )
            
            features = [
                ("Async Processing", has_async_support()),
                ("Security Features", has_security_features()),
                ("PDF Export", has_pdf_export()),
                ("DOCX Export", has_docx_export()),
                ("GUI Support", has_gui_support()),
            ]
            
            for feature, available in features:
                status = "[green]✓[/green]" if available else "[red]✗[/red]"
                console.print(f"  {status} {feature}")
            
            console.print(f"\n[bold]Available Export Formats:[/bold] {', '.join(get_available_export_formats())}")
            
        except ImportError:
            console.print("[yellow]⚠ Could not check feature availability[/yellow]")
    
    except ImportError as e:
        console.print(f"[red]Error loading dependency manager: {e}[/red]")
        console.print("[yellow]Dependency management system may not be properly set up[/yellow]")


@cli.command()
def setup():
    """Initial setup wizard for first-time users."""
    
    console.print("[bold]YouTube Transcript Extractor Setup[/bold]\n")
    console.print("Setup wizard would run here...")
    console.print("[green]✓ Setup completed![/green]")


@cli.command()
def deps_detailed():
    """Check dependency status and feature availability."""
    try:
        # Add current directory to path for imports
        import sys
        from pathlib import Path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        from utils.dependencies import get_dependency_manager
        manager = get_dependency_manager()
        
        # Get dependency report
        report = manager.get_dependency_report()
        
        console.print("[bold]Dependency Status Report[/bold]\n")
        
        # Summary
        console.print(f"Total dependencies: {report['total_dependencies']}")
        console.print(f"✅ Available: {report['available_count']}")
        console.print(f"⚠️  Missing required: {report['missing_required_count']}")
        console.print(f"💡 Missing optional: {report['missing_optional_count']}\n")
        
        # Missing required dependencies
        if report['missing_required']:
            console.print("[bold red]Missing REQUIRED dependencies:[/bold red]")
            for name in report['missing_required']:
                dep = manager._dependencies[name]
                console.print(f"  ❌ [bold]{name}[/bold]: {dep.description}")
                console.print(f"     Install: [cyan]{dep.install_command}[/cyan]")
            console.print()
        
        # Missing optional dependencies
        if report['missing_optional']:
            console.print("[bold yellow]Missing OPTIONAL dependencies:[/bold yellow]")
            for name in report['missing_optional']:
                dep = manager._dependencies[name]
                console.print(f"  💡 [bold]{name}[/bold]: {dep.description}")
                console.print(f"     Install: [cyan]{dep.install_command}[/cyan]")
                if dep.fallback_message:
                    console.print(f"     Fallback: {dep.fallback_message}")
            console.print()
        
        # Feature area status
        console.print("[bold]Feature Area Status:[/bold]")
        for area, deps in report['feature_status'].items():
            if not deps:  # Skip empty feature areas
                continue
                
            available_count = sum(1 for available in deps.values() if available)
            total_count = len(deps)
            
            if available_count == total_count:
                status = "✅"
                color = "green"
            elif available_count > 0:
                status = "⚠️"
                color = "yellow"
            else:
                status = "❌"
                color = "red"
            
            console.print(f"  {status} [{color}]{area.title()}[/{color}]: {available_count}/{total_count} available")
            
            # Show which specific dependencies are missing in this area
            missing_in_area = [name for name, available in deps.items() if not available]
            if missing_in_area:
                console.print(f"     Missing: {', '.join(missing_in_area)}")
        
        # Recommendations
        if report['missing_required']:
            console.print("\n[bold red]⚠️  Action Required:[/bold red]")
            console.print("Install missing required dependencies to use core features.")
        elif report['missing_optional']:
            console.print("\n[bold blue]💡 Suggestions:[/bold blue]")
            console.print("Install optional dependencies to unlock additional features.")
        else:
            console.print("\n[bold green]🎉 All dependencies are available![/bold green]")
            
    except ImportError as e:
        console.print(f"[red]Error loading dependency manager: {e}[/red]")
        console.print("This indicates a core system issue.")


@cli.command()
def list_jobs():
    """List resumable and completed jobs."""
    
    console.print("[yellow]No jobs found[/yellow]")


@cli.command()
@click.option('--feature', type=click.Choice(['export', 'security', 'async', 'gui', 'full']), 
              help='Install dependencies for specific feature area')
@click.option('--dry-run', is_flag=True, help='Show what would be installed without installing')
def install_deps(feature, dry_run):
    """Install missing optional dependencies."""
    
    try:
        import subprocess
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from utils.dependencies import get_dependency_manager
        
        manager = get_dependency_manager()
        
        if feature:
            # Install dependencies for specific feature
            console.print(f"[bold]Installing {feature} dependencies[/bold]\n")
            
            # Get dependencies for the feature area
            feature_deps = []
            for dep in manager._dependencies.values():
                if (feature == 'full' or 
                    dep.feature_area.value == feature or
                    (feature == 'gui' and dep.feature_area.value == 'gui')):
                    if not dep.is_available and dep.level.value != 'development':
                        feature_deps.append(dep)
            
            if not feature_deps:
                console.print(f"[green]✓ All {feature} dependencies are already installed![/green]")
                return
            
            # Show what will be installed
            console.print(f"Dependencies to install for {feature}:")
            for dep in feature_deps:
                console.print(f"  • {dep.name} - {dep.description}")
            
            if dry_run:
                console.print("\n[yellow]Dry run - no packages will be installed[/yellow]")
                for dep in feature_deps:
                    console.print(f"Would run: [dim]{dep.install_command}[/dim]")
                return
            
            # Install packages
            console.print(f"\n[bold]Installing {len(feature_deps)} packages...[/bold]")
            
            for dep in feature_deps:
                try:
                    console.print(f"Installing {dep.name}...")
                    result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep.name], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        console.print(f"  ✓ {dep.name} installed successfully")
                    else:
                        console.print(f"  ✗ Failed to install {dep.name}: {result.stderr}")
                except Exception as e:
                    console.print(f"  ✗ Error installing {dep.name}: {e}")
            
            console.print(f"\n[green]✓ {feature.title()} dependencies installation completed![/green]")
            
        else:
            # Show available feature groups
            console.print("[bold]Available dependency groups:[/bold]\n")
            
            groups = {
                'export': 'PDF and DOCX export capabilities',
                'security': 'Secure credential storage and encryption',
                'async': 'Async processing and concurrent operations', 
                'gui': 'Graphical user interface',
                'full': 'All optional features'
            }
            
            for group, description in groups.items():
                console.print(f"  [cyan]{group}[/cyan] - {description}")
            
            console.print("\nUsage: [dim]youtube-transcript-extractor install-deps --feature <group>[/dim]")
            
    except ImportError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("Dependency management system not available")


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
