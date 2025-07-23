"""
Simple entry point for YouTube Transcript Extractor.

This module serves as the main entry point, delegating to either CLI or GUI mode.
"""

import sys
import os
from pathlib import Path

# Ensure the youtube_transcript_extractor is in the path
current_dir = Path(__file__).parent
yte_path = current_dir / "youtube_transcript_extractor"
sys.path.insert(0, str(yte_path))

def main():
    """Main entry point - delegate to CLI or GUI based on arguments."""
    
    # Check if GUI mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        try:
            from .ui.main_window import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"❌ GUI not available: {e}")
            print("Please install GUI dependencies or use CLI mode")
            sys.exit(1)
    else:
        # Default to CLI mode
        try:
            from .cli import main as cli_main
            cli_main()
        except ImportError as e:
            print(f"❌ CLI not available: {e}")
            print("Please ensure all dependencies are installed")
            sys.exit(1)


if __name__ == "__main__":
    main()
