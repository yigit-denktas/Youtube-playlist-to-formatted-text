"""
Tests for the exporters module.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from pathlib import Path
from youtube_transcript_extractor.src.core.exporters import (
    ExporterBase, MarkdownExporter, PDFExporter, DocxExporter, 
    HTMLExporter, ExportManager
)


@pytest.mark.unit
class TestExporterBase:
    """Tests for ExporterBase abstract class."""
    
    def test_cannot_instantiate_directly(self):
        """Test that ExporterBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ExporterBase()   # type: ignore[abstract]


@pytest.mark.unit
class TestMarkdownExporter:
    """Tests for MarkdownExporter class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.exporter = MarkdownExporter()
        self.sample_content = """Video URL: https://www.youtube.com/watch?v=example1
This is a sample transcript for the first video.
It contains multiple sentences and paragraphs.

Video URL: https://www.youtube.com/watch?v=example2
This is another sample transcript for the second video.
It also contains content that can be processed."""
    
    def test_init(self):
        """Test MarkdownExporter initialization."""
        assert self.exporter is not None
        assert hasattr(self.exporter, 'logger')
    
    def test_get_file_extension(self):
        """Test getting file extension."""
        assert self.exporter.get_file_extension() == ".md"
    
    def test_is_available(self):
        """Test availability check."""
        assert self.exporter.is_available() is True
    
    def test_export_success(self, temp_dir):
        """Test successful export to markdown."""
        output_path = Path(temp_dir) / "test_output.md"
        metadata = {
            "title": "Test Document",
            "source_url": "https://example.com",
            "language": "English"
        }
        
        result = self.exporter.export(self.sample_content, output_path, metadata)
        
        assert result is True
        assert output_path.exists()
        
        # Check content
        content = output_path.read_text(encoding='utf-8')
        assert "# Test Document" in content
        assert "https://www.youtube.com/watch?v=example1" in content
        assert "This is a sample transcript" in content
    
    def test_export_without_extension(self, temp_dir):
        """Test export adds .md extension if missing."""
        output_path = Path(temp_dir) / "test_output"
        
        result = self.exporter.export(self.sample_content, output_path)
        
        assert result is True
        expected_path = Path(temp_dir) / "test_output.md"
        assert expected_path.exists()
    
    def test_export_wrong_extension(self, temp_dir):
        """Test export corrects wrong extension."""
        output_path = Path(temp_dir) / "test_output.txt"
        
        result = self.exporter.export(self.sample_content, output_path)
        
        assert result is True
        expected_path = Path(temp_dir) / "test_output.md"
        assert expected_path.exists()
    
    def test_export_creates_directories(self, temp_dir):
        """Test export creates necessary directories."""
        output_path = Path(temp_dir) / "subdir" / "test_output.md"
        
        result = self.exporter.export(self.sample_content, output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.parent.exists()
    
    def test_format_markdown_content_with_metadata(self):
        """Test formatting markdown content with metadata."""
        metadata = {
            "title": "Test Document",
            "source_url": "https://example.com",
            "language": "English",
            "date": "2024-01-01"
        }
        

        formatted = self.exporter._format_markdown_content(self.sample_content, metadata)
        
        assert "# Test Document" in formatted
        assert "**Source URL:** https://example.com" in formatted
        assert "**Language:** English" in formatted
        assert "**Date:** 2024-01-01" in formatted
    
    def test_format_markdown_content_without_metadata(self):
        """Test formatting markdown content without metadata."""
        formatted = self.exporter._format_markdown_content(self.sample_content)
        
        assert "# YouTube Transcript Export" in formatted
        assert "## Video 1" in formatted
        assert "🎥 [https://www.youtube.com/watch?v=example1]" in formatted
    
    def test_generate_table_of_contents(self):
        """Test table of contents generation."""
        content_lines = [
            "# Main Title",
            "Some content",
            "## Section 1", 
            "More content",
            "## Section 2",
            "Final content"
        ]
        
        toc = self.exporter._generate_table_of_contents(content_lines)
        
        assert "## 📋 Table of Contents" in "\n".join(toc)
        assert "- [Section 1](#section-1)" in "\n".join(toc)
        assert "- [Section 2](#section-2)" in "\n".join(toc)
    
    def test_export_failure_permission_error(self, temp_dir):
        """Test handling of permission errors during export."""
        # Create a file and make parent directory read-only
        output_path = Path(temp_dir) / "readonly" / "test.md"
        output_path.parent.mkdir()
        
        # Make directory read-only (Windows compatible approach)
        try:
            os.chmod(output_path.parent, 0o444)
            result = self.exporter.export(self.sample_content, output_path)
            assert result is False
        except (OSError, PermissionError):
            # Expected on some systems
            pass
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(output_path.parent, 0o777)
            except (OSError, PermissionError):
                pass


@pytest.mark.unit
class TestHTMLExporter:
    """Tests for HTMLExporter class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.exporter = HTMLExporter()
        self.sample_content = """Video URL: https://www.youtube.com/watch?v=example1
This is a sample transcript for the first video."""
    
    def test_init(self):
        """Test HTMLExporter initialization."""
        assert self.exporter is not None
    
    def test_get_file_extension(self):
        """Test getting file extension."""
        assert self.exporter.get_file_extension() == ".html"
    
    def test_is_available(self):
        """Test availability check."""
        assert self.exporter.is_available() is True
    
    def test_export_success(self, temp_dir):
        """Test successful export to HTML."""
        output_path = Path(temp_dir) / "test_output.html"
        metadata = {"title": "Test Document"}
        
        result = self.exporter.export(self.sample_content, output_path, metadata)
        
        assert result is True
        assert output_path.exists()
        
        # Check HTML content
        content = output_path.read_text(encoding='utf-8')
        assert "<!DOCTYPE html>" in content
        assert "<title>YouTube Transcript Export</title>" in content
        assert "https://www.youtube.com/watch?v=example1" in content
    
    def test_escape_html_characters(self):
        """Test HTML character escaping."""
        test_text = "Test <script>alert('xss')</script> & \"quotes\""
        escaped = self.exporter._escape_html(test_text)
        
        assert "&lt;script&gt;" in escaped
        assert "&amp;" in escaped
        assert "&quot;" in escaped
        assert "&#x27;" not in escaped or "'" not in escaped  # Either escaped or original


