"""
Setup script for YouTube Transcript Extractor.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, '..', 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="youtube-transcript-extractor",
    version="2.0.0",
    author="YouTube Transcript Extractor Team",
    author_email="",
    description="A modular application for extracting and refining YouTube transcripts using AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yigit-denktas/Youtube-playlist-to-formatted-text",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        # Development dependencies
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        # Export format dependencies
        "export": [
            "reportlab>=3.6.0",
            "python-docx>=0.8.11",
        ],
        # Security features
        "security": [
            "keyring>=23.0.0",
            "cryptography>=40.0.0",
        ],
        # Async processing features
        "async": [
            "aiohttp>=3.8.0",
            "tenacity>=8.2.0",
        ],
        # All optional features
        "full": [
            "reportlab>=3.6.0",
            "python-docx>=0.8.11",
            "keyring>=23.0.0",
            "cryptography>=40.0.0",
            "aiohttp>=3.8.0",
            "tenacity>=8.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "youtube-transcript-extractor=src.cli_test:main",
            "yte=src.cli_test:main",  # Short alias
        ],
        "gui_scripts": [
            "youtube-transcript-extractor-gui=src.ui.main_window:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["*.py"],
        "src.core": ["*.py"],
        "src.ui": ["*.py"],
        "src.utils": ["*.py"],
    },
    zip_safe=False,
    keywords=[
        "youtube", "transcript", "ai", "gemini", "text-processing", 
        "video", "automation", "education", "accessibility"
    ],
    project_urls={
        "Bug Reports": "https://github.com/yigit-denktas/Youtube-playlist-to-formatted-text/issues",
        "Source": "https://github.com/yigit-denktas/Youtube-playlist-to-formatted-text",
        "Documentation": "https://github.com/yigit-denktas/Youtube-playlist-to-formatted-text/blob/main/README.md",
    },
)
