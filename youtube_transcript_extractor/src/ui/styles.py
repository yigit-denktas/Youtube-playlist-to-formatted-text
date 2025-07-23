"""
UI styles and themes for the YouTube Transcript Extractor application.
"""

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt


class DarkTheme:
    """Dark theme colors and styles for the application."""
    
    # Color palette
    BACKGROUND = "#2c3e50"
    SECONDARY_BACKGROUND = "#34495e"
    ACCENT = "#5ba8e5"
    SUCCESS = "#2ecc71"
    SUCCESS_HOVER = "#27ae60"
    WARNING = "#e67e22"
    WARNING_HOVER = "#d35400"
    ERROR = "#e74c3c"
    ERROR_HOVER = "#c0392b"
    INFO = "#3498db"
    INFO_HOVER = "#2980b9"
    PURPLE = "#9b59b6"
    PURPLE_HOVER = "#8e44ad"
    GRAY = "#95a5a6"
    GRAY_HOVER = "#7f8c8d"
    
    TEXT_PRIMARY = "#ecf0f1"
    TEXT_SECONDARY = "#c8d1d5"
    TEXT_PLACEHOLDER = "#a8b8c3"
    TEXT_DISABLED = "#9ca9aa"
    
    BORDER = "#7f8c8d"
    SELECTION_BG = "#5ba8e5"
    SELECTION_TEXT = "#ffffff"