@pytest.mark.unit
class TestPDFExporter:
    """Tests for PDFExporter class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.exporter = PDFExporter()
    
    def test_init(self):
        """Test PDFExporter initialization."""
        assert self.exporter is not None
    
    def test_get_file_extension(self):
        """Test getting file extension."""
        assert self.exporter.get_file_extension() == ".pdf"
    
    @patch('youtube_transcript_extractor.src.core.exporters.REPORTLAB_AVAILABLE', True)
    def test_is_available_with_reportlab(self):
        """Test availability when ReportLab is available."""
        assert self.exporter.is_available() is True
    
    @patch('youtube_transcript_extractor.src.core.exporters.REPORTLAB_AVAILABLE', False)
    def test_is_available_without_reportlab(self):
        """Test availability when ReportLab is not available."""
        assert self.exporter.is_available() is False
    
    @patch('youtube_transcript_extractor.src.core.exporters.REPORTLAB_AVAILABLE', True)
    @patch('youtube_transcript_extractor.src.core.exporters.SimpleDocTemplate')
    def test_export_success(self, mock_doc_template, temp_dir):
        """Test successful export to PDF."""
        # Mock ReportLab components
        mock_doc = Mock()
        mock_doc_template.return_value = mock_doc
        
        output_path = Path(temp_dir) / "test_output.pdf"
        content = "Test content for PDF export"
        
        result = self.exporter.export(content, output_path)
        
        assert result is True
        mock_doc.build.assert_called_once()
    
    @patch('youtube_transcript_extractor.src.core.exporters.REPORTLAB_AVAILABLE', False)
    def test_export_failure_no_reportlab(self, temp_dir):
        """Test export failure when ReportLab is not available."""
        output_path = Path(temp_dir) / "test_output.pdf" 
        content = "Test content"
        
        result = self.exporter.export(content, output_path)
        
        assert result is False


@pytest.mark.unit
class TestDocxExporter:
    """Tests for DocxExporter class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.exporter = DocxExporter()
    
    def test_init(self):
        """Test DocxExporter initialization."""
        assert self.exporter is not None
    
    def test_get_file_extension(self):
        """Test getting file extension."""
        assert self.exporter.get_file_extension() == ".docx"
    
    @patch('youtube_transcript_extractor.src.core.exporters.DOCX_AVAILABLE', True)
    def test_is_available_with_docx(self):
        """Test availability when python-docx is available."""
        assert self.exporter.is_available() is True
    
    @patch('youtube_transcript_extractor.src.core.exporters.DOCX_AVAILABLE', False)
    def test_is_available_without_docx(self):
        """Test availability when python-docx is not available."""
        assert self.exporter.is_available() is False
    
    @patch('youtube_transcript_extractor.src.core.exporters.DOCX_AVAILABLE', True)
    @patch('youtube_transcript_extractor.src.core.exporters.Document')
    def test_export_success(self, mock_document, temp_dir):
        """Test successful export to DOCX."""
        # Mock python-docx components
        mock_doc = Mock()
        mock_document.return_value = mock_doc
        
        output_path = Path(temp_dir) / "test_output.docx"
        content = "Test content for DOCX export"
        
        result = self.exporter.export(content, output_path)
        
        assert result is True
        mock_doc.save.assert_called_once()


