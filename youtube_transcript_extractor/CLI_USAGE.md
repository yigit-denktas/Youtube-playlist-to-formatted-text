# CLI Usage Guide

## Installation

### Development Mode

```bash
cd youtube_transcript_extractor
pip install -e .
```

### Production Mode

```bash
cd youtube_transcript_extractor
pip install .
```

## Quick Start

1. **Initial Setup**

   ```bash
   youtube-transcript-extractor setup --interactive
   ```

2. **Process a Playlist**

   ```bash
   youtube-transcript-extractor process "https://youtube.com/playlist?list=YOUR_PLAYLIST_ID"
   ```

3. **Check Progress**

   ```bash
   youtube-transcript-extractor list-jobs
   ```

## Commands

### `process` - Main Processing Command

Process a YouTube playlist or single video and generate formatted transcripts.

```bash
youtube-transcript-extractor process [OPTIONS] URL
```

**Options:**

- `--output, -o PATH`: Output directory (default: outputs)
- `--formats, -f TEXT`: Export formats, comma-separated (default: markdown,html)
- `--language, -l TEXT`: Target language for transcripts
- `--style, -s [summary|detailed|educational|technical]`: Refinement style
- `--workers, -w INTEGER`: Number of concurrent workers (default: 3)
- `--chunk-size INTEGER`: Text chunk size for processing (default: 3000)
- `--model [gemini-1.5-flash|gemini-1.5-pro]`: Gemini model to use
- `--dry-run`: Show what would be processed without actually processing

**Examples:**

```bash
# Basic usage
youtube-transcript-extractor process "https://youtube.com/playlist?list=PLExample"

# Custom output directory and formats
youtube-transcript-extractor process "https://youtube.com/playlist?list=PLExample" \
  --output "./my-transcripts" \
  --formats "markdown,pdf,html"

# Educational style with more workers
youtube-transcript-extractor process "https://youtube.com/playlist?list=PLExample" \
  --style educational \
  --workers 5 \
  --language "Spanish"

# Dry run to see what would be processed
youtube-transcript-extractor process "https://youtube.com/playlist?list=PLExample" --dry-run
```

### `list-jobs` - Show Jobs

List resumable and completed jobs with status information.

```bash
youtube-transcript-extractor list-jobs [OPTIONS]
```

**Options:**

- `--status [active|completed|failed|all]`: Filter jobs by status (default: all)
- `--limit INTEGER`: Maximum number of jobs to show (default: 10)

**Examples:**

```bash
# Show all jobs
youtube-transcript-extractor list-jobs

# Show only active jobs
youtube-transcript-extractor list-jobs --status active

# Show last 5 completed jobs
youtube-transcript-extractor list-jobs --status completed --limit 5
```

### `resume` - Resume Interrupted Job

Resume a previously interrupted processing job.

```bash
youtube-transcript-extractor resume [OPTIONS] JOB_ID
```

**Options:**

- `--force`: Force resume even if job appears completed

**Examples:**

```bash
# Resume job by partial ID
youtube-transcript-extractor resume abc123

# Force resume a job
youtube-transcript-extractor resume abc123 --force
```

### `config` - Configuration Management

Show and manage configuration settings.

```bash
youtube-transcript-extractor config [OPTIONS]
```

**Options:**

- `--show-api-key`: Show current API key (masked)
- `--show-all`: Show all configuration values

**Examples:**

```bash
# Show basic configuration
youtube-transcript-extractor config

# Show API key status
youtube-transcript-extractor config --show-api-key

# Show full configuration
youtube-transcript-extractor config --show-all
```

### `setup` - Initial Setup Wizard

Initial setup wizard for first-time users.

```bash
youtube-transcript-extractor setup [OPTIONS]
```

**Options:**

- `--interactive`: Interactive setup wizard

**Examples:**

```bash
# Quick setup check
youtube-transcript-extractor setup

# Interactive setup wizard
youtube-transcript-extractor setup --interactive
```

## Global Options

These options work with any command:

- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress non-essential output
- `--version`: Show version information
- `--help`: Show help message

## Configuration

### Environment Variables

