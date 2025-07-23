"""
YouTube Transcript Extractor - Main package.
"""

__version__ = "2.0.0"
__author__ = "YouTube Transcript Extractor Team"
__description__ = "A modular application for extracting and refining YouTube transcripts using AI"

"""
YouTube Transcript Extractor - Main package.
"""

__version__ = "2.0.0"
__author__ = "YouTube Transcript Extractor Team"
__description__ = "A modular application for extracting and refining YouTube transcripts using AI"

# Use centralized dependency management
try:
    from .utils.dependencies import (
        get_dependency_manager, 
        has_gui_support,
        get_available_export_formats
    )
    
    # Import core components with proper error handling
    dependency_manager = get_dependency_manager()
    
    # Core imports that should always be available
    from .core.models import ProcessingConfig, ProcessingMode, RefinementStyle, GeminiModels
    from .core.transcript_fetcher import TranscriptFetcher
    from .core.gemini_processor import GeminiProcessor
    from .utils.config import ConfigManager
    from .utils.validators import InputValidator
    
    # Optional imports with graceful degradation
    MainWindow = None
    if has_gui_support():
        try:
            from .ui.main_window import MainWindow
        except ImportError:
            pass
    
    __all__ = [
        'ProcessingConfig', 'ProcessingMode', 'RefinementStyle', 'GeminiModels',
        'TranscriptFetcher', 'GeminiProcessor', 'MainWindow', 'ConfigManager', 'InputValidator',
        'dependency_manager', 'has_gui_support'
    ]

except ImportError as e:
    # Fallback for cases where dependency management is not available
    import warnings
    warnings.warn(f"Could not import all components: {e}")
    
    # Set essential components to None for graceful degradation
    ProcessingConfig = None
    ProcessingMode = None
    RefinementStyle = None
    GeminiModels = None
    TranscriptFetcher = None
    GeminiProcessor = None
    MainWindow = None
    ConfigManager = None
    InputValidator = None
    dependency_manager = None
    
    __all__ = [
        'ProcessingConfig', 'ProcessingMode', 'RefinementStyle', 'GeminiModels',
        'TranscriptFetcher', 'GeminiProcessor', 'MainWindow', 'ConfigManager', 'InputValidator'
    ]
