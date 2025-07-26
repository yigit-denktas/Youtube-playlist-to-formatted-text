"""
Tests for CLI functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from youtube_transcript_extractor.src.cli import cli, YTECli
from youtube_transcript_extractor.src.core.models import RefinementStyle


class TestYTECli:
    """Tests for YTECli class."""
    
    def test_init(self):
        """Test CLI initialization."""
        cli_app = YTECli()
        assert cli_app.config_manager is not None
        assert cli_app.secure_manager is not None
        assert cli_app.job_manager is not None
        assert cli_app.export_manager is not None
    
    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        cli_app = YTECli()
        
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/playlist?list=PLrAXtmRdnEQy4XM6YsJfxrxXgT6KqA0",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            assert cli_app.validate_url(url), f"URL should be valid: {url}"
    
    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        cli_app = YTECli()
        
        invalid_urls = [
            "https://www.google.com",
            "https://vimeo.com/123456",
            "not_a_url",
            ""
        ]
        
        for url in invalid_urls:
            assert not cli_app.validate_url(url), f"URL should be invalid: {url}"
    
    def test_validate_formats_valid(self):
        """Test format validation with valid formats."""
        cli_app = YTECli()
        
        with patch.object(cli_app.export_manager, 'get_available_formats', return_value=['markdown', 'html', 'pdf']):
            formats = cli_app.validate_formats(['markdown', 'html'])
            assert formats == ['markdown', 'html']
    
    def test_validate_formats_invalid(self):
        """Test format validation with invalid formats."""
        cli_app = YTECli()
        
        with patch.object(cli_app.export_manager, 'get_available_formats', return_value=['markdown', 'html', 'pdf']):
            formats = cli_app.validate_formats(['invalid_format'])
            assert formats == ['markdown']  # Falls back to default


class TestCLICommands:
    """Tests for CLI commands."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'YouTube Transcript Extractor' in result.output
    
    def test_cli_version(self):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'v2.0.0' in result.output
    
    def test_process_help(self):
        """Test process command help."""
        result = self.runner.invoke(cli, ['process', '--help'])
        assert result.exit_code == 0
        assert 'Process a YouTube playlist' in result.output
    
    def test_process_invalid_url(self):
        """Test process command with invalid URL."""
        result = self.runner.invoke(cli, ['process', 'https://www.google.com'])
        assert result.exit_code == 1
        assert 'Invalid YouTube URL' in result.output
    
    @patch('youtube_transcript_extractor.src.cli.asyncio.run')
    def test_process_dry_run(self, mock_asyncio_run):
        """Test process command with dry run."""
        result = self.runner.invoke(cli, [
            'process', 
            'https://youtube.com/playlist?list=test',
            '--dry-run'
        ])
        assert result.exit_code == 0
        assert 'DRY RUN' in result.output
        assert not mock_asyncio_run.called
    
    def test_list_jobs_help(self):
        """Test list-jobs command help."""
        result = self.runner.invoke(cli, ['list-jobs', '--help'])
        assert result.exit_code == 0
        assert 'List resumable and completed jobs' in result.output
    
    def test_resume_help(self):
        """Test resume command help."""
        result = self.runner.invoke(cli, ['resume', '--help'])
        assert result.exit_code == 0
        assert 'Resume an interrupted job' in result.output
    
    def test_config_help(self):
        """Test config command help."""
        result = self.runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
        assert 'Show and manage configuration' in result.output
    
    def test_setup_help(self):
        """Test setup command help."""
        result = self.runner.invoke(cli, ['setup', '--help'])
        assert result.exit_code == 0
        assert 'Initial setup wizard' in result.output


