"""
Centralized dependency management for YouTube Transcript Extractor.

This module provides a unified way to handle optional dependencies with graceful degradation
and consistent user messaging throughout the application.
"""

import sys
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DependencyLevel(Enum):
    """Dependency requirement levels."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    DEVELOPMENT = "development"


class FeatureArea(Enum):
    """Application feature areas."""
    CORE = "core"
    CLI = "cli"
    GUI = "gui"
    EXPORT = "export"
    SECURITY = "security"
    ASYNC = "async"
    AI = "ai"
    TESTING = "testing"


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    import_name: str
    level: DependencyLevel
    feature_area: FeatureArea
    install_command: str
    description: str
    fallback_message: Optional[str] = None
    min_version: Optional[str] = None
    is_available: bool = False
    import_error: Optional[str] = None


class DependencyManager:
    """Centralized dependency management system."""
    
    def __init__(self):
        """Initialize dependency manager."""
        self._dependencies: Dict[str, DependencyInfo] = {}
        self._feature_cache: Dict[str, bool] = {}
        self._register_dependencies()
        self._check_all_dependencies()
    
    def _register_dependencies(self) -> None:
        """Register all known dependencies."""
        
        # Core dependencies (should always be available)
        self.register_dependency(
            name="click",
            import_name="click",
            level=DependencyLevel.REQUIRED,
            feature_area=FeatureArea.CLI,
            install_command="pip install click",
            description="Command-line interface framework"
        )
        
        self.register_dependency(
            name="rich",
            import_name="rich",
            level=DependencyLevel.REQUIRED,
            feature_area=FeatureArea.CLI,
            install_command="pip install rich",
            description="Rich text and beautiful formatting for CLI"
        )
        
        # AI/Processing dependencies
        self.register_dependency(
            name="google-generativeai",
            import_name="google.generativeai",
            level=DependencyLevel.REQUIRED,
            feature_area=FeatureArea.AI,
            install_command="pip install google-generativeai",
            description="Google Gemini AI API client",
            fallback_message="AI processing features will not be available"
        )
        
        self.register_dependency(
            name="youtube-transcript-api",
            import_name="youtube_transcript_api",
            level=DependencyLevel.REQUIRED,
            feature_area=FeatureArea.CORE,
            install_command="pip install youtube-transcript-api",
            description="YouTube transcript extraction API"
        )
        
        self.register_dependency(
            name="pytube",
            import_name="pytube",
            level=DependencyLevel.REQUIRED,
            feature_area=FeatureArea.CORE,
            install_command="pip install pytube",
            description="YouTube video information extraction"
        )
        
        # Async processing dependencies
        self.register_dependency(
            name="aiohttp",
            import_name="aiohttp",
            level=DependencyLevel.OPTIONAL,
            feature_area=FeatureArea.ASYNC,
            install_command="pip install aiohttp",
            description="Async HTTP client for concurrent processing",
            fallback_message="Concurrent processing will use synchronous methods"
        )
        
        self.register_dependency(
            name="tenacity",
            import_name="tenacity",
            level=DependencyLevel.OPTIONAL,
            feature_area=FeatureArea.ASYNC,
            install_command="pip install tenacity",
            description="Retry library for robust async operations",
            fallback_message="Simple retry logic will be used instead"
        )
        
        # Security dependencies
        self.register_dependency(
            name="keyring",
            import_name="keyring",
            level=DependencyLevel.OPTIONAL,
            feature_area=FeatureArea.SECURITY,
            install_command="pip install keyring",
            description="Secure credential storage",
            fallback_message="API keys will be stored in plaintext configuration"
        )
        
        self.register_dependency(
            name="cryptography",
            import_name="cryptography.fernet",
            level=DependencyLevel.OPTIONAL,
            feature_area=FeatureArea.SECURITY,
            install_command="pip install cryptography",
            description="Encryption for secure configuration storage",
            fallback_message="Configuration will be stored without encryption"
        )
        
        # Export format dependencies
        self.register_dependency(
            name="markdown",
            import_name="markdown",
            level=DependencyLevel.OPTIONAL,
            feature_area=FeatureArea.EXPORT,
            install_command="pip install markdown",
            description="Enhanced markdown processing and conversion",
            fallback_message="Basic markdown export will be used"
        )
        
        self.register_dependency(
            name="reportlab",
            import_name="reportlab.lib.pagesizes",
            level=DependencyLevel.OPTIONAL,
            feature_area=FeatureArea.EXPORT,
            install_command="pip install reportlab",
            description="PDF generation and formatting",
            fallback_message="PDF export will not be available"
        )
        
        self.register_dependency(
            name="python-docx",
            import_name="docx",
            level=DependencyLevel.OPTIONAL,
            feature_area=FeatureArea.EXPORT,
            install_command="pip install python-docx",
            description="Microsoft Word document generation",
            fallback_message="DOCX export will not be available"
        )
        
        # GUI dependencies
        self.register_dependency(
            name="PyQt5",
            import_name="PyQt5.QtWidgets",
            level=DependencyLevel.OPTIONAL,
            feature_area=FeatureArea.GUI,
            install_command="pip install PyQt5",
            description="Qt-based graphical user interface",
            fallback_message="GUI mode will not be available"
        )
        
        # Development/Testing dependencies
        self.register_dependency(
            name="pytest",
            import_name="pytest",
            level=DependencyLevel.DEVELOPMENT,
            feature_area=FeatureArea.TESTING,
            install_command="pip install pytest",
            description="Testing framework"
        )
    
    def register_dependency(
        self,
        name: str,
        import_name: str,
        level: DependencyLevel,
        feature_area: FeatureArea,
        install_command: str,
        description: str,
        fallback_message: Optional[str] = None,
        min_version: Optional[str] = None
    ) -> None:
        """Register a dependency.
        
        Args:
            name: Package name
            import_name: Import name (may differ from package name)
            level: Dependency level
            feature_area: Feature area this dependency supports
            install_command: Command to install this dependency
            description: Human-readable description
            fallback_message: Message to show when dependency is missing
            min_version: Minimum required version
        """
        self._dependencies[name] = DependencyInfo(
            name=name,
            import_name=import_name,
            level=level,
            feature_area=feature_area,
            install_command=install_command,
            description=description,
            fallback_message=fallback_message,
            min_version=min_version
        )
    
    def _check_all_dependencies(self) -> None:
        """Check availability of all registered dependencies."""
        for dep_info in self._dependencies.values():
            self._check_dependency(dep_info)
    
    def _check_dependency(self, dep_info: DependencyInfo) -> bool:
        """Check if a dependency is available.
        
        Args:
            dep_info: Dependency information
            
        Returns:
            True if dependency is available
        """
        try:
            __import__(dep_info.import_name)
            dep_info.is_available = True
            dep_info.import_error = None
            return True
        except ImportError as e:
            dep_info.is_available = False
            dep_info.import_error = str(e)
            
            if dep_info.level == DependencyLevel.REQUIRED:
                logger.warning(f"Required dependency '{dep_info.name}' is not available: {e}")
            else:
                logger.info(f"Optional dependency '{dep_info.name}' is not available: {e}")
            
            return False
    
    def is_available(self, name: str) -> bool:
        """Check if a dependency is available.
        
        Args:
            name: Dependency name
            
        Returns:
            True if dependency is available
        """
        if name not in self._dependencies:
            logger.warning(f"Unknown dependency '{name}' requested")
            return False
        
        return self._dependencies[name].is_available
    
    def require_dependency(self, name: str, feature_description: str = "") -> bool:
        """Require a dependency for a feature.
        
        Args:
            name: Dependency name
            feature_description: Description of the feature needing this dependency
            
        Returns:
            True if dependency is available
            
        Raises:
            ImportError: If required dependency is not available
        """
        if not self.is_available(name):
            dep_info = self._dependencies.get(name)
            if not dep_info:
                raise ImportError(f"Unknown dependency '{name}' required for {feature_description}")
            
            error_msg = f"Missing dependency '{name}' required for {feature_description}"
            if dep_info.fallback_message:
                error_msg += f". {dep_info.fallback_message}"
            error_msg += f". Install with: {dep_info.install_command}"
            
            if dep_info.level == DependencyLevel.REQUIRED:
                raise ImportError(error_msg)
            else:
                logger.warning(error_msg)
                return False
        
        return True
    
    def get_missing_required(self) -> List[DependencyInfo]:
        """Get list of missing required dependencies.
        
        Returns:
            List of missing required dependencies
        """
        return [
            dep for dep in self._dependencies.values()
            if dep.level == DependencyLevel.REQUIRED and not dep.is_available
        ]
    
    def get_missing_optional(self) -> List[DependencyInfo]:
        """Get list of missing optional dependencies.
        
        Returns:
            List of missing optional dependencies
        """
        return [
            dep for dep in self._dependencies.values()
            if dep.level == DependencyLevel.OPTIONAL and not dep.is_available
        ]
    
    def get_feature_availability(self, feature_area: FeatureArea) -> Dict[str, bool]:
        """Get availability status for all dependencies in a feature area.
        
        Args:
            feature_area: Feature area to check
            
        Returns:
            Dictionary mapping dependency names to availability
        """
        return {
            dep.name: dep.is_available
            for dep in self._dependencies.values()
            if dep.feature_area == feature_area
        }
    
    def get_dependency_report(self) -> Dict[str, Any]:
        """Generate comprehensive dependency report.
        
        Returns:
            Dictionary with dependency status information
        """
        available = [dep for dep in self._dependencies.values() if dep.is_available]
        missing_required = self.get_missing_required()
        missing_optional = self.get_missing_optional()
        
        return {
            "total_dependencies": len(self._dependencies),
            "available_count": len(available),
            "missing_required_count": len(missing_required),
            "missing_optional_count": len(missing_optional),
            "available": [dep.name for dep in available],
            "missing_required": [dep.name for dep in missing_required],
            "missing_optional": [dep.name for dep in missing_optional],
            "feature_status": {
                area.value: self.get_feature_availability(area)
                for area in FeatureArea
            }
        }
    
    def print_dependency_status(self) -> None:
        """Print formatted dependency status to console."""
        report = self.get_dependency_report()
        
        print("=== Dependency Status Report ===")
        print(f"Total dependencies: {report['total_dependencies']}")
        print(f"Available: {report['available_count']}")
        print(f"Missing required: {report['missing_required_count']}")
        print(f"Missing optional: {report['missing_optional_count']}")
        
        if report['missing_required']:
            print("\n⚠️  Missing REQUIRED dependencies:")
            for name in report['missing_required']:
                dep = self._dependencies[name]
                print(f"  - {name}: {dep.description}")
                print(f"    Install: {dep.install_command}")
        
        if report['missing_optional']:
            print("\n💡 Missing OPTIONAL dependencies:")
            for name in report['missing_optional']:
                dep = self._dependencies[name]
                print(f"  - {name}: {dep.description}")
                print(f"    Install: {dep.install_command}")
                if dep.fallback_message:
                    print(f"    Fallback: {dep.fallback_message}")
        
        print("\n📋 Feature Area Status:")
        for area, deps in report['feature_status'].items():
            available_count = sum(1 for available in deps.values() if available)
            total_count = len(deps)
            status = "✅" if available_count == total_count else "⚠️" if available_count > 0 else "❌"
            print(f"  {status} {area.title()}: {available_count}/{total_count} available")


# Global dependency manager instance
_dependency_manager: Optional[DependencyManager] = None


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance.
    
    Returns:
        Global dependency manager
    """
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


