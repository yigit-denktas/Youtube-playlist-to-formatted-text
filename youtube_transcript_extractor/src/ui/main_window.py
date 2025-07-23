"""
Main window UI for the YouTube Transcript Extractor application.
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
    QComboBox, QSlider, QDialog, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor

from ..core.models import (
    ProcessingConfig, ProcessingMode, RefinementStyle, GeminiModels,
    ProcessingPrompts, ProcessingProgress, ProcessingResult
)
from ..core.transcript_fetcher import TranscriptFetcher
from ..core.gemini_processor import GeminiProcessor
from ..utils.config import ConfigManager, DefaultPaths
from ..utils.validators import InputValidator
from .styles import (
    StyleSheets, ButtonStyles, PaletteSetup, MessageBoxStyles,
    DarkTheme, Fonts
)


class UIHelpers:
    """Helper methods for consistent UI styling."""
    
    @staticmethod
    def create_label_font(bold: bool = False) -> QFont:
        """Create a consistent label font.
        
        Args:
            bold: Whether the font should be bold
            
        Returns:
            Configured QFont object
        """
        weight = QFont.Bold if bold else QFont.Normal
        return QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE, weight)
    
    @staticmethod
    def create_title_font() -> QFont:
        """Create a consistent title font.
        
        Returns:
            Configured QFont object for titles
        """
        return QFont(Fonts.PRIMARY_FONT, Fonts.TITLE_SIZE, QFont.Bold)


class ProcessingThread(QThread):
    """Thread for handling transcript extraction and Gemini processing."""
    
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    processing_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config: ProcessingConfig):
        """Initialize processing thread.
        
        Args:
            config: Processing configuration
        """
        super().__init__()
        self.config = config
        self.transcript_fetcher = TranscriptFetcher()
        self.gemini_processor: Optional[GeminiProcessor] = None
        self._is_running = True
    
    def run(self) -> None:
        """Run the processing pipeline."""
        try:
            # Step 1: Extract transcripts
            self.status_update.emit("Starting transcript extraction...")
            
            if self.config.mode == ProcessingMode.YOUTUBE_URL:
                result = self.transcript_fetcher.fetch_from_youtube(
                    self.config.source_path,
                    self.config.transcript_output_file,
                    self._progress_callback,
                    self._status_callback
                )
            else:  # LOCAL_FOLDER
                result = self.transcript_fetcher.fetch_from_local_folder(
                    self.config.source_path,
                    self.config.transcript_output_file,
                    self._progress_callback,
                    self._status_callback
                )
            
            if not result.success:
                self.error_occurred.emit(result.error_message or "Unknown error during transcript extraction")
                return
            
            # Step 2: Process with Gemini
            if not self._is_running:
                return
            
            self.status_update.emit("Starting Gemini AI processing...")
            self.progress_update.emit(0)  # Reset progress for Gemini processing
            
            self.gemini_processor = GeminiProcessor(
                self.config.api_key,
                self.config.gemini_model
            )
            
            gemini_result = self.gemini_processor.process_transcripts(
                self.config.transcript_output_file,
                self.config.gemini_output_file,
                self.config.output_language,
                self.config.refinement_style,
                self.config.chunk_size,
                self._progress_callback,
                self._status_callback
            )
            
            if gemini_result.success:
                self.processing_complete.emit(gemini_result.output_file or "")
            else:
                self.error_occurred.emit(gemini_result.error_message or "Unknown error during Gemini processing")
                
        except Exception as e:
            self.error_occurred.emit(f"Processing error: {str(e)}")
    
    def stop(self) -> None:
        """Stop the processing."""
        self._is_running = False
        if self.transcript_fetcher:
            self.transcript_fetcher.cancel()
        if self.gemini_processor:
            self.gemini_processor.cancel()
    
    def _progress_callback(self, progress: ProcessingProgress) -> None:
        """Handle progress updates."""
        if self._is_running:
            self.progress_update.emit(progress.percentage)
    
    def _status_callback(self, message: str) -> None:
        """Handle status updates."""
        if self._is_running:
            self.status_update.emit(message)


class ModelSelectionDialog(QDialog):
    """Dialog for selecting Gemini model."""
    
    def __init__(self, parent=None, current_model: str = ""):
        """Initialize model selection dialog.
        
        Args:
            parent: Parent widget
            current_model: Currently selected model
        """
        super().__init__(parent)
        self.setWindowTitle("Select Gemini Model")
        self.setStyleSheet(MessageBoxStyles.dark_theme())
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout()
        
        # Label
        label = QLabel("Choose a Gemini model for refinement:")
        label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE))
        layout.addWidget(label)
        
        # Model combo box
        self.model_combo = QComboBox()
        self.model_combo.addItems(GeminiModels.get_models())
        if current_model in GeminiModels.get_models():
            self.model_combo.setCurrentText(current_model)
        self.model_combo.setStyleSheet(StyleSheets.combobox())
        layout.addWidget(self.model_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet(ButtonStyles.success())
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(ButtonStyles.gray())
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_selected_model(self) -> str:
        """Get the selected model.
        
        Returns:
            Selected model name
        """
        return self.model_combo.currentText()


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.processing_thread: Optional[ProcessingThread] = None
        self.is_processing = False
        
        # UI state
        self.selected_refinement_style = RefinementStyle.BALANCED_DETAILED
        self.selected_model = GeminiModels.get_default_model()
        
        # Initialize UI
        self.init_ui()
        self.center_window()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("YouTube Playlist Transcript & Gemini Refinement Extractor")
        self.setMinimumSize(900, 850)
        self.setStyleSheet(StyleSheets.main_window())
        
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(StyleSheets.scroll_area())
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 22, 10)
        scroll_layout.setSpacing(15)
        
        # Add UI sections
        self._create_title_section(scroll_layout)
        self._create_input_section(scroll_layout)
        self._create_progress_section(scroll_layout)
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        
        # Control buttons
        self._create_control_buttons(main_layout)
        
        # Set layout
        self.central_widget.setLayout(main_layout)
        self.showMaximized()
    
    def _create_title_section(self, layout: QVBoxLayout) -> None:
        """Create the title section."""
        title_label = QLabel("YouTube Playlist Transcript & Gemini Refinement Extractor")
        title_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.TITLE_SIZE, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setStyleSheet(f"""
            color: {DarkTheme.SUCCESS};
            padding: 10px;
            border-radius: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {DarkTheme.BACKGROUND}, stop:1 {DarkTheme.ACCENT});
        """)
        layout.addWidget(title_label)
    
    def _create_input_section(self, layout: QVBoxLayout) -> None:
        """Create the input section."""
        input_container = QWidget()
        input_container.setStyleSheet(StyleSheets.container())
        input_layout = QVBoxLayout(input_container)
        input_layout.setSpacing(15)
        
        # Source selection
        self._create_source_section(input_layout)
        
        # Language input
        self._create_language_section(input_layout)
        
        # Style selection
        self._create_style_section(input_layout)
        
        # Chunk size
        self._create_chunk_size_section(input_layout)
        
        # File outputs
        self._create_file_sections(input_layout)
        
        # API key
        self._create_api_key_section(input_layout)
        
        layout.addWidget(input_container)
    
    def _create_source_section(self, layout: QVBoxLayout) -> None:
        """Create the input source section."""
        source_layout = QVBoxLayout()
        
        source_label = QLabel("Input Source:")
        source_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE, QFont.Bold))
        source_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY};")
        source_layout.addWidget(source_label)
        
        # YouTube URL container
        url_container = QWidget()
        url_container.setStyleSheet(StyleSheets.input_container())
        url_container_layout = QVBoxLayout(url_container)
        url_container_layout.setContentsMargins(12, 12, 12, 12)
        url_container_layout.setSpacing(8)
        
        url_label = QLabel("YouTube URL (Playlist or Video):")
        url_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.TEXT_SIZE, QFont.Bold))
        url_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY};")
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube playlist or video URL")
        self._setup_input_field(self.url_input)
        self.url_input.textChanged.connect(self._on_url_changed)
        
        url_container_layout.addWidget(url_label)
        url_container_layout.addWidget(self.url_input)
        source_layout.addWidget(url_container)
        
        # OR divider
        self._create_or_divider(source_layout)
        
        # Local folder container
        folder_container = QWidget()
        folder_container.setStyleSheet(StyleSheets.input_container())
        folder_container_layout = QVBoxLayout(folder_container)
        folder_container_layout.setContentsMargins(12, 12, 12, 12)
        folder_container_layout.setSpacing(8)
        
        folder_label = QLabel("Local Transcript Folder:")
        folder_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.TEXT_SIZE, QFont.Bold))
        folder_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY};")
        
        folder_input_layout = QHBoxLayout()
        folder_input_layout.setSpacing(8)
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a folder containing transcript files (.txt)")
        self.folder_input.setReadOnly(True)
        self._setup_input_field(self.folder_input)
        self.folder_input.textChanged.connect(self._on_folder_changed)
        
        self.select_folder_button = QPushButton("Browse Folder")
        self.select_folder_button.setStyleSheet(ButtonStyles.warning())
        self.select_folder_button.clicked.connect(self._select_local_folder)
        self.select_folder_button.setMinimumHeight(36)
        self.select_folder_button.setFixedWidth(120)
        
        folder_input_layout.addWidget(self.folder_input)
        folder_input_layout.addWidget(self.select_folder_button)
        
        folder_container_layout.addWidget(folder_label)
        folder_container_layout.addLayout(folder_input_layout)
        source_layout.addWidget(folder_container)
        
        layout.addLayout(source_layout)
    
    def _create_or_divider(self, layout: QVBoxLayout) -> None:
        """Create an OR divider."""
        or_layout = QHBoxLayout()
        
        or_line1 = QLabel()
        or_line1.setStyleSheet(f"background-color: {DarkTheme.BORDER}; height: 1px;")
        or_line1.setFixedHeight(1)
        
        or_text = QLabel("OR")
        or_text.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE, QFont.Bold))
        or_text.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; padding: 0 10px;")
        or_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        or_line2 = QLabel()
        or_line2.setStyleSheet(f"background-color: {DarkTheme.BORDER}; height: 1px;")
        or_line2.setFixedHeight(1)
        
        or_layout.addWidget(or_line1, 1)
        or_layout.addWidget(or_text, 0)
        or_layout.addWidget(or_line2, 1)
        
        layout.addLayout(or_layout)
    
    def _create_language_section(self, layout: QVBoxLayout) -> None:
        """Create the language input section."""
        language_layout = QVBoxLayout()
        
        language_label = QLabel("Output Language:")
        language_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE, QFont.Bold))
        language_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY};")
        
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("e.g., English, Spanish, French")
        self._setup_input_field(self.language_input)
        self.language_input.setText(self.config_manager.get_language())
        
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_input)
        layout.addLayout(language_layout)
    
    def _create_style_section(self, layout: QVBoxLayout) -> None:
        """Create the refinement style section."""
        style_layout = QVBoxLayout()
        
        style_label = QLabel("Refinement Style:")
        style_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE, QFont.Bold))
        style_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY};")
        
        self.style_combo = QComboBox()
        self.style_combo.addItems([style.value for style in RefinementStyle])
        self.style_combo.setCurrentText(self.selected_refinement_style.value)
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        self.style_combo.setStyleSheet(StyleSheets.combobox())
        
        style_layout.addWidget(style_label)
        style_layout.addWidget(self.style_combo)
        layout.addLayout(style_layout)
    
    def _create_chunk_size_section(self, layout: QVBoxLayout) -> None:
        """Create the chunk size section."""
        chunk_layout = QVBoxLayout()
        chunk_layout.setSpacing(2)
        chunk_layout.setContentsMargins(5, 5, 5, 5)
        
        chunk_label = QLabel("Chunk Size:")
        chunk_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE, QFont.Bold))
        chunk_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; margin-bottom: 4px;")
        chunk_layout.addWidget(chunk_label)
        
        self.chunk_slider = QSlider(Qt.Orientation.Horizontal)
        self.chunk_slider.setMinimum(2000)
        self.chunk_slider.setMaximum(50000)
        self.chunk_slider.setValue(self.config_manager.get_chunk_size())
        self.chunk_slider.valueChanged.connect(self._on_chunk_size_changed)
        self.chunk_slider.setStyleSheet(StyleSheets.slider())
        chunk_layout.addWidget(self.chunk_slider)
        
        self.chunk_value_label = QLabel(str(self.chunk_slider.value()))
        self.chunk_value_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE))
        self.chunk_value_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; margin-top: 4px;")
        chunk_layout.addWidget(self.chunk_value_label)
        
        chunk_desc = QLabel(
            "(Maximum number of words per API call. Larger chunks: Fewer calls, faster execution, "
            "but potentially lower detail. Good for summarizing longer videos.)"
        )
        chunk_desc.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.SMALL_SIZE))
        chunk_desc.setStyleSheet(f"""
            color: {DarkTheme.TEXT_SECONDARY};
            margin-top: 18px;
            padding: 2px;
        """)
        chunk_desc.setWordWrap(True)
        chunk_layout.addWidget(chunk_desc)
        
        layout.addLayout(chunk_layout)
    
    def _create_file_sections(self, layout: QVBoxLayout) -> None:
        """Create the file input sections."""
        self._create_file_input(layout, "Transcript Output:", "Choose File",
                              "transcript_file_input", self._select_transcript_file)
        self._create_file_input(layout, "Gemini Output:", "Choose File",
                              "gemini_file_input", self._select_gemini_file)
    
    def _create_file_input(self, parent_layout: QVBoxLayout, label_text: str,
                          button_text: str, field_name: str, handler) -> None:
        """Create a file input section."""
        file_layout = QHBoxLayout()
        
        input_field = QLineEdit()
        input_field.setObjectName(field_name)
        input_field.setReadOnly(True)
        input_field.setPlaceholderText(f"Select {label_text.split(':')[0]} file")
        self._setup_input_field(input_field)
        input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        button = QPushButton(button_text)
        button.setStyleSheet(ButtonStyles.info())
        button.setMinimumHeight(36)
        button.setFixedWidth(120)
        button.clicked.connect(handler)
        
        file_layout.addWidget(input_field)
        file_layout.addWidget(button)
        
        label = QLabel(label_text)
        label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE, QFont.Bold))
        label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; padding: 0px;")
        
        parent_layout.addWidget(label)
        parent_layout.addLayout(file_layout)
        
        setattr(self, field_name, input_field)
    
    def _create_api_key_section(self, layout: QVBoxLayout) -> None:
        """Create the API key section."""
        api_layout = QVBoxLayout()
        
        api_label = QLabel("Gemini API Key:")
        api_label.setFont(QFont(Fonts.PRIMARY_FONT, Fonts.LABEL_SIZE, QFont.Bold))
        api_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY};")
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Gemini API key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self._setup_input_field(self.api_key_input)
        self.api_key_input.setText(self.config_manager.get_api_key())
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input)
        layout.addLayout(api_layout)
    
    def _create_progress_section(self, layout: QVBoxLayout) -> None:
        """Create the progress section."""
        progress_container = QWidget()
        progress_container.setStyleSheet(StyleSheets.progress_container())
        progress_layout = QVBoxLayout(progress_container)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet(StyleSheets.progress_bar())
        progress_layout.addWidget(self.progress_bar)
        
        # Status display
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMinimumHeight(150)
        self.status_display.setMaximumHeight(200)
        self.status_display.setStyleSheet(StyleSheets.text_display())
        progress_layout.addWidget(self.status_display)
        
        layout.addWidget(progress_container)
    
    def _create_control_buttons(self, layout: QVBoxLayout) -> None:
        """Create the control buttons."""
        control_layout = QHBoxLayout()
        control_layout.setSpacing(20)
        
        # Auto-fill button
        self.autofill_button = QPushButton("Auto-fill from .env")
        self.autofill_button.setStyleSheet(ButtonStyles.purple())
        self.autofill_button.setMinimumHeight(40)
        self.autofill_button.clicked.connect(self._autofill_from_env)
        
        # Start button
        self.start_button = QPushButton("Start Processing")
        self.start_button.setStyleSheet(ButtonStyles.success())
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self._start_processing)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(ButtonStyles.error())
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self._cancel_processing)
        self.cancel_button.setEnabled(False)
        
        control_layout.addStretch(1)
        control_layout.addWidget(self.autofill_button)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.cancel_button)
        control_layout.addStretch(1)
        
        layout.addLayout(control_layout)
    
    def _setup_input_field(self, field: QLineEdit) -> None:
        """Set up input field with proper styling."""
        field.setStyleSheet(StyleSheets.input_field())
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        PaletteSetup.setup_input_palette(field)
    
    def center_window(self) -> None:
        """Center the window on screen."""
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen()
        if screen is not None:
            center_point = screen.availableGeometry().center()
            frame.moveCenter(center_point)
            self.move(frame.topLeft())
    
    # Event handlers
    def _on_url_changed(self, text: str) -> None:
        """Handle URL input change."""
        if text.strip():
            self.folder_input.clear()
    
    def _on_folder_changed(self, text: str) -> None:
        """Handle folder input change."""
        if text.strip():
            self.url_input.clear()
    
    def _on_style_changed(self, style_text: str) -> None:
        """Handle refinement style change."""
        for style in RefinementStyle:
            if style.value == style_text:
                self.selected_refinement_style = style
                # Update chunk size to default for this style
                default_chunk_size = ProcessingPrompts.get_default_chunk_size(style)
                self.chunk_slider.setValue(default_chunk_size)
                break
    
    @pyqtSlot(int)
    def _on_chunk_size_changed(self, value: int) -> None:
        """Handle chunk size change."""
        self.chunk_value_label.setText(str(value))
    
    def _select_local_folder(self) -> None:
        """Select local folder containing transcript files."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder Containing Transcript Files",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder_path:
            self.folder_input.setText(folder_path)
            self.url_input.clear()
    
    def _select_transcript_file(self) -> None:
        """Select transcript output file."""
        self._select_output_file("Select Transcript Output File", self.transcript_file_input)
    
    def _select_gemini_file(self) -> None:
        """Select Gemini output file."""
        self._select_output_file("Select Gemini Output File", self.gemini_file_input)
    
    def _select_output_file(self, title: str, field: QLineEdit) -> None:
        """Select output file."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, title, "", "Text Files (*.txt);;All Files (*)", options=options
        )
        if file_path:
            file_path = DefaultPaths.ensure_txt_extension(file_path)
            field.setText(file_path)
    
    def _autofill_from_env(self) -> None:
        """Auto-fill form fields from environment variables."""
        try:
            self.config_manager.load_environment()
            data = self.config_manager.get_auto_fill_data()
            count = 0
            
            # Fill fields with data
            if data["language"]:
                self.language_input.setText(data["language"])
                count += 1
            
            if data["api_key"]:
                self.api_key_input.setText(data["api_key"])
                count += 1
            
            if data["transcript_output_file"]:
                self.transcript_file_input.setText(data["transcript_output_file"])
                count += 1
            
            if data["gemini_output_file"]:
                self.gemini_file_input.setText(data["gemini_output_file"])
                count += 1
            
            if data["refinement_style"] != RefinementStyle.BALANCED_DETAILED:
                self.style_combo.setCurrentText(data["refinement_style"].value)
                self.selected_refinement_style = data["refinement_style"]
                count += 1
            
            if data["chunk_size"] != 3000:
                self.chunk_slider.setValue(data["chunk_size"])
                count += 1
            
            if data["gemini_model"] != GeminiModels.get_default_model():
                self.selected_model = data["gemini_model"]
                count += 1
            
            # Show result
            if count > 0:
                self._show_message(
                    QMessageBox.Information,
                    "Auto-fill Complete",
                    f"Successfully auto-filled {count} field(s) from .env file!"
                )
                self._update_status(f"✅ Auto-filled {count} fields from .env file", DarkTheme.PURPLE)
            else:
                self._show_message(
                    QMessageBox.Warning,
                    "Auto-fill Warning",
                    "No values found in .env file to auto-fill.\n\n"
                    "Make sure your .env file exists and contains the required variables."
                )
                
        except Exception as e:
            self._show_message(
                QMessageBox.Critical,
                "Auto-fill Error",
                f"Error reading .env file: {str(e)}"
            )
    
    def _start_processing(self) -> None:
        """Start the processing pipeline."""
        # Validate inputs
        is_valid, error_message = self._validate_inputs()
        if not is_valid:
            self._show_message(QMessageBox.Warning, "Validation Error", error_message)
            return
        
        # Select Gemini model
        dialog = ModelSelectionDialog(self, self.selected_model)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_model = dialog.get_selected_model()
        else:
            return  # User cancelled
        
        # Create processing configuration
        config = self._create_processing_config()
        
        # Set UI state
        self._set_processing_state(True)
        self.progress_bar.setValue(0)
        self.status_display.clear()
        
        # Start processing thread
        self.processing_thread = ProcessingThread(config)
        self.processing_thread.progress_update.connect(self.progress_bar.setValue)
        self.processing_thread.status_update.connect(self._update_status)
        self.processing_thread.processing_complete.connect(self._handle_success)
        self.processing_thread.error_occurred.connect(self._handle_error)
        
        self._update_status("Starting processing...", DarkTheme.INFO)
        self.processing_thread.start()
    
    def _cancel_processing(self) -> None:
        """Cancel the current processing."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.processing_thread.quit()
            self.processing_thread.wait()
        
        self._set_processing_state(False)
        self._update_status("Processing cancelled by user", DarkTheme.ERROR)
        self.progress_bar.setValue(0)
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs."""
        url_text = self.url_input.text().strip()
        folder_text = self.folder_input.text().strip()
        transcript_file = self.transcript_file_input.text().strip()
        gemini_file = self.gemini_file_input.text().strip()
        api_key = self.api_key_input.text().strip()
        language = self.language_input.text().strip()
        chunk_size = self.chunk_slider.value()
        
        return InputValidator.validate_processing_inputs(
            url_text, folder_text, transcript_file, gemini_file,
            api_key, language, chunk_size
        )
    
    def _create_processing_config(self) -> ProcessingConfig:
        """Create processing configuration from UI inputs."""
        url_text = self.url_input.text().strip()
        folder_text = self.folder_input.text().strip()
        
        # Determine mode and source
        if url_text:
            mode = ProcessingMode.YOUTUBE_URL
            source_path = url_text
        else:
            mode = ProcessingMode.LOCAL_FOLDER
            source_path = folder_text
        
        # Get or generate output file paths
        transcript_file = self.transcript_file_input.text().strip()
        if not transcript_file:
            transcript_file = DefaultPaths.get_default_transcript_filename()
        
        gemini_file = self.gemini_file_input.text().strip()
        if not gemini_file:
            gemini_file = DefaultPaths.get_default_gemini_filename()
        
        return ProcessingConfig(
            mode=mode,
            source_path=source_path,
            output_language=self.language_input.text().strip(),
            refinement_style=self.selected_refinement_style,
            chunk_size=self.chunk_slider.value(),
            gemini_model=self.selected_model,
            api_key=self.api_key_input.text().strip(),
            transcript_output_file=transcript_file,
            gemini_output_file=gemini_file
        )
    
    def _set_processing_state(self, processing: bool) -> None:
        """Set the UI processing state."""
        self.is_processing = processing
        self.start_button.setEnabled(not processing)
        self.cancel_button.setEnabled(processing)
        self.autofill_button.setEnabled(not processing)
        
        # Set input fields read-only during processing
        inputs = [
            self.url_input, self.folder_input, self.language_input,
            self.transcript_file_input, self.gemini_file_input, self.api_key_input
        ]
        for input_field in inputs:
            input_field.setReadOnly(processing)
    
    def _update_status(self, message: str, color: str = DarkTheme.INFO) -> None:
        """Update status display."""
        self.status_display.append(f"<font color='{color}'>{message}</font>")
    
    def _handle_success(self, output_file: str) -> None:
        """Handle successful processing."""
        self._set_processing_state(False)
        self.progress_bar.setValue(100)
        
        self._show_message(
            QMessageBox.Information,
            "Success",
            f"Processing complete!\nOutput saved to: {output_file}"
        )
        
        self._update_status("✅ Processing completed successfully!", DarkTheme.SUCCESS)
    
    def _handle_error(self, error_message: str) -> None:
        """Handle processing error."""
        self._set_processing_state(False)
        self.progress_bar.setValue(0)
        
        self._show_message(QMessageBox.Critical, "Error", error_message)
        self._update_status(f"❌ Error: {error_message}", DarkTheme.ERROR)
    
    def _show_message(self, icon: QMessageBox.Icon, title: str, message: str) -> None:
        """Show a message box with dark theme styling."""
        msg_box = QMessageBox()
        msg_box.setStyleSheet(MessageBoxStyles.dark_theme())
        msg_box.setIcon(icon)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.exec_()
    

def main():
    """Main function to run the GUI application."""
    import sys
    app = QApplication(sys.argv)
    
    # Apply a consistent, modern style palette
    try:
        PaletteSetup.setup_input_palette(app)
    except AttributeError:
        # Fallback if setup_dark_theme doesn't exist
        pass
    
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()