class TestConfigManagement:
    """Tests for configuration management in CLI."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
    
    @patch('youtube_transcript_extractor.src.cli.YTECli')
    def test_config_basic(self, mock_cli_class):
        """Test basic config display."""
        mock_cli = MagicMock()
        mock_cli.config_manager.get_auto_fill_data.return_value = {
            'language': 'English',
            'refinement_style': RefinementStyle.SUMMARY,
            'chunk_size': 3000,
            'gemini_model': 'gemini-1.5-flash',
            'api_key': 'test_key'
        }
        mock_cli_class.return_value = mock_cli
        
        result = self.runner.invoke(cli, ['config'])
        assert result.exit_code == 0
        assert 'Configuration Summary' in result.output
    
    @patch('youtube_transcript_extractor.src.cli.YTECli')
    def test_config_show_api_key(self, mock_cli_class):
        """Test config with API key display."""
        mock_cli = MagicMock()
        mock_cli.config_manager.get_api_key.return_value = 'test_api_key_1234567890'
        mock_cli_class.return_value = mock_cli
        
        result = self.runner.invoke(cli, ['config', '--show-api-key'])
        assert result.exit_code == 0
        assert 'test_api_*' in result.output or 'API Key:' in result.output


class TestJobManagement:
    """Tests for job management in CLI."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
    
    @patch('youtube_transcript_extractor.src.cli.YTECli')
    def test_list_jobs_empty(self, mock_cli_class):
        """Test list jobs with no jobs."""
        mock_cli = MagicMock()
        mock_cli.job_manager.get_jobs_by_status.return_value = []
        mock_cli_class.return_value = mock_cli
        
        result = self.runner.invoke(cli, ['list-jobs'])
        assert result.exit_code == 0
        assert 'No jobs found' in result.output
    
    @patch('youtube_transcript_extractor.src.cli.YTECli')
    def test_list_jobs_with_data(self, mock_cli_class):
        """Test list jobs with job data."""
        mock_cli = MagicMock()
        mock_cli.job_manager.get_jobs_by_status.return_value = [
            {
                'id': 'test_job_12345678',
                'source_url': 'https://youtube.com/playlist?list=test',
                'status': 'completed',
                'completed_items': 5,
                'total_items': 5,
                'updated_at': '2024-01-01T10:00:00'
            }
        ]
        mock_cli_class.return_value = mock_cli
        
        result = self.runner.invoke(cli, ['list-jobs'])
        assert result.exit_code == 0
        assert 'test_job' in result.output  # Check for partial ID (table may truncate)
        assert 'completed' in result.output
    
    @patch('youtube_transcript_extractor.src.cli.YTECli')
    def test_resume_job_not_found(self, mock_cli_class):
        """Test resume job that doesn't exist."""
        mock_cli = MagicMock()
        mock_cli.job_manager.get_resumable_jobs.return_value = []
        mock_cli_class.return_value = mock_cli
        
        result = self.runner.invoke(cli, ['resume', 'nonexistent'])
        assert result.exit_code == 1
        assert 'Job not found' in result.output


class TestSetupWizard:
    """Tests for setup wizard functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
    
    @patch('youtube_transcript_extractor.src.cli.YTECli')
    def test_setup_quick(self, mock_cli_class):
        """Test quick setup check."""
        mock_cli = MagicMock()
        mock_cli.config_manager.get_api_key.return_value = 'test_key'
        mock_cli_class.return_value = mock_cli
        
        result = self.runner.invoke(cli, ['setup'])
        assert result.exit_code == 0
        assert 'Setup looks good' in result.output or 'API key configured' in result.output
    
    @patch('youtube_transcript_extractor.src.cli.YTECli')
    @patch('youtube_transcript_extractor.src.cli.Confirm.ask')
    @patch('youtube_transcript_extractor.src.cli.Prompt.ask')
    def test_setup_interactive(self, mock_prompt, mock_confirm, mock_cli_class):
        """Test interactive setup wizard."""
        mock_cli = MagicMock()
        mock_cli.config_manager.get_api_key.return_value = ''
        mock_cli.config_manager.get_language.return_value = 'English'
        mock_cli.config_manager.set_api_key.return_value = True
        mock_cli_class.return_value = mock_cli
        
        # Mock user inputs
        mock_confirm.side_effect = [True, False, False]  # Update API key, don't change language, don't change output dir
        mock_prompt.ask.return_value = 'test_api_key'
        
        result = self.runner.invoke(cli, ['setup', '--interactive'])
        assert result.exit_code == 0
        assert 'Setup completed' in result.output


if __name__ == '__main__':
    pytest.main([__file__])
