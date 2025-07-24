"""
Data models and classes for the YouTube Transcript Extractor application.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class ProcessingMode(Enum):
    """Enumeration for different processing modes."""
    YOUTUBE_URL = "youtube_url"
    LOCAL_FOLDER = "local_folder"


class RefinementStyle(Enum):
    """Enumeration for different refinement styles."""
    BALANCED_DETAILED = "Balanced and Detailed"
    SUMMARY = "Summary"
    EDUCATIONAL = "Educational"
    NARRATIVE_REWRITING = "Narrative Rewriting"
    QA_GENERATION = "Q&A Generation"


@dataclass
class ProcessingConfig:
    """Configuration for processing transcripts."""
    mode: ProcessingMode
    source_path: str  # URL for YouTube, folder path for local
    output_language: str
    refinement_style: RefinementStyle
    chunk_size: int
    gemini_model: str
    api_key: str
    transcript_output_file: str
    gemini_output_file: str


@dataclass
class TranscriptVideo:
    """Represents a single video transcript."""
    url: str
    title: Optional[str]
    content: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class ProcessingProgress:
    """Represents the progress of a processing operation."""
    current_item: int
    total_items: int
    current_operation: str
    percentage: int
    message: str


@dataclass
class ProcessingResult:
    """Represents the result of a processing operation."""
    success: bool
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    videos_processed: int = 0
    total_videos: int = 0
    content: Optional[str] = None


class ProcessingPrompts:
    """Container for all processing prompts."""
    
    PROMPTS = {
        RefinementStyle.BALANCED_DETAILED: """Turn the following unorganized transcript text into a well-structured, readable format while retaining EVERY detail, context, and nuance of the original content.
    Refine the transcript to improve clarity, grammar, and coherence WITHOUT cutting, summarizing, or omitting any information.
    The goal is to make the transcript content easier to read and process by:

    - Organizing the content into logical sections with appropriate subheadings.
    - Using bullet points or numbered lists where applicable to present facts, stats, or comparisons.
    - Highlighting key terms, names, or headings with **bold** text for emphasis.
    - Preserving the original tone, humor, and narrative style while ensuring readability.
    - Adding clear separators or headings for topic shifts to improve navigation.

    Ensure the transcript remains informative, capturing the original intent, tone, and details while presenting the information in a format optimized for analysis by both humans and AI.
    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized transcript text in your response.

    Transcript Text:""",

        RefinementStyle.SUMMARY: """Summarize the following transcript into a concise and informative summary. 
    Identify the core message, main arguments, and key pieces of information presented in the video.
    The summary should capture the essence of the video's content in a clear and easily understandable way.
    Aim for a summary that is shorter than the original transcript but still accurately reflects its key points.  
    Focus on conveying the most important information and conclusions.

    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text in your response.

    Text:""",

        RefinementStyle.EDUCATIONAL: """Transform the following transcript into a comprehensive educational text, resembling a textbook chapter. Structure the content with clear headings, subheadings, and bullet points to enhance readability and organization for educational purposes.

    Crucially, identify any technical terms, jargon, or concepts that are mentioned but not explicitly explained within the transcript. For each identified term, provide a concise definition (no more than two sentences) formatted as a blockquote. Integrate these definitions strategically within the text, ideally near the first mention of the term, to enhance understanding without disrupting the flow.

    Ensure the text is highly informative, accurate, and retains all the original details and nuances of the transcript. The goal is to create a valuable educational resource that is easy to study and understand. You can create and include diagrams using Mermaid.js syntax to illustrate complex concepts or processes. Whenever you add a diagram, wrap the ```mermaid code block inside `<div align="center">` and `</div>`, start the block with a descriptive `%% Figure 1 - Title` (or nested `%% Figure 1.1 - Title` when context requires), keep diagrams concise (≤ 15 nodes), and follow each diagram with one-to-two explanatory sentences.

    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized transcript text in your response.

    Transcript:""",

        RefinementStyle.NARRATIVE_REWRITING: """Rewrite the following transcript into an engaging narrative or story format. Transform the factual or conversational content into a more captivating and readable piece, similar to a short story or narrative article.

    While rewriting, maintain a close adherence to the original subjects and information presented in the video. Do not deviate significantly from the core topics or introduce unrelated elements. The goal is to enhance engagement and readability through storytelling techniques without altering the fundamental content or message of the video. Use narrative elements like descriptive language, scene-setting (if appropriate), and a compelling flow to make the information more accessible and enjoyable.

    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized transcript text in your response.

    Transcript:""",

        RefinementStyle.QA_GENERATION: """Generate a set of questions and answers based on the following transcript for self-assessment or review. For each question, create a corresponding answer.

    Format each question as a level-3 heading using Markdown syntax (### Question Text). Immediately following each question, provide the answer. This format is designed for foldable sections, allowing users to easily hide and reveal answers for self-testing.

    Ensure the questions are relevant to the key information and concepts in the transcript and that the answers are accurate and comprehensive based on the video content.

    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized transcript text in your response.

    Transcript:"""
    }

    CATEGORY_CHUNK_SIZES = {
        RefinementStyle.BALANCED_DETAILED: 3000,
        RefinementStyle.SUMMARY: 10000,
        RefinementStyle.EDUCATIONAL: 3000,
        RefinementStyle.NARRATIVE_REWRITING: 5000,
        RefinementStyle.QA_GENERATION: 3000
    }

    @classmethod
    def get_prompt(cls, style: RefinementStyle) -> str:
        """Get the prompt for a specific refinement style."""
        return cls.PROMPTS.get(style, cls.PROMPTS[RefinementStyle.BALANCED_DETAILED])

    @classmethod
    def get_default_chunk_size(cls, style: RefinementStyle) -> int:
        """Get the default chunk size for a specific refinement style."""
        return cls.CATEGORY_CHUNK_SIZES.get(style, 3000)


class GeminiModels:
    """Container for available Gemini models."""
    
    AVAILABLE_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.0-flash", 
        "gemini-2.0-flash-thinking-exp-01-21",
        "gemini-2.5-flash-lite-preview-06-17",
        "gemini-2.5-pro-preview-03-25",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    DEFAULT_MODEL = "gemini-2.5-flash"

    @classmethod
    def get_models(cls) -> List[str]:
        """Get list of available models."""
        return cls.AVAILABLE_MODELS.copy()

    @classmethod
    def get_default_model(cls) -> str:
        """Get the default model."""
        return cls.DEFAULT_MODEL