The CLI respects these environment variables:

- `API_KEY`: Gemini API key
- `LANGUAGE`: Default output language
- `REFINEMENT_STYLE`: Default refinement style
- `CHUNK_SIZE`: Default chunk size for processing
- `GEMINI_MODEL`: Default Gemini model
- `TRANSCRIPT_OUTPUT_FILE`: Default transcript output file
- `GEMINI_OUTPUT_FILE`: Default Gemini output file

### Configuration Files

Configuration is managed through:

1. **Secure Storage**: API keys are stored securely using the system keyring
2. **Environment Files**: `.env` file in the working directory
3. **CLI Options**: Override defaults with command-line options

### API Key Setup

Get your Gemini API key:

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Run the interactive setup: `youtube-transcript-extractor setup --interactive`

## Output Formats

Supported export formats:

- **markdown**: Structured markdown files
- **html**: Styled HTML pages
- **pdf**: PDF documents (requires additional dependencies)
- **docx**: Word documents
- **txt**: Plain text files

## Progress and Status

### Progress Indication

- Real-time progress bars during processing
- Colored status messages
- Time elapsed information

### Job Persistence

- Jobs are automatically saved and can be resumed
- View job history with `list-jobs`
- Resume interrupted jobs with `resume`

### Error Handling

- Clear error messages with suggested fixes
- Automatic retry for transient failures
- Graceful handling of interruptions

## Examples

### Complete Workflow

```bash
# 1. Initial setup
youtube-transcript-extractor setup --interactive

# 2. Process a playlist
youtube-transcript-extractor process \
  "https://youtube.com/playlist?list=PLrAXtmRdnEQy" \
  --formats "markdown,html,pdf" \
  --style educational \
  --language "English" \
  --workers 4

# 3. Check results
ls outputs/

# 4. View job status
youtube-transcript-extractor list-jobs

# 5. If interrupted, resume
youtube-transcript-extractor resume abc123
```

### Batch Processing

```bash
# Process multiple playlists
for playlist in "PLExample1" "PLExample2" "PLExample3"; do
  youtube-transcript-extractor process \
    "https://youtube.com/playlist?list=$playlist" \
    --output "./batch-output/$playlist"
done
```

### Custom Configuration

```bash
# Create custom .env file
cat > .env << EOF
API_KEY=your_gemini_api_key_here
LANGUAGE=Spanish
REFINEMENT_STYLE=Educational and Detailed
CHUNK_SIZE=4000
GEMINI_MODEL=gemini-1.5-pro
EOF

# Process with custom config
youtube-transcript-extractor process "https://youtube.com/playlist?list=PLExample"
```

## Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues**

   ```bash
   youtube-transcript-extractor setup --interactive
   ```

3. **Permission Errors**

   ```bash
   # Check output directory permissions
   ls -la outputs/
   ```

4. **Network Issues**

   ```bash
   # Retry with fewer workers
   youtube-transcript-extractor process URL --workers 1
   ```

### Verbose Mode

For debugging, use verbose mode:

```bash
youtube-transcript-extractor --verbose process URL
```

### Log Files

Check log files for detailed information:

- `yte_cli.log`: CLI operations
- `yte_enhanced.log`: Processing operations

## Aliases

For convenience, you can use the short alias:

```bash
# These are equivalent
youtube-transcript-extractor process URL
yte process URL
```

## Integration

### Shell Scripts

```bash
#!/bin/bash
# process_playlists.sh

PLAYLISTS=(
  "PLExample1"
  "PLExample2"
  "PLExample3"
)

for playlist in "${PLAYLISTS[@]}"; do
  echo "Processing playlist: $playlist"
  youtube-transcript-extractor process \
    "https://youtube.com/playlist?list=$playlist" \
    --output "./output/$playlist" \
    --formats "markdown,html"
done
```

### Python Integration

```python
import subprocess
import sys

def process_playlist(url, output_dir="outputs"):
    """Process playlist using CLI."""
    cmd = [
        sys.executable, "-m", "youtube_transcript_extractor.src.cli",
        "process", url,
        "--output", output_dir,
        "--formats", "markdown,html"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```
