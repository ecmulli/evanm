# Jobs Package

A Python package for running scheduled jobs and automation tasks.

## Features

- **Base Job Class**: Abstract base class for creating custom jobs
- **Job Scheduler**: Manages and runs jobs on a schedule
- **Configuration Management**: Environment-based configuration
- **Logging**: Comprehensive logging with configurable levels
- **Example Jobs**: Ready-to-use example implementations

## Quick Start

### Installation

#### Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install in editable mode
uv pip install -e .
```

#### Using pip (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt

# Or using the package manager
python -m pip install -e .
```

### Basic Usage

```bash
# Run scheduler continuously (daemon mode)
python -m jobs

# Run in development mode (more frequent scheduling, debug logging)
python -m jobs --dev

# Run a specific job once
python -m jobs --job hello_world

# Run all jobs once and exit (cron-friendly)
python -m jobs --once

# Run scheduler for 300 seconds then exit
python -m jobs --duration 300

# List all available jobs
python -m jobs --list
```

### Configuration

Copy the example environment file and customize:

```bash
cp .env.example .env
```

Edit `.env` to configure jobs and scheduling:

```env
# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/jobs.log

# Job scheduling
HELLO_SCHEDULE=every(30).seconds
STATUS_SCHEDULE=every(2).minutes

# Job-specific settings
HELLO_MESSAGE=Hello from my custom job!
STATUS_CHECK_URL=https://example.com/health
```

## Creating Custom Jobs

### Step 1: Create a Job Class

```python
from jobs.base_job import BaseJob

class MyCustomJob(BaseJob):
    def __init__(self, config=None):
        super().__init__("my_custom_job", config)
    
    def run(self) -> bool:
        # Your job logic here
        self.logger.info("Running my custom job")
        
        # Return True for success, False for failure
        return True
```

### Step 2: Register the Job

Add your job to `jobs/scheduler.py` in the `_register_jobs` method:

```python
def _register_jobs(self):
    # ... existing jobs ...
    
    # Add your custom job
    from .my_custom_job import MyCustomJob
    custom_job = MyCustomJob(self.config.get("my_custom_job", {}))
    self.register_job(custom_job)
```

### Step 3: Configure Scheduling

Add scheduling configuration to your `.env` file:

```env
MY_CUSTOM_SCHEDULE=every(1).hours
```

## Available Services

This package includes several specialized automation services:

### Notion Sync (`notion/`)
Bidirectional task synchronization between Notion workspaces.
- Syncs tasks between personal hub and external workspaces (Livepeer, Vanquish)
- Maintains workspace labels and external IDs
- Handles property mapping across databases

**Usage:**
```bash
cd notion
python notion_sync.py --mode full
```

See [notion/README.md](notion/README.md) for details.

### Motion Sync (`motion/`)
Bidirectional synchronization between Motion AI and Notion.
- Syncs tasks between Notion and Motion's AI-powered scheduling
- Handles priority and status mapping
- Supports multiple workspaces

**Usage:**
```bash
cd motion
python motion_sync.py --mode full
```

See [motion/README.md](motion/README.md) for details.

### Notion Calendar Auto-Scheduler (`scheduler/`) ✨ NEW
Automatically schedules Notion tasks into calendar time slots with continuous rescheduling.
- Schedules tasks based on priority ranking
- 15-minute time slots during work hours (9am-5pm, Mon-Fri)
- Automatically reschedules incomplete tasks
- Integrates directly with Notion Calendar app

**Usage:**
```bash
cd scheduler
python calendar_scheduler.py --mode continuous
```

See [scheduler/README.md](scheduler/README.md) and [scheduler/SETUP.md](scheduler/SETUP.md) for details.

### Available Jobs

### Hello World Job
- **Name**: `hello_world`
- **Purpose**: Simple example that prints a message
- **Configuration**: 
  - `HELLO_MESSAGE`: Message to print
  - `HELLO_JOB_ENABLED`: Enable/disable the job

