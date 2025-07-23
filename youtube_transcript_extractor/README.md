# YouTube Transcript Extractor

[![CI Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/user/repo/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-blue)](https://github.com/user/repo)
[![PyPI version](https://badge.fury.io/py/youtube-transcript-extractor.svg)](https://badge.fury.io/py/youtube-transcript-extractor)

> An advanced tool for fetching, processing, and refining YouTube video transcripts with AI-powered summarization and multiple export formats.

## Description

This application provides both a command-line interface (CLI) and a graphical user interface (GUI) to extract transcripts from YouTube videos or playlists. It leverages Google's Gemini AI to refine raw transcripts into summaries, educational content, or Q&A formats, and supports exporting to Markdown, PDF, DOCX, and HTML.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/youtube-transcript-extractor.git
    cd youtube-transcript-extractor
    ```

2. **Install dependencies:**
    It is recommended to use a virtual environment.

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. **Install as a package:**
    To make the CLI commands available system-wide, install the package in editable mode.

    ```bash
    pip install -e .
    ```

## Usage

### Graphical User Interface (GUI)

To launch the GUI, run the `main_window` module directly:

```bash
python -m src.ui.main_window
