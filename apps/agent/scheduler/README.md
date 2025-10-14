# Task Scheduler

Automatic task scheduling system that schedules Notion tasks into calendar time slots based on priority ranking.

## Overview

This scheduler is integrated into the Agent service and runs as a background task. It automatically:
- Schedules new tasks into available time slots
- Reschedules incomplete tasks
- Prioritizes by rank (lower number = higher priority)
- Only schedules during work hours (default: 9 AM - 5 PM, Mon-Fri)

## Configuration

Add these environment variables to your `.env` file or Railway configuration:

### Required
```bash
# Livepeer Notion Credentials
LIVEPEER_NOTION_API_KEY=secret_xxxxx
LIVEPEER_NOTION_DB_ID=xxxxxxxx
```

### Optional (with defaults)
```bash
# Work hours (24-hour format)
WORK_START_HOUR=9
WORK_END_HOUR=17

# Time slot configuration
SLOT_DURATION_MINUTES=15
SCHEDULE_DAYS_AHEAD=7

# Scheduler interval (how often to run)
SCHEDULER_INTERVAL_MINUTES=10
```

## API Endpoints

### Get Scheduler Status
```bash
GET /api/v1/scheduler/status
```

Returns current scheduler configuration and last run statistics.

**Response:**
```json
{
  "last_run": "2025-10-14T15:30:00-05:00",
  "last_stats": {
    "scheduled": 5,
    "rescheduled": 2,
    "skipped": 1,
    "errors": 0
  },
  "work_hours": "9:00 - 17:00",
  "slot_duration_minutes": 15,
  "schedule_days_ahead": 7
}
```

### Manually Trigger Scheduling
```bash
POST /api/v1/scheduler/run
```

Immediately runs a scheduling cycle (doesn't wait for interval).

**Response:**
```json
{
  "success": true,
  "message": "Scheduling cycle completed successfully",
  "stats": {
    "scheduled": 5,
    "rescheduled": 2,
    "skipped": 1,
    "errors": 0
  }
}
```

### Health Check
```bash
GET /api/v1/scheduler/health
```

Check if scheduler is running properly.

**Response:**
```json
{
  "status": "operational",
  "healthy": true,
  "last_run": "2025-10-14T15:30:00-05:00",
  "last_stats": {...}
}
```

## How It Works

### Background Task
The scheduler runs automatically in the background when the Agent service starts:
1. Starts on application startup
2. Runs every 10 minutes (configurable via `SCHEDULER_INTERVAL_MINUTES`)
3. Fetches all tasks that need scheduling
4. Assigns them to available time slots based on priority
5. Updates Notion with scheduled dates
6. Logs statistics

### Task Prioritization
Tasks are sorted by the "Rank" column (ascending):
- Lower rank number = higher priority = earlier slot
- Rank is calculated from priority, duration, and due date
- Tasks with no rank are skipped

### Scheduling Logic
1. **Fetch tasks**: Get all tasks without a scheduled date or past their scheduled time
2. **Generate slots**: Create 15-minute time slots for work hours
3. **Assign tasks**: Match tasks to slots based on:
   - Task rank (priority)
   - Task duration (must fit in available slots)
   - Preference for scheduling before due date
4. **Update Notion**: Save scheduled date/time back to database

### Work Hours
- Default: Monday-Friday, 9 AM - 5 PM
- Configurable via environment variables
- Slots are 15 minutes by default
- Tasks are scheduled into consecutive slots based on duration

### Timezone Handling
The scheduler uses configured timezone for all scheduling operations:
- Default timezone: `America/Chicago` (Central Time)
- Automatically handles Daylight Saving Time transitions
- Configure via `TIMEZONE` environment variable
- Supports all IANA timezone names (e.g., America/New_York, America/Los_Angeles, Europe/London, UTC)

## Integration with Notion

### Required Database Properties
Your Notion database must have these properties:

1. **Rank** (Number): Priority ranking (lower = higher priority)
2. **Duration** (Number): Task duration in minutes
3. **Due Date** (Date): Optional soft deadline
4. **Status** (Select): Must include "Done" option
5. **Scheduled Date** (Date with time): Auto-populated by scheduler
6. **Last Scheduled** (Date with time): Timestamp of last scheduling

### Notion Calendar Integration
The scheduler updates the "Scheduled Date" property which Notion Calendar uses to display tasks on your calendar.

## Logs

Monitor scheduler activity in the Agent logs:

```
📅 Scheduler background task started (interval: 10 min)
🔄 Running scheduled task scheduling cycle...
📊 Scheduling cycle complete:
  ✅ Scheduled: 5
  🔄 Rescheduled: 2
  ⏭️  Skipped: 1
  ⏱️  Duration: 2.34s
```

## Development

### Testing Locally
The scheduler will start automatically when you run the Agent service:

```bash
cd apps/agent
source venv/bin/activate  # If using venv
python app.py
```

### Manual Trigger
Use the API to manually trigger a cycle:

```bash
curl -X POST http://localhost:8000/api/v1/scheduler/run
```

### Check Status
```bash
curl http://localhost:8000/api/v1/scheduler/status
```

## Railway Deployment

The scheduler runs automatically in your existing Railway deployment:

1. Add environment variables in Railway dashboard:
   - `LIVEPEER_NOTION_API_KEY`
   - `LIVEPEER_NOTION_DB_ID`
   - Optional: `SCHEDULER_INTERVAL_MINUTES`, `WORK_START_HOUR`, etc.

2. Deploy/redeploy the agent service

3. Scheduler starts automatically on startup

4. Monitor logs in Railway dashboard

## Future Enhancements

- [ ] Pull existing calendar events and schedule around them
- [ ] Add visual indicators for overdue tasks
- [ ] Multi-workspace support (Hub, Vanquish)
- [ ] Smart task fitting (fit small tasks in remaining slots)
- [ ] Configurable work hours per day of week