class StyleSheets:
    """Collection of stylesheet definitions for UI components."""
    
    @staticmethod
    def main_window() -> str:
        """Main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {DarkTheme.BACKGROUND};
            }}
            QLabel {{
                color: {DarkTheme.TEXT_PRIMARY};
            }}
        """
    
    @staticmethod
    def input_field() -> str:
        """Input field stylesheet."""
        return f"""
            QLineEdit {{
                background-color: {DarkTheme.SECONDARY_BACKGROUND};
                border: 2px solid {DarkTheme.ACCENT};
                border-radius: 5px;
                color: {DarkTheme.TEXT_PRIMARY};
                padding: 10px 12px;
                font-size: 9pt;
                min-height: 16px;
                selection-background-color: {DarkTheme.SELECTION_BG};
                selection-color: {DarkTheme.SELECTION_TEXT};
            }}
            QLineEdit:disabled {{
                background-color: {DarkTheme.BACKGROUND};
                border-color: {DarkTheme.BORDER};
                color: {DarkTheme.TEXT_DISABLED};
                padding: 10px 12px;
            }}
            QLineEdit:read-only {{
                background-color: {DarkTheme.SECONDARY_BACKGROUND};
                border: 2px solid {DarkTheme.ACCENT};
                color: {DarkTheme.TEXT_PRIMARY};
                font-weight: normal;
                padding: 10px 12px;
            }}
            QLineEdit:focus {{
                border: 2px solid {DarkTheme.SUCCESS};
                background-color: #3e5470;
                padding: 10px 12px;
            }}
        """
    
    @staticmethod
    def button(color1: str, color2: str) -> str:
        """Button stylesheet with gradient colors."""
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color1}, stop:1 {color2});
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                min-height: 20px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color2}, stop:1 {color1});
            }}
            QPushButton:disabled {{
                background: {DarkTheme.GRAY};
                color: {DarkTheme.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def combobox() -> str:
        """ComboBox stylesheet."""
        return f"""
            QComboBox {{
                background-color: {DarkTheme.SECONDARY_BACKGROUND};
                border: 2px solid {DarkTheme.ACCENT};
                border-radius: 5px;
                color: {DarkTheme.TEXT_PRIMARY};
                padding: 0px;
                font-size: 10pt;
            }}
            QComboBox:!editable, QComboBox::drop-down:editable {{
                 background: {DarkTheme.SECONDARY_BACKGROUND};
            }}

            QComboBox:on {{
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #9ca9aa;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }}

            QComboBox::down-arrow:on {{
                top: 1px;
                left: 1px;
            }}

            QComboBox QAbstractItemView {{
                border: 2px solid {DarkTheme.ACCENT};
                border-radius: 5px;
                background-color: {DarkTheme.BACKGROUND};
                color: {DarkTheme.TEXT_PRIMARY};
                selection-background-color: {DarkTheme.ACCENT};
                selection-color: {DarkTheme.TEXT_PRIMARY};
            }}
        """
    
    @staticmethod
    def progress_bar() -> str:
        """Progress bar stylesheet."""
        return f"""
            QProgressBar {{
                background: {DarkTheme.BACKGROUND};
                border: 2px solid {DarkTheme.INFO};
                border-radius: 5px;
                text-align: center;
                color: white;
                font-size: 12px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {DarkTheme.INFO}, stop:1 {DarkTheme.SUCCESS});
                border-radius: 3px;
            }}
        """
    
    @staticmethod
    def text_display() -> str:
        """Text display area stylesheet."""
        return f"""
            QTextEdit {{
                background-color: {DarkTheme.BACKGROUND};
                border: 2px solid {DarkTheme.INFO};
                border-radius: 5px;
                color: {DarkTheme.TEXT_PRIMARY};
                font-size: 12px;
                padding: 8px;
            }}
        """
    
    @staticmethod
    def scroll_area() -> str:
        """Scroll area stylesheet."""
        return f"""
            QScrollArea {{
                background-color: {DarkTheme.BACKGROUND};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {DarkTheme.SECONDARY_BACKGROUND};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {DarkTheme.ACCENT};
                border-radius: 6px;
                min-height: 20px;
            }}
        """
    
    @staticmethod
    def slider() -> str:
        """Slider stylesheet."""
        return f"""
            QSlider {{
                padding: 0px;
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                margin: 2px 0;
                background: {DarkTheme.SECONDARY_BACKGROUND};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 12px;
                margin: -6px 0px;
                background: {DarkTheme.ACCENT};
                border-radius: 6px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {DarkTheme.SUCCESS};
            }}
        """
    
    @staticmethod
    def container() -> str:
        """Container widget stylesheet."""
        return f"""
            background-color: {DarkTheme.BACKGROUND};
            border-radius: 10px;
            padding: 15px;
        """
    
    @staticmethod
    def input_container() -> str:
        """Input container stylesheet."""
        return f"""
            background-color: {DarkTheme.SECONDARY_BACKGROUND};
            border-radius: 8px;
            padding: 12px;
            margin: 4px;
        """
    
    @staticmethod
    def progress_container() -> str:
        """Progress container stylesheet."""
        return f"""
            background-color: {DarkTheme.SECONDARY_BACKGROUND};
            border-radius: 10px;
            padding: 10px;
        """


class ButtonStyles:
    """Predefined button style combinations."""
    
    @staticmethod
    def success() -> str:
        """Success button style (green)."""
        return StyleSheets.button(DarkTheme.SUCCESS, DarkTheme.SUCCESS_HOVER)
    
    @staticmethod
    def warning() -> str:
        """Warning button style (orange)."""
        return StyleSheets.button(DarkTheme.WARNING, DarkTheme.WARNING_HOVER)
    
    @staticmethod
    def error() -> str:
        """Error button style (red)."""
        return StyleSheets.button(DarkTheme.ERROR, DarkTheme.ERROR_HOVER)
    
    @staticmethod
    def info() -> str:
        """Info button style (blue)."""
        return StyleSheets.button(DarkTheme.INFO, DarkTheme.INFO_HOVER)
    
    @staticmethod
    def purple() -> str:
        """Purple button style."""
        return StyleSheets.button(DarkTheme.PURPLE, DarkTheme.PURPLE_HOVER)
    
    @staticmethod
    def gray() -> str:
        """Gray button style."""
        return StyleSheets.button(DarkTheme.GRAY, DarkTheme.GRAY_HOVER)


class PaletteSetup:
    """Helper for setting up widget palettes."""
    
    @staticmethod
    def setup_input_palette(widget) -> None:
        """Set up dark theme palette for input widgets.
        
        Args:
            widget: Input widget to configure
        """
        palette = widget.palette()
        palette.setColor(QPalette.Text, QColor(DarkTheme.TEXT_PRIMARY))
        palette.setColor(QPalette.PlaceholderText, QColor(DarkTheme.TEXT_PLACEHOLDER))
        palette.setColor(QPalette.Base, QColor(DarkTheme.SECONDARY_BACKGROUND))
        palette.setColor(QPalette.Highlight, QColor(DarkTheme.SELECTION_BG))
        palette.setColor(QPalette.HighlightedText, QColor(DarkTheme.SELECTION_TEXT))
        widget.setPalette(palette)


class MessageBoxStyles:
    """Styles for message boxes."""
    
    @staticmethod
    def dark_theme() -> str:
        """Dark theme message box style."""
        return f"color: {DarkTheme.TEXT_PRIMARY}; background-color: {DarkTheme.SECONDARY_BACKGROUND};"


class Fonts:
    """Font definitions for the application."""
    
    # Font families
    PRIMARY_FONT = "Segoe UI"
    
    # Font sizes
    TITLE_SIZE = 18
    HEADING_SIZE = 12
    LABEL_SIZE = 10
    TEXT_SIZE = 9
    SMALL_SIZE = 8