# Convenience functions for common operations
def is_available(name: str) -> bool:
    """Check if a dependency is available.
    
    Args:
        name: Dependency name
        
    Returns:
        True if dependency is available
    """
    return get_dependency_manager().is_available(name)


def require_dependency(name: str, feature_description: str = "") -> bool:
    """Require a dependency for a feature.
    
    Args:
        name: Dependency name
        feature_description: Description of the feature needing this dependency
        
    Returns:
        True if dependency is available
        
    Raises:
        ImportError: If required dependency is not available
    """
    return get_dependency_manager().require_dependency(name, feature_description)


def safe_import(import_name: str, package_name: Optional[str] = None) -> Tuple[Any, bool]:
    """Safely import a module with fallback.
    
    Args:
        import_name: Name to import (e.g., 'requests.get')
        package_name: Package name for dependency tracking (defaults to first part of import_name)
        
    Returns:
        Tuple of (imported_object_or_None, success_boolean)
    """
    if package_name is None:
        package_name = import_name.split('.')[0]
    
    try:
        # Handle complex import paths
        parts = import_name.split('.')
        module = __import__(parts[0])
        for part in parts[1:]:
            module = getattr(module, part)
        return module, True
    except (ImportError, AttributeError) as e:
        manager = get_dependency_manager()
        if package_name in manager._dependencies:
            dep_info = manager._dependencies[package_name]
            if dep_info.fallback_message:
                logger.info(f"Using fallback for {package_name}: {dep_info.fallback_message}")
        return None, False


# Feature availability checkers
def has_async_support() -> bool:
    """Check if async processing features are available."""
    return is_available("aiohttp") and is_available("tenacity")


def has_security_features() -> bool:
    """Check if security features are available."""
    return is_available("keyring") and is_available("cryptography")


def has_pdf_export() -> bool:
    """Check if PDF export is available."""
    return is_available("reportlab")


def has_docx_export() -> bool:
    """Check if DOCX export is available."""
    return is_available("python-docx")


def has_gui_support() -> bool:
    """Check if GUI features are available."""
    return is_available("PyQt5")


def get_available_export_formats() -> List[str]:
    """Get list of available export formats based on dependencies.
    
    Returns:
        List of available export format names
    """
    formats = ["txt", "markdown", "html"]  # Always available
    
    if has_pdf_export():
        formats.append("pdf")
    
    if has_docx_export():
        formats.append("docx")
    
    return formats