### Status Check Job
- **Name**: `status_check`
- **Purpose**: Checks if a URL is responding
- **Configuration**:
  - `STATUS_CHECK_URL`: URL to check
  - `STATUS_CHECK_TIMEOUT`: Request timeout in seconds
  - `STATUS_JOB_ENABLED`: Enable/disable the job

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=jobs

# Run specific test file
python -m pytest tests/test_base_job.py
```

### Code Formatting

```bash
# Format code
black jobs/ tests/

# Check formatting
black --check jobs/ tests/

# Lint code
flake8 jobs/ tests/
```

### Development Mode

Development mode provides:
- More frequent job scheduling
- Debug-level logging
- Development-specific configuration

```bash
python -m jobs --dev
```

## Deployment Patterns

The jobs package supports multiple deployment patterns:

### 1. Long-Running Service (Default)
Best for: Dedicated servers, containers, VPS

```bash
# Run continuously until stopped
python -m jobs

# Or with systemd
sudo systemctl start jobs-scheduler
```

### 2. Cron Jobs (External Scheduling)
Best for: Traditional servers, when you want OS-level scheduling

```bash
# crontab -e
*/5 * * * * cd /path/to/jobs && python -m jobs --once
0 */2 * * * cd /path/to/jobs && python -m jobs --job status_check
```

### 3. Serverless/Lambda
Best for: Cost optimization, event-driven workloads

```python
# Lambda handler
def lambda_handler(event, context):
    scheduler = JobScheduler(config)
    results = scheduler.run_once()
    return results
```

### 4. CI/CD Pipelines
Best for: GitHub Actions, GitLab CI, etc.

```yaml
# .github/workflows/scheduled-jobs.yml
on:
  schedule:
    - cron: "*/30 * * * *"
jobs:
  run-jobs:
    runs-on: ubuntu-latest
    steps:
      - run: python -m jobs --once
```

### 5. Kubernetes CronJobs
Best for: Kubernetes environments

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scheduled-jobs
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: jobs
            image: your-app:latest
            command: ["python", "-m", "jobs", "--once"]
```

## Scheduling Format

The package uses a simple scheduling format:

- `every(N).seconds` - Every N seconds
- `every(N).minutes` - Every N minutes
- `every(N).hours` - Every N hours
- `every().day` - Once per day
- `every().hour` - Once per hour

Examples:
```env
SCHEDULE=every(30).seconds  # Every 30 seconds
SCHEDULE=every(5).minutes   # Every 5 minutes
SCHEDULE=every(2).hours     # Every 2 hours
```

## Logging

Logs include:
- Job start/completion messages
- Error details for failed jobs
- Scheduling information
- Performance metrics

Configure logging via environment variables:
```env
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/jobs.log  # Optional file output
```

## Scripts

### Tennis Tournament Visualization (`scripts/tennisviz.py`)

Generates an interactive HTML visualization of a tennis tournament bracket using NetworkX and Pyvis.

**Usage:**
```bash
# Using uv
uv run python scripts/tennisviz.py

# Or with activated venv
python scripts/tennisviz.py
```

The script will automatically save the HTML file to `apps/web/public/tennis_tournament_bracket.html` if the web app directory exists, otherwise it saves to the scripts directory.

## Project Structure

```
jobs/
├── __init__.py         # Package initialization
├── __main__.py         # CLI entry point
├── base_job.py         # Abstract base job class
├── scheduler.py        # Job scheduler
├── config.py          # Configuration management
├── example_jobs.py     # Example job implementations
├── scripts/            # Standalone scripts
│   └── tennisviz.py   # Tennis tournament visualization
└── tests/              # Test suite
    ├── __init__.py
    ├── test_base_job.py
    └── ...
```

## Contributing

1. Create a new job class inheriting from `BaseJob`
2. Add comprehensive tests
3. Update documentation
4. Follow code formatting standards (black, flake8)