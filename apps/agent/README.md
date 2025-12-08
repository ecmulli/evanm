# Agent Server

AI-powered task creation and management API built with FastAPI.

## Features

🤖 **Intelligent Task Creation**
- AI-powered task synthesis from text and images
- Smart parsing of priority, duration, workspace, and due dates
- Rich task descriptions and acceptance criteria generation
- Integration with Notion databases

📅 **Automatic Task Scheduling**
- Auto-schedules tasks into calendar time slots based on priority
- Continuous rescheduling of incomplete tasks
- Work hours enforcement (9 AM - 5 PM, Mon-Fri)
- Direct Notion Calendar integration
- Background task runs every 10 minutes

🚀 **Modern API Design**
- FastAPI with automatic OpenAPI documentation
- Pydantic models for request/response validation
- Proper error handling and logging
- Health check endpoints

🔧 **Production Ready**
- Environment-based configuration
- CORS middleware for web clients
- Railway deployment ready
- Comprehensive logging

## API Endpoints

### Task Creation
```
POST /api/v1/task_creator
```

**Request:**
```json
{
  "text_inputs": ["Fix the urgent bug by tomorrow. This is for Livepeer and should take 2 hours."],
  "image_urls": ["https://example.com/screenshot.png"],
  "suggested_workspace": "Livepeer",
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Task 'Fix urgent bug for Livepeer' created successfully in Livepeer",
  "task_id": "notion-page-id",
  "task_url": "https://notion.so/...",
  "parsed_data": {
    "task_name": "Fix urgent bug for Livepeer",
    "workspace": "Livepeer",
    "priority": "ASAP",
    "estimated_hours": 2,
    "due_date": "2025-09-02",
    "description": "...",
    "acceptance_criteria": "..."
  },
  "dry_run": false
}
```

### Task Scheduler

Get scheduler status:
```
GET /api/v1/scheduler/status
```

Manually trigger scheduling:
```
POST /api/v1/scheduler/run
```

Scheduler health check:
```
GET /api/v1/scheduler/health
```

See [scheduler/README.md](scheduler/README.md) for detailed documentation.

### Health Check
```
GET /api/v1/health
```

## Setup

### Environment Variables

Create a `.env` file in the agent directory:

```env
# Required
OPENAI_API_KEY=your_openai_api_key
HUB_NOTION_API_KEY=your_notion_api_key
HUB_NOTION_DB_ID=your_notion_database_id

# Optional (for external workspaces)
LIVEPEER_NOTION_API_KEY=livepeer_notion_key
LIVEPEER_NOTION_DB_ID=livepeer_database_id
LIVEPEER_NOTION_USER_ID=evan  # Required for scheduler - only schedules tasks assigned to this user (name or user ID, defaults to "evan")
VANQUISH_NOTION_API_KEY=vanquish_notion_key
VANQUISH_NOTION_DB_ID=vanquish_database_id

# Server config (optional)
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Task Scheduler Config (optional)
SCHEDULER_INTERVAL_MINUTES=10
WORK_START_HOUR=9
WORK_END_HOUR=17
SLOT_DURATION_MINUTES=15
SCHEDULE_DAYS_AHEAD=7
TIMEZONE=America/Chicago  # Default: America/Chicago (handles DST automatically)
# Other timezones: America/New_York, America/Los_Angeles, Europe/London, UTC
```

### Installation

#### Using uv (Recommended)

1. **Install uv if you haven't already:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies:**
   ```bash
   cd apps/agent
   uv sync
   ```

3. **Run the server:**
   ```bash
   # Activate the virtual environment
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows
   
   # Run the server
   python app.py
   ```

   Or with uvicorn directly:
   ```bash
   uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Using pip (Alternative)

1. **Install dependencies:**
   ```bash
   cd apps/agent
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python app.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the API:**
   - Server: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/v1/health

## Railway Deployment

This server is designed to be Railway-ready:

1. **Create a Railway project**
2. **Set environment variables** in Railway dashboard
3. **Deploy** - Railway will automatically detect the Python app

The server uses the `PORT` environment variable that Railway provides.

## Development

### Project Structure
```
apps/agent/
├── app.py                  # FastAPI application
├── requirements.txt        # Dependencies
├── routes/                 # API route handlers
│   ├── task_creator.py    # Task creation endpoints
│   └── scheduler.py       # Scheduler endpoints
├── services/              # Business logic
│   ├── task_creation.py   # Task creation service
│   └── task_scheduler.py  # Scheduler service
├── scheduler/             # Scheduler core logic
│   ├── time_slots.py      # Time slot management
│   └── scheduling_algorithm.py
├── models/                # Pydantic models
│   └── task_models.py
└── utils/                 # Utilities
    └── config.py
```

### Testing the Scheduler

Check scheduler status:
```bash
curl http://localhost:8000/api/v1/scheduler/status
```

Manually trigger scheduling:
```bash
curl -X POST http://localhost:8000/api/v1/scheduler/run
```

The scheduler runs automatically every 10 minutes when the server is running.

### Future Features

The architecture is designed to easily support additional AI-powered features:

- **Task Analyzer** - Analyze existing tasks for insights
- **Content Generator** - Generate various types of content
- **Meeting Summarizer** - Summarize meetings and create action items
- **Smart Router** - Automatically route requests to appropriate handlers
- **Calendar Event Integration** - Pull existing events and schedule around them
- **Overdue Task Highlighting** - Visual indicators for past-due tasks

### Testing

Test the API with curl:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create task (dry run)
curl -X POST http://localhost:8000/api/v1/task_creator \
  -H "Content-Type: application/json" \
  -d '{
    "text_inputs": ["Fix the payment bug by tomorrow. High priority Livepeer work, 3 hours."],
    "dry_run": true
  }'
```

## Architecture

The Agent Server uses a modular architecture:

- **Routes** handle HTTP requests and responses
- **Services** contain business logic and external integrations
- **Models** define data structures and validation
- **Utils** provide shared functionality and configuration

This separation makes it easy to add new features and maintain the codebase as it grows.
