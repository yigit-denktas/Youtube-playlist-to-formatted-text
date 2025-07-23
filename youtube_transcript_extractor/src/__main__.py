"""
Simple entry point for YouTube Transcript Extractor.

This module serves as the main entry point, delegating to either CLI or GUI mode.
"""

import sys

def main():
    """Main entry point - delegate to CLI or GUI based on arguments."""
    
    # Import dependency manager for better error handling
    try:
        from .utils.dependencies import get_dependency_manager, has_gui_support
        dependency_manager = get_dependency_manager()
    except ImportError:
        dependency_manager = None
        has_gui_support = lambda: False
    
    # Check if GUI mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        # Check GUI availability using dependency manager
        if dependency_manager and not has_gui_support():
            print("❌ GUI not available: PyQt5 dependency is missing")
            print("Install GUI dependencies: pip install PyQt5")
            print("Or use CLI mode without --gui flag")
            sys.exit(1)
            
        try:
            from .ui.main_window import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"❌ GUI not available: {e}")
            if dependency_manager:
                gui_deps = [dep for dep in dependency_manager._dependencies.values() 
                           if dep.feature_area.value == "gui" and not dep.is_available]
                if gui_deps:
                    print("Missing GUI dependencies:")
                    for dep in gui_deps:
                        print(f"  {dep.install_command}")
            print("Please install GUI dependencies or use CLI mode")
            sys.exit(1)
    else:
        # Default to CLI mode
        try:
            from .cli import main as cli_main
            cli_main()
        except ImportError as e:
            print(f"❌ CLI not available: {e}")
            if dependency_manager:
                cli_deps = [dep for dep in dependency_manager._dependencies.values() 
                           if dep.feature_area.value == "cli" and not dep.is_available]
                if cli_deps:
                    print("Missing CLI dependencies:")
                    for dep in cli_deps:
                        print(f"  {dep.install_command}")
            else:
                print("Please ensure click and rich are installed: pip install click rich")
            sys.exit(1)


if __name__ == "__main__":
    main()
