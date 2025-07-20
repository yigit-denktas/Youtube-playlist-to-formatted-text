import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                             QComboBox, QSlider, QDialog, QScrollArea, QSizePolicy) # Import QComboBox, QDialog, and QScrollArea
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from pytube import Playlist
from youtube_transcript_api._api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound

import google.generativeai as genai
import re
import logging
import os
import time
import random
from dotenv import load_dotenv
load_dotenv(".env")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.prompts = {

            "Balanced and Detailed": """Turn the following unorganized text into a well-structured, readable format while retaining EVERY detail, context, and nuance of the original content.
            Refine the text to improve clarity, grammar, and coherence WITHOUT cutting, summarizing, or omitting any information.
            The goal is to make the content easier to read and process by:

            - Organizing the content into logical sections with appropriate subheadings.
            - Using bullet points or numbered lists where applicable to present facts, stats, or comparisons.
            - Highlighting key terms, names, or headings with bold text for emphasis.
            - Preserving the original tone, humor, and narrative style while ensuring readability.
            - Adding clear separators or headings for topic shifts to improve navigation.

            Ensure the text remains informative, capturing the original intent, tone,
            and details while presenting the information in a format optimized for analysis by both humans and AI.
            REMEMBER that Details are important, DO NOT overlook Any details, even small ones.
            All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
            Text:
            """,

            "Summary": """Summarize the following transcript into a concise and informative summary. 
            Identify the core message, main arguments, and key pieces of information presented in the video.
            The summary should capture the essence of the video's content in a clear and easily understandable way.
            Aim for a summary that is shorter than the original transcript but still accurately reflects its key points.  
            Focus on conveying the most important information and conclusions.
All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
Text: """,
            "Educational": """Transform the following transcript into a comprehensive educational text, resembling a textbook chapter. Structure the content with clear headings, subheadings, and bullet points to enhance readability and organization for educational purposes.

Crucially, identify any technical terms, jargon, or concepts that are mentioned but not explicitly explained within the transcript. For each identified term, provide a concise definition (no more than two sentences) formatted as a blockquote.  Integrate these definitions strategically within the text, ideally near the first mention of the term, to enhance understanding without disrupting the flow.

Ensure the text is highly informative, accurate, and retains all the original details and nuances of the transcript. The goal is to create a valuable educational resource that is easy to study and understand. You can create and include diagrams using mermaid.js syntax to illustrate complex concepts or processes, enhancing the educational value of the text.

All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not use any other language at any point in the response. Do not include this unorganized text into your response.

Text:""",
            "Narrative Rewriting": """Rewrite the following transcript into an engaging narrative or story format. Transform the factual or conversational content into a more captivating and readable piece, similar to a short story or narrative article.

While rewriting, maintain a close adherence to the original subjects and information presented in the video. Do not deviate significantly from the core topics or introduce unrelated elements.  The goal is to enhance engagement and readability through storytelling techniques without altering the fundamental content or message of the video.  Use narrative elements like descriptive language, scene-setting (if appropriate), and a compelling flow to make the information more accessible and enjoyable.

All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.

Text:""",
            "Q&A Generation": """Generate a set of questions and answers based on the following transcript for self-assessment or review.  For each question, create a corresponding answer.

Format each question as a level 3 heading using Markdown syntax (### Question Text). Immediately following each question, provide the answer.  This format is designed for foldable sections, allowing users to easily hide and reveal answers for self-testing.

Ensure the questions are relevant to the key information and concepts in the transcript and that the answers are accurate and comprehensive based on the video content.

All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.

Text:"""
        }
        self.category_chunk_sizes = {
            "Balanced and Detailed": 3000,
            "Summary": 10000,  # Larger chunk size for summarization
            "Educational": 3000, # Default chunk size for detailed output
            "Narrative Rewriting": 5000, # Default chunk size
            "Q&A Generation": 3000   # Default chunk size
        }
        self.selected_category = "Balanced and Detailed" # Default Category
        

        self.extraction_thread = None
        self.gemini_thread = None
        self.is_processing = False
        self.available_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-thinking-exp-01-21", "gemini-2.5-flash-lite-preview-06-17","gemini-2.5-pro-preview-03-25", "gemini-2.0-flash-lite","gemini-1.5-flash", "gemini-1.5-pro"] # Static model list
        self.selected_model_name = "gemini-2.5-flash" # Default model

        self.initUI()

        
        
    def get_combobox_style(self):
        return """
            QComboBox {
                background-color: #34495e;
                border: 2px solid #5ba8e5;
                border-radius: 5px;
                color: #ecf0f1;
                padding: 0px;
                font-size: 10pt;
            }
            QComboBox:!editable, QComboBox::drop-down:editable {
                 background: #34495e;
            }

            QComboBox:on { /* shift the text when the popup opens */
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;

                border-left-width: 1px;
                border-left-color: #9ca9aa;
                border-left-style: solid; /* just a single line */
                border-top-right-radius: 3px; /* same radius as the QComboBox */
                border-bottom-right-radius: 3px;
            }

            QComboBox::down-arrow {
                image: url(down_arrow.png); /* Replace with your arrow image if you want a custom one */
            }

            QComboBox::down-arrow:on { /* shift the arrow when popup is open */
                top: 1px;
                left: 1px;
            }

            QComboBox QAbstractItemView {
                border: 2px solid #5ba8e5;
                border-radius: 5px;
                background-color: #2c3e50;
                color: #ecf0f1;
                selection-background-color: #5ba8e5;
                selection-color: #ecf0f1;
            }
        """

    def category_changed(self, index):
        category_name = self.category_combo.itemText(index) # Get selected category name
        self.selected_category = category_name # Update selected category
        if category_name in self.category_chunk_sizes:
            suggested_chunk_size = self.category_chunk_sizes[category_name]
            self.chunk_size_slider.setValue(suggested_chunk_size) # Set slider value
            self.update_chunk_size_label(suggested_chunk_size) # Update label

    @pyqtSlot(int) # Indicate it's a slot and expects an integer (slider value)
    def update_chunk_size_label(self, value):
        self.chunk_size_value_label.setText(str(value)) # Update the label text with the new slider value


    def initUI(self):
        
        self.setWindowTitle("YouTube Playlist Transcript & Gemini Refinement Extractor")
        self.setMinimumSize(900, 850)
        self.apply_dark_mode()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create scrollable area for better content management
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2c3e50;
                border: none;
            }
            QScrollBar:vertical {
                background: #34495e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #5ba8e5;
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 22, 10)  # Right margin for scrollbar
        scroll_layout.setSpacing(15)

        # Title Section
        title_label = QLabel("YouTube Playlist Transcript & Gemini Refinement Extractor")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setStyleSheet("""
            color: #2ecc71;
            padding: 10px;
            border-radius: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2c3e50, stop:1 #5ba8e5);
        """)
        scroll_layout.addWidget(title_label)

        # Input Container
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #2c3e50; border-radius: 10px; padding: 15px;")
        input_layout = QVBoxLayout(input_container)
        input_layout.setSpacing(15)  # Increased spacing between sections

        # Input Source Section with YouTube URL and Local Folder options
        source_layout = QVBoxLayout()
        source_label = QLabel("Input Source:")
        source_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        source_label.setStyleSheet("color: #ecf0f1;")
        source_layout.addWidget(source_label)

        # YouTube URL Input
        url_container = QWidget()
        url_container.setStyleSheet("background-color: #34495e; border-radius: 8px; padding: 12px; margin: 4px;")
        url_container_layout = QVBoxLayout(url_container)
        url_container_layout.setContentsMargins(12, 12, 12, 12)
        url_container_layout.setSpacing(8)
        
        url_label = QLabel("YouTube URL (Playlist or Video):")
        url_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        url_label.setStyleSheet("color: #ecf0f1;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube playlist or video URL (e.g., https://www.youtube.com/playlist?list=... or https://www.youtube.com/watch?v=...)")
        self.url_input.setFont(QFont("Segoe UI", 9))
        self.setup_input_field_for_dark_theme(self.url_input)
        self.url_input.textChanged.connect(self.on_url_input_changed)
        
        # Explicitly set placeholder text color for dark theme
        palette = self.url_input.palette()
        palette.setColor(palette.PlaceholderText, QColor("#a8b8c3"))
        self.url_input.setPalette(palette)
        url_container_layout.addWidget(url_label)
        url_container_layout.addWidget(self.url_input)
        source_layout.addWidget(url_container)

        # OR Divider
        or_layout = QHBoxLayout()
        or_line1 = QLabel()
        or_line1.setStyleSheet("background-color: #7f8c8d; height: 1px;")
        or_line1.setFixedHeight(1)
        or_text = QLabel("OR")
        or_text.setFont(QFont("Segoe UI", 10, QFont.Bold))
        or_text.setStyleSheet("color: #95a5a6; padding: 0 10px;")
        or_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        or_line2 = QLabel()
        or_line2.setStyleSheet("background-color: #7f8c8d; height: 1px;")
        or_line2.setFixedHeight(1)
        or_layout.addWidget(or_line1, 1)
        or_layout.addWidget(or_text, 0)
        or_layout.addWidget(or_line2, 1)
        source_layout.addLayout(or_layout)

        # Local Folder Input
        folder_container = QWidget()
        folder_container.setStyleSheet("background-color: #34495e; border-radius: 8px; padding: 12px; margin: 4px;")
        folder_container_layout = QVBoxLayout(folder_container)
        folder_container_layout.setContentsMargins(12, 12, 12, 12)
        folder_container_layout.setSpacing(8)
        
        folder_label = QLabel("Local Transcript Folder:")
        folder_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        folder_label.setStyleSheet("color: #ecf0f1;")
        
        folder_input_layout = QHBoxLayout()
        folder_input_layout.setSpacing(8)  # Add spacing between input and button
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a folder containing transcript files (.txt)")
        self.folder_input.setFont(QFont("Segoe UI", 9))
        self.setup_input_field_for_dark_theme(self.folder_input)
        self.folder_input.setReadOnly(True)
        self.folder_input.textChanged.connect(self.on_folder_input_changed)
        
        # Explicitly set placeholder text color for dark theme
        palette = self.folder_input.palette()
        palette.setColor(palette.PlaceholderText, QColor("#a8b8c3"))
        self.folder_input.setPalette(palette)
        
        self.select_folder_button = QPushButton("Browse Folder")
        self.select_folder_button.setStyleSheet(self.get_button_style("#e67e22", "#d35400"))
        self.select_folder_button.clicked.connect(self.select_local_folder)
        self.select_folder_button.setMinimumHeight(36)
        self.select_folder_button.setFixedWidth(120)
        
        folder_input_layout.addWidget(self.folder_input)
        folder_input_layout.addWidget(self.select_folder_button)
        
        folder_container_layout.addWidget(folder_label)
        folder_container_layout.addLayout(folder_input_layout)
        source_layout.addWidget(folder_container)

        input_layout.addLayout(source_layout)

        # Language Input
        language_layout = QVBoxLayout()
        language_label = QLabel("Output Language:")
        language_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        language_label.setStyleSheet("color: #ecf0f1;")
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("e.g., English, Spanish, French")
        self.language_input.setFont(QFont("Segoe UI", 9))
        self.setup_input_field_for_dark_theme(self.language_input)

        self.language_input.setText(os.environ.get("LANGUAGE", ""))
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_input)
        input_layout.addLayout(language_layout)

        # Style Selection
        category_layout = QVBoxLayout()
        category_label = QLabel("Refinement Style:")
        category_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        category_label.setStyleSheet("color: #ecf0f1;")
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.prompts.keys())) 
        self.category_combo.setCurrentText(self.selected_category) 
        self.category_combo.currentIndexChanged.connect(self.category_changed) 
        self.category_combo.setStyleSheet(self.get_combobox_style())
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        input_layout.addLayout(category_layout)
        # Chunk Size Slider Section
        chunk_size_layout = QVBoxLayout()

        
        chunk_size_layout.setSpacing(2)  
        chunk_size_layout.setContentsMargins(5, 5, 5, 5)  

        chunk_size_label = QLabel("Chunk Size:")
        chunk_size_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        chunk_size_label.setStyleSheet("color: #ecf0f1; margin-bottom: 4px;")  
        chunk_size_layout.addWidget(chunk_size_label)

        self.chunk_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.chunk_size_slider.setMinimum(2000)
        self.chunk_size_slider.setMaximum(50000)
        self.chunk_size_slider.setValue(GeminiProcessingThread.DEFAULT_CHUNK_SIZE)
        self.chunk_size_slider.valueChanged.connect(self.update_chunk_size_label)
        self.chunk_size_slider.setStyleSheet("""
            QSlider {
                padding: 0px; /* Reduced padding */
            }
            QSlider::groove:horizontal {
                height: 4px;
                margin: 2px 0; /* Add vertical margin */
            }
            QSlider::handle:horizontal {
                width: 12px;
                margin: -6px 0px;
            }
        """)
        chunk_size_layout.addWidget(self.chunk_size_slider)

        self.chunk_size_value_label = QLabel(str(GeminiProcessingThread.DEFAULT_CHUNK_SIZE))
        self.chunk_size_value_label.setFont(QFont("Segoe UI", 10))
        self.chunk_size_value_label.setStyleSheet("color: #ecf0f1; margin-top: 4px;")  
        chunk_size_layout.addWidget(self.chunk_size_value_label)

        chunk_size_description = QLabel("(Maximum number of words to be given to Gemini as content input per API call)(Default : 3000 words) Bigger chunk size: Fewer API calls, faster execution, but potentially lower detail (good for summarizing longer videos).")
        chunk_size_description.setFont(QFont("Segoe UI", 8))
        chunk_size_description.setStyleSheet("""
            color: #c8d1d5;
            margin-top: 18px;  
            padding: 2px;
        """)
        chunk_size_description.setWordWrap(True)
        chunk_size_layout.addWidget(chunk_size_description)

        input_layout.addLayout(chunk_size_layout)



        


        # File Inputs
        self.create_file_input(input_layout, "   Transcript Output:", "Choose File",
                             "transcript_file_input", self.select_transcript_output_file)
        self.create_file_input(input_layout, "   Gemini Output:", "Choose File",
                             "gemini_file_input", self.select_gemini_output_file)

        # API Key Input
        api_key_layout = QVBoxLayout()
        api_key_label = QLabel("Gemini API Key:")
        api_key_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        api_key_label.setStyleSheet("color: #ecf0f1;")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Gemini API key")
        self.api_key_input.setFont(QFont("Segoe UI", 9))
        self.setup_input_field_for_dark_theme(self.api_key_input)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        # Remove fixed height
        # self.api_key_input.setMinimumHeight(80)

        self.api_key_input.setText(os.environ.get("API_KEY", ""))

        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        input_layout.addLayout(api_key_layout)

        scroll_layout.addWidget(input_container)

        # Progress Section
        progress_container = QWidget()
        progress_container.setStyleSheet("background-color: #34495e; border-radius: 10px; padding: 10px;")
        progress_layout = QVBoxLayout(progress_container)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 5px;
                text-align: center;
                color: white;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        # Status Display
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMinimumHeight(150)
        self.status_display.setMaximumHeight(200)
        self.status_display.setStyleSheet("""
            background-color: #2c3e50;
            border: 2px solid #3498db;
            border-radius: 5px;
            color: #ecf0f1;
            font-size: 12px;
            padding: 8px;
        """)
        progress_layout.addWidget(self.status_display)
        scroll_layout.addWidget(progress_container)

        # Control Buttons
        control_layout = QHBoxLayout()
        control_layout.setSpacing(20)

        # Auto-fill button
        self.autofill_button = QPushButton("Auto-fill from .env")
        self.autofill_button.setStyleSheet(self.get_button_style("#9b59b6", "#8e44ad"))
        self.autofill_button.setMinimumHeight(40)
        self.autofill_button.clicked.connect(self.autofill_from_env)

        self.extract_button = QPushButton("Start Processing")
        self.extract_button.setStyleSheet(self.get_button_style("#2ecc71", "#27ae60"))
        self.extract_button.setMinimumHeight(40)
        self.extract_button.clicked.connect(self.start_extraction_and_refinement)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setEnabled(False)

        control_layout.addStretch(1)
        control_layout.addWidget(self.autofill_button)
        control_layout.addWidget(self.extract_button)
        control_layout.addWidget(self.cancel_button)
        control_layout.addStretch(1)
        
        # Set up the scroll area and main layout
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)  # Give it stretch factor
        main_layout.addLayout(control_layout)
        
        # Set the layout to central widget
        self.central_widget.setLayout(main_layout)
        self.center()
        # Show maximized instead of fullscreen
        self.showMaximized()

    def create_file_input(self, parent_layout, label_text, button_text, field_name, handler):
        layout = QHBoxLayout()
        
        input_field = QLineEdit()
        input_field.setObjectName(field_name)
        input_field.setReadOnly(True)
        input_field.setPlaceholderText(f"Select {label_text.split(':')[0]} file")
        self.setup_input_field_for_dark_theme(input_field)
        
        # Set size policy for proper expansion
        input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        button = QPushButton(button_text)
        button.setStyleSheet(self.get_button_style("#5ba8e5", "#4a94d4"))
        button.setMinimumHeight(36)
        button.setFixedWidth(120)  # Fixed width for consistency
        button.clicked.connect(handler)

        layout.addWidget(input_field)
        layout.addWidget(button)

        font = QFont("Segoe UI", 10, QFont.Bold)
        label = QLabel(label_text)
        label.setFont(font)
        label.setStyleSheet("color: #ecf0f1; padding: 0px;")

        parent_layout.addWidget(label)
        parent_layout.addLayout(layout)

        setattr(self, field_name, input_field)

    def setup_input_field_for_dark_theme(self, input_field):
        """Configure an input field with proper dark theme styling and colors"""
        input_field.setStyleSheet(self.get_input_style())
        
        # Set size policy
        input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Set explicit palette for dark theme compatibility
        palette = input_field.palette()
        palette.setColor(palette.Text, QColor("#ecf0f1"))  # Main text color
        palette.setColor(palette.PlaceholderText, QColor("#a8b8c3"))  # Improved placeholder text color
        palette.setColor(palette.Base, QColor("#34495e"))  # Background color
        palette.setColor(palette.Highlight, QColor("#5ba8e5"))  # Improved selection background
        palette.setColor(palette.HighlightedText, QColor("#ffffff"))  # Selection text
        input_field.setPalette(palette)

    def get_input_style(self):
        return """
            QLineEdit {
                background-color: #34495e;
                border: 2px solid #5ba8e5;
                border-radius: 5px;
                color: #ecf0f1;
                padding: 10px 12px;  /* Increased padding for better text visibility */
                font-size: 9pt;
                min-height: 16px;    /* Reduced from 20px */
                selection-background-color: #5ba8e5;
                selection-color: #ffffff;
            }
            QLineEdit:disabled {
                background-color: #2c3e50;
                border-color: #7f8c8d;
                color: #9ca9aa;
                padding: 10px 12px;
            }
            QLineEdit:read-only {
                background-color: #34495e;
                border: 2px solid #5ba8e5;
                color: #ecf0f1;
                font-weight: normal;
                padding: 10px 12px;
            }
            QLineEdit:focus {
                border: 2px solid #2ecc71;
                background-color: #3e5470;
                padding: 10px 12px;
            }
        """

    def get_button_style(self, color1, color2):
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
                background: #95a5a6;
                color: #7f8c8d;
            }}
        """

    def apply_dark_mode(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
            }
        """)

    def center(self):
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen()
        if screen is not None:
            center_point = screen.availableGeometry().center()
            frame.moveCenter(center_point)
            self.move(frame.topLeft())

    def validate_inputs(self):
        url_text = self.url_input.text().strip()
        folder_text = self.folder_input.text().strip()
        
        # Check if neither URL nor folder is provided
        if not url_text and not folder_text:
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter a YouTube URL or select a local folder containing transcript files")
            msg_box.setWindowTitle("Input Source Required")
            msg_box.exec_()
            return False

        # If URL is provided, validate it
        if url_text and not (url_text.startswith("https://www.youtube.com/playlist") or
                           url_text.startswith("https://www.youtube.com/watch?v=")):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter a valid YouTube playlist or video URL")
            msg_box.setWindowTitle("Invalid URL")
            msg_box.exec_()
            return False

        # If folder is provided, validate it exists and contains txt files
        if folder_text:
            import os
            import glob
            if not os.path.exists(folder_text):
                msg_box = QMessageBox()
                msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText("Selected folder does not exist")
                msg_box.setWindowTitle("Invalid Folder")
                msg_box.exec_()
                return False
            
            # Check if folder contains any .txt files
            txt_files = glob.glob(os.path.join(folder_text, "*.txt"))
            if not txt_files:
                msg_box = QMessageBox()
                msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText("Selected folder does not contain any .txt transcript files")
                msg_box.setWindowTitle("No Transcript Files Found")
                msg_box.exec_()
                return False

        if not self.transcript_file_input.text().endswith(".txt"):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Transcript output file must be a .txt file")
            msg_box.setWindowTitle("Invalid File")
            msg_box.exec_()
            return False

        if not self.gemini_file_input.text().endswith(".txt"):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Gemini output file must be a .txt file")
            msg_box.setWindowTitle("Invalid File")
            msg_box.exec_()
            return False

        if not self.api_key_input.text().strip():
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter your Gemini API key")
            msg_box.setWindowTitle("API Key Required")
            msg_box.exec_()
            return False

        if not self.language_input.text().strip(): # Validate Language Input
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please specify the output language")
            msg_box.setWindowTitle("Language Required")
            msg_box.exec_()
            return False

        return True

    def set_processing_state(self, processing):
        self.is_processing = processing
        self.extract_button.setEnabled(not processing)
        self.cancel_button.setEnabled(processing)
        self.autofill_button.setEnabled(not processing)

        inputs = [self.url_input, self.transcript_file_input,
                self.gemini_file_input, self.api_key_input, self.language_input]
        for input_field in inputs:
            input_field.setReadOnly(processing)

    def select_gemini_model(self):
        model_combo = QComboBox()
        model_combo.addItems(self.available_models)
        model_combo.setCurrentText(self.selected_model_name) 

        # Create a custom dialog instead of trying to modify QMessageBox layout
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Gemini Model")
        dialog.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
        
        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(QLabel("Choose a Gemini model for refinement:"))
        dialog_layout.addWidget(model_combo)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)
        
        dialog.setLayout(dialog_layout)
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            return model_combo.currentText()
        else:
            return None


    def start_extraction_and_refinement(self):
        if not self.validate_inputs():
            return

        selected_model = self.select_gemini_model()
        if selected_model:
            self.selected_model_name = selected_model
        else:
            return # User cancelled model selection
        
        self.set_processing_state(True)
        self.progress_bar.setValue(0)
        self.status_display.clear()

        transcript_output = self.transcript_file_input.text() or \
                          f"transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

        url_text = self.url_input.text().strip()
        folder_text = self.folder_input.text().strip()

        if url_text:
            # Download transcripts from YouTube
            self.extraction_thread = TranscriptExtractionThread(
                url_text,
                transcript_output
            )

            self.extraction_thread.progress_update.connect(self.progress_bar.setValue)
            self.extraction_thread.status_update.connect(self.update_status)
            self.extraction_thread.extraction_complete.connect(self.start_gemini_processing)
            self.extraction_thread.error_occurred.connect(self.handle_error)

            self.status_display.append("<font color='#3498db'>Starting transcript extraction from YouTube...</font>")
            self.extraction_thread.start()
        
        elif folder_text:
            # Process local transcript files
            self.status_display.append("<font color='#e67e22'>Processing local transcript files...</font>")
            self.process_local_transcripts(folder_text, transcript_output)

    def start_gemini_processing(self, transcript_file):
        self.progress_bar.setValue(0) # Reset progress bar for Gemini processing
        self.status_display.append("<font color='#2ecc71'>Transcript extraction complete! Starting Gemini processing...</font>")

        output_language = self.language_input.text() # Get language from input field
        current_chunk_size = self.chunk_size_slider.value()
        selected_prompt = self.prompts[self.selected_category]
        self.gemini_thread = GeminiProcessingThread(
            transcript_file,
            self.gemini_file_input.text(),
            self.api_key_input.text(),
            self.selected_model_name, # Pass selected model name
            output_language, # Pass output language
            chunk_size=current_chunk_size,
            prompt=selected_prompt
        )

        self.gemini_thread.progress_update.connect(self.update_gemini_progress) # Use separate progress update for Gemini
        self.gemini_thread.status_update.connect(self.update_status)
        self.gemini_thread.processing_complete.connect(self.handle_success)
        self.gemini_thread.error_occurred.connect(self.handle_error)

        self.gemini_thread.start()

    def update_gemini_progress(self, progress_percent):
        # Offset the progress bar to start after extraction (assuming extraction takes up to 50%)
        
        gemini_progress = progress_percent 
        self.progress_bar.setValue(gemini_progress)


    def update_status(self, message):
        color = "#3498db" if "extraction" in message else "#2ecc71"
        self.status_display.append(f"<font color='{color}'>{message}</font>")

    def handle_success(self, output_file):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"Processing complete!\nOutput saved to: {output_file}")
        msg_box.setWindowTitle("Success")
        msg_box.exec_()
        self.progress_bar.setValue(100)

    def handle_error(self, error):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(error)
        msg_box.setWindowTitle("Error")
        msg_box.exec_()
        self.progress_bar.setValue(0)

    def cancel_processing(self):
        if self.extraction_thread and self.extraction_thread.isRunning():
            self.extraction_thread.stop()
            self.extraction_thread.quit()
            self.extraction_thread.wait()

        if self.gemini_thread and self.gemini_thread.isRunning():
            self.gemini_thread.stop()
            self.gemini_thread.quit()
            self.gemini_thread.wait()

        self.set_processing_state(False)
        self.status_display.append("<font color='#e74c3c'>Processing cancelled by user</font>")
        self.progress_bar.setValue(0)

    def select_local_folder(self):
        """Let user select a folder containing transcript files"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder Containing Transcript Files",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder_path:
            self.folder_input.setText(folder_path)
            # Clear URL input when folder is selected
            self.url_input.clear()

    def on_url_input_changed(self, text):
        """Clear folder input when URL is entered"""
        if text.strip():
            self.folder_input.clear()

    def on_folder_input_changed(self, text):
        """Clear URL input when folder is selected"""
        if text.strip():
            self.url_input.clear()

    def select_transcript_output_file(self):
        self.select_output_file("Select Transcript Output File", self.transcript_file_input)

    def select_gemini_output_file(self):
        self.select_output_file("Select Gemini Output File", self.gemini_file_input)

    def select_output_file(self, title, field):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, title, "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            if not (file_path.endswith(".txt") ):
                file_path += ".txt"  # Default to .txt if no extension is given
            field.setText(file_path)

    def autofill_from_env(self):
        """Auto-fill form fields using values from the .env file (except playlist URL)"""
        try:
            # Load environment variables fresh from .env file
            load_dotenv(".env", override=True)
            
            # Count how many fields will be filled
            filled_count = 0
            
            # Language
            language = os.environ.get("LANGUAGE", "")
            if language:
                self.language_input.setText(language)
                filled_count += 1
            
            # API Key
            api_key = os.environ.get("API_KEY", "")
            if api_key:
                self.api_key_input.setText(api_key)
                filled_count += 1
            
            # File paths (if they exist in env)
            transcript_file = os.environ.get("TRANSCRIPT_OUTPUT_FILE", "")
            if transcript_file:
                self.transcript_file_input.setText(transcript_file)
                filled_count += 1
            
            gemini_file = os.environ.get("GEMINI_OUTPUT_FILE", "")
            if gemini_file:
                self.gemini_file_input.setText(gemini_file)
                filled_count += 1
            
            # Refinement style
            refinement_style = os.environ.get("REFINEMENT_STYLE", "")
            if refinement_style and refinement_style in self.prompts:
                self.category_combo.setCurrentText(refinement_style)
                self.selected_category = refinement_style
                filled_count += 1
            
            # Chunk size
            chunk_size = os.environ.get("CHUNK_SIZE", "")
            if chunk_size:
                try:
                    chunk_size_int = int(chunk_size)
                    if 2000 <= chunk_size_int <= 50000:  # Within slider range
                        self.chunk_size_slider.setValue(chunk_size_int)
                        self.update_chunk_size_label(chunk_size_int)
                        filled_count += 1
                except ValueError:
                    pass  # Invalid chunk size, skip
            
            # Model selection
            model_name = os.environ.get("GEMINI_MODEL", "")
            if model_name and model_name in self.available_models:
                self.selected_model_name = model_name
                filled_count += 1
            
            # Show success message
            if filled_count > 0:
                msg_box = QMessageBox()
                msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setText(f"Successfully auto-filled {filled_count} field(s) from .env file!")
                msg_box.setWindowTitle("Auto-fill Complete")
                msg_box.exec_()
                
                # Update status display
                self.status_display.append(f"<font color='#9b59b6'>✅ Auto-filled {filled_count} fields from .env file</font>")
            else:
                msg_box = QMessageBox()
                msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText("No values found in .env file to auto-fill.\n\nMake sure your .env file exists and contains the required variables.")
                msg_box.setWindowTitle("Auto-fill Warning")
                msg_box.exec_()
                
        except Exception as e:
            # Show error message
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText(f"Error reading .env file: {str(e)}")
            msg_box.setWindowTitle("Auto-fill Error")
            msg_box.exec_()

    def select_transcript_source(self):
        """Ask user whether to download transcripts or use local files"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Transcript Source")
        dialog.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Choose transcript source:")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Select how you want to obtain transcripts for processing:")
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        download_button = QPushButton("📥 Download from YouTube")
        download_button.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        download_button.setToolTip("Download transcripts from YouTube URLs (requires playlist/video URL)")
        
        local_button = QPushButton("📁 Use Local Files")
        local_button.setStyleSheet(self.get_button_style("#e67e22", "#d35400"))
        local_button.setToolTip("Process existing transcript files from a folder")
        
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.setStyleSheet(self.get_button_style("#95a5a6", "#7f8c8d"))
        
        button_layout.addWidget(download_button)
        button_layout.addWidget(local_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        result = {"choice": ""}
        
        def on_download():
            result["choice"] = "download"
            dialog.accept()
        
        def on_local():
            result["choice"] = "local"
            dialog.accept()
        
        def on_cancel():
            result["choice"] = ""
            dialog.reject()
        
        download_button.clicked.connect(on_download)
        local_button.clicked.connect(on_local)
        cancel_button.clicked.connect(on_cancel)
        
        dialog.exec_()
        return result["choice"] if result["choice"] else None

    def select_transcript_folder(self):
        """Let user select a folder containing transcript files"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder Containing Transcript Files",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        return folder_path if folder_path else None

    def process_local_transcripts(self, folder_path, output_file):
        """Process existing transcript files from a folder"""
        try:
            import glob
            
            # Find all .txt files in the folder
            txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
            
            if not txt_files:
                msg_box = QMessageBox()
                msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText(f"No .txt files found in the selected folder:\n{folder_path}")
                msg_box.setWindowTitle("No Files Found")
                msg_box.exec_()
                self.set_processing_state(False)
                return
            
            self.status_display.append(f"<font color='#e67e22'>📁 Found {len(txt_files)} transcript files in folder</font>")
            self.status_display.append(f"<font color='#e67e22'>📂 Folder: {folder_path}</font>")
            
            # Create a combined transcript file
            self.status_display.append("<font color='#3498db'>🔄 Combining transcript files...</font>")
            
            with open(output_file, 'w', encoding='utf-8') as combined_file:
                combined_file.write(f"Local Transcript Files from: {folder_path}\n\n")
                
                for i, file_path in enumerate(txt_files, 1):
                    filename = os.path.basename(file_path)  # Define filename at the start
                    try:
                        self.status_display.append(f"<font color='#3498db'>Processing file {i}/{len(txt_files)}: {filename}</font>")
                        
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        # Write in the same format as YouTube transcripts
                        combined_file.write(f"Video URL: Local File - {filename}\n")
                        combined_file.write(content + '\n\n')
                        
                        # Update progress
                        progress = int((i / len(txt_files)) * 100)
                        self.progress_bar.setValue(progress)
                        
                    except Exception as file_error:
                        self.status_display.append(f"<font color='#e74c3c'>⚠️ Error reading {filename}: {str(file_error)}</font>")
                        continue
            
            self.status_display.append(f"<font color='#2ecc71'>✅ Successfully combined {len(txt_files)} files into {output_file}</font>")
            
            # Start Gemini processing directly
            self.start_gemini_processing(output_file)
            
        except Exception as e:
            self.handle_error(f"Error processing local transcripts: {str(e)}")


class TranscriptExtractionThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    extraction_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, playlist_url, output_file):
        super().__init__()
        self.playlist_url = playlist_url
        self.output_file = output_file
        self._is_running = True

    def run(self):
        try:
            url = self.playlist_url

            # Initialize YouTube Transcript API
            self.status_update.emit("Using direct connection for transcript access...")
            ytt_api = YouTubeTranscriptApi()

            if "playlist?list=" in url:
                playlist = Playlist(url)
                video_urls = playlist.video_urls
                total_videos = len(video_urls)
                playlist_name = playlist.title
            elif "watch?v=" in url:
                video_urls = [url]
                total_videos = 1
                playlist_name = "Single Video"
            else:
                # Handle invalid URL case
                self.error_occurred.emit("Invalid URL provided. Please use a valid YouTube video or playlist URL.")
                return

            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(f"Playlist Name: {playlist_name}\n\n")
                for index, video_url in enumerate(video_urls, 1):
                    if not self._is_running:
                        return

                    try:
                        video_id = video_url.split("?v=")[1].split("&")[0]
                        fetched_transcript = None  # Initialize for this video

                        # Enhanced transcript extraction with retry logic
                        max_retries = 3
                        retry_delay = 2
                        
                        for attempt in range(max_retries):
                            try:
                                if attempt > 0:
                                    self.status_update.emit(f"Retry attempt {attempt + 1}/{max_retries} for video {index}/{total_videos}")
                                    time.sleep(retry_delay + random.uniform(1, 3))  # Random delay
                                
                                # 1. Get the list of all available transcripts using the configured API
                                transcript_list_obj = ytt_api.list_transcripts(video_id)

                                # 2. Try to find and fetch English first
                                try:
                                    transcript_object = transcript_list_obj.find_transcript(['en'])
                                    self.status_update.emit(f"Found English transcript for video {index}/{total_videos}. Fetching...")
                                    fetched_transcript = transcript_object.fetch()
                                    break  # Success, exit retry loop
                                
                                # 3. If English is not found, fallback to the first available transcript
                                except NoTranscriptFound:
                                    self.status_update.emit(f"English not found for video {index}/{total_videos}. Trying fallback...")
                                    # Get the first transcript object from the list
                                    first_transcript_object = next(iter(transcript_list_obj))
                                    self.status_update.emit(f"Found fallback: '{first_transcript_object.language}'. Fetching...")
                                    fetched_transcript = first_transcript_object.fetch()
                                    break  # Success, exit retry loop
                                    
                            except Exception as fetch_error:
                                error_msg = str(fetch_error)
                                if "blocking requests" in error_msg or "IP" in error_msg:
                                    if attempt < max_retries - 1:
                                        self.status_update.emit(f"IP blocked for video {index}/{total_videos}, waiting before retry...")
                                        time.sleep(retry_delay * (attempt + 2))  # Exponential backoff
                                        continue
                                    else:
                                        self.status_update.emit(f"Failed after {max_retries} attempts for video {index}/{total_videos}: IP blocked")
                                        break
                                else:
                                    # Other error, don't retry
                                    raise fetch_error
                        
                        # 4. If we successfully got a transcript, process and write it
                        if fetched_transcript:
                            transcript = ' '.join([segment.text for segment in fetched_transcript])
                            f.write(f"Video URL: {video_url}\n")
                            f.write(transcript + '\n\n')
                            self.status_update.emit(f"✅ Extracted transcript for video {index}/{total_videos}")
                        else:
                            self.status_update.emit(f"⚠️ Could not extract transcript for video {index}/{total_videos} ({video_url})")

                        progress_percent = int((index / total_videos) * 100)
                        self.progress_update.emit(progress_percent)
                        
                        # Add a small delay between videos to avoid rate limiting
                        if index < total_videos:
                            time.sleep(random.uniform(1, 2))

                    # 5. This 'except' catches if a video has NO transcripts at all
                    except NoTranscriptFound:
                        self.status_update.emit(f"❌ No transcripts available for video {index}/{total_videos} ({video_url})")
                    except Exception as video_error:
                        error_msg = str(video_error)
                        if "blocking requests" in error_msg:
                            self.status_update.emit(f"🚫 IP blocked for video {index}/{total_videos} - Consider waiting longer between batches")
                        else:
                            self.status_update.emit(f"❌ Error processing {video_url}: {error_msg}")
                            
                        # If we're getting blocked, suggest stopping
                        if "blocking requests" in error_msg and index > 5:  # After 5 videos
                            self.status_update.emit("⚠️ Multiple IP blocks detected. Consider stopping and waiting 30+ minutes before continuing.")
                            self.status_update.emit("💡 Tip: Process videos in smaller batches (10-20 at a time) with longer delays between batches.")

            self.extraction_complete.emit(self.output_file)
        except Exception as e:
            self.error_occurred.emit(f"Extraction error: {str(e)}")

    def stop(self):
        self._is_running = False


class GeminiProcessingThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    processing_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    DEFAULT_CHUNK_SIZE = 3000
    

    def __init__(self, input_file, output_file, api_key, selected_model_name, output_language, chunk_size,prompt): 
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.selected_model_name = selected_model_name # Store selected model name
        self.output_language = output_language # Store output language
        self.prompt = prompt
        self._is_running = True
        logging.basicConfig(filename='gemini_processing.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


    def run(self):
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)  # type: ignore
            video_chunks = self.split_videos(self.input_file) # input_file is transcript file path
            final_output_path = self.output_file
            response_file_path = self.output_file.replace(".txt", "_temp_response.txt")
            total_videos = len(video_chunks) -1 if len(video_chunks) > 1 else 0 # Calculate total videos for progress

            with open(response_file_path, "w", encoding="utf-8") as response_file:
                response_file.write("")

            for video_index, video_chunk in enumerate(video_chunks[1:]): # Start from 1 to skip empty chunk
                if not self._is_running: # Check for stop signal
                    return
                self.status_update.emit(f"\nProcessing Video {video_index + 1}/{total_videos}: Preview: {video_chunk[:50]}...")
                word_count = len(video_chunk.split())
                self.status_update.emit(f"Word Count: {word_count} words")
                self.status_update.emit(f"Chunk Size: {self.chunk_size} words")
                

                video_transcript_chunks = self.split_text_into_chunks(video_chunk, self.chunk_size)
                previous_response = ""
                for chunk_index, chunk in enumerate(video_transcript_chunks):
                    if not self._is_running: # Check for stop signal inside inner loop
                        return
                    if previous_response:
                        context_prompt = (
                            "The following text is a continuation... "
                            f"Previous response:\n{previous_response}\n\nNew text to process(Do Not Repeat the Previous response:):\n"
                        )
                    else:
                        context_prompt = ""

                    # Replace [Language] with user specified language
                    formatted_prompt = self.prompt.replace("[Language]", self.output_language)
                    full_prompt = f"{context_prompt}{formatted_prompt}\n\n{chunk}"
                    model = genai.GenerativeModel(model_name=self.selected_model_name)  # type: ignore

                    self.status_update.emit(f"Generating Gemini response for Video {video_index + 1}/{total_videos}, Chunk {chunk_index + 1}/{len(video_transcript_chunks)}, please wait...")
                    response = model.generate_content(full_prompt)

                    with open(response_file_path, "a", encoding="utf-8") as response_file:
                        response_file.write(response.text + "\n\n")
                    previous_response = response.text
                    self.status_update.emit(f"Chunk {chunk_index + 1}/{len(video_transcript_chunks)} processed and saved to temp file.")

                self.status_update.emit(f"All Gemini responses for video {video_index + 1} have been saved to temp file.")

                with open(response_file_path, "r", encoding="utf-8") as response_file:
                    video_response_content = response_file.read()

                with open(final_output_path, "a", encoding="utf-8") as final_output_file:
                    final_output_file.write(f"Video URL: {video_chunks[video_index+1].splitlines()[0].replace('Video URL: ', '')}\n") # Add Video URL as heading
                    final_output_file.write(video_response_content + "\n\n")

                with open(response_file_path, "w", encoding="utf-8") as response_file:
                    response_file.write("") # Clear temp file

                progress_percent = int(((video_index + 1) / total_videos) * 100) if total_videos > 0 else 100 # Calculate Gemini progress
                self.progress_update.emit(progress_percent) # Emit Gemini progress
                self.status_update.emit(f"Final Gemini output for video {video_index + 1} appended to {final_output_path}")

            self.status_update.emit(f"All Gemini responses for all videos have been saved to {final_output_path}.")
            self.processing_complete.emit(final_output_path)
            self.progress_update.emit(100) # Ensure progress bar reaches 100% at the end
        except Exception as e:
            error_message = f"Gemini error: {str(e)}"
            self.error_occurred.emit(error_message)
            logging.error(error_message)


    def split_text_into_chunks(self, text, chunk_size, min_chunk_size=500):
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        if len(chunks) > 1 and len(chunks[-1].split()) < min_chunk_size:
            chunks[-2] += " " + chunks[-1]
            chunks.pop()
        return chunks

    def split_videos(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        video_chunks = re.split(r'(?=Video URL:)', content) # Split by Video URL: from transcript file
        video_chunks = [chunk.strip() for chunk in video_chunks if chunk.strip()]
        return video_chunks

    def stop(self):
        self._is_running = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())