@pytest.mark.unit
class TestExportManager:
    """Tests for ExportManager class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = ExportManager()
    
    def test_init(self):
        """Test ExportManager initialization."""
        assert self.manager is not None
        assert 'markdown' in self.manager.exporters
        assert 'html' in self.manager.exporters
        assert 'pdf' in self.manager.exporters
        assert 'docx' in self.manager.exporters
    
    def test_get_available_formats(self):
        """Test getting available export formats."""
        formats = self.manager.get_available_formats()
        
        assert isinstance(formats, list)
        assert 'markdown' in formats
        assert 'html' in formats
        # PDF and DOCX availability depends on optional dependencies
    
    def test_export_content_success(self, temp_dir):
        """Test successful content export."""
        output_path = Path(temp_dir) / "test_output"
        content = "Test content for export"
        metadata = {"title": "Test Document"}
        
        result = self.manager.export_content(content, 'markdown', output_path, metadata)
        
        assert result is True
        assert (Path(temp_dir) / "test_output.md").exists()
    
    def test_export_content_unknown_format(self, temp_dir):
        """Test export with unknown format."""
        output_path = Path(temp_dir) / "test_output"
        content = "Test content"
        
        result = self.manager.export_content(content, 'unknown', output_path)
        
        assert result is False
    
    def test_export_content_unavailable_format(self, temp_dir):
        """Test export with unavailable format."""
        output_path = Path(temp_dir) / "test_output"
        content = "Test content"
        
        # Mock PDF exporter as unavailable
        with patch.object(self.manager.exporters['pdf'], 'is_available', return_value=False):
            result = self.manager.export_content(content, 'pdf', output_path)
            assert result is False
    
    def test_export_to_multiple_formats(self, temp_dir):
        """Test exporting to multiple formats."""
        base_path = Path(temp_dir) / "test_output"
        content = "Test content for multiple exports"
        formats = ['markdown', 'html']
        
        results = self.manager.export_to_multiple_formats(content, base_path, formats)
        
        assert isinstance(results, dict)
        assert 'markdown' in results
        assert 'html' in results
        assert results['markdown'] is True
        assert results['html'] is True
        
        # Check files were created
        assert (Path(temp_dir) / "test_output.md").exists()
        assert (Path(temp_dir) / "test_output.html").exists()
    
    def test_export_to_multiple_formats_with_unknown(self, temp_dir):
        """Test exporting to multiple formats including unknown format."""
        base_path = Path(temp_dir) / "test_output"
        content = "Test content"
        formats = ['markdown', 'unknown_format']
        
        results = self.manager.export_to_multiple_formats(content, base_path, formats)
        
        assert results['markdown'] is True
        assert results['unknown_format'] is False
    
    def test_get_missing_dependencies(self):
        """Test getting missing dependencies."""
        missing = self.manager.get_missing_dependencies()
        
        assert isinstance(missing, dict)
        # The exact content depends on what's installed
        # but it should be a valid dict structure
        for format_name, packages in missing.items():
            assert isinstance(format_name, str)
            assert isinstance(packages, list)


@pytest.mark.integration
class TestExportersIntegration:
    """Integration tests for exporters."""
    
    def test_full_export_workflow(self, temp_dir, sample_transcript_content):
        """Test complete export workflow with all available formats."""
        manager = ExportManager()
        base_path = Path(temp_dir) / "integration_test"
        
        metadata = {
            "title": "Integration Test",
            "source_url": "https://example.com",
            "language": "English"
        }
        
        available_formats = manager.get_available_formats()
        results = manager.export_to_multiple_formats(
            sample_transcript_content, 
            base_path, 
            available_formats,
            metadata
        )
        
        # All available formats should export successfully
        for format_name in available_formats:
            assert results[format_name] is True
            
            # Check file was created
            exporter = manager.exporters[format_name]
            extension = exporter.get_file_extension()
            expected_file = base_path.with_suffix(extension)
            assert expected_file.exists()
            assert expected_file.stat().st_size > 0


if __name__ == '__main__':
    pytest.main([__file__])
