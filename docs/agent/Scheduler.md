# Scheduler API Reference

The Task Scheduler automatically assigns Notion tasks to calendar time slots based on priority ranking.

## Overview

The scheduler runs as a background task in the Agent service:
- Executes every 10 minutes (configurable)
- Schedules tasks based on Rank column (lower = higher priority)
- Only schedules during work hours (default: 9 AM - 5 PM, Mon-Fri)
- Updates the "Scheduled Date" property in Notion

## Endpoints

### GET /api/v1/scheduler/status

Returns current scheduler configuration and last run statistics.

**Authentication:** None required

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

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `last_run` | string | ISO timestamp of last scheduling cycle |
| `last_stats` | object | Statistics from last run |
| `last_stats.scheduled` | int | Tasks newly scheduled |
| `last_stats.rescheduled` | int | Tasks moved to new slots |
| `last_stats.skipped` | int | Tasks skipped (no rank, etc.) |
| `last_stats.errors` | int | Tasks that failed to schedule |
| `work_hours` | string | Configured work hours |
| `slot_duration_minutes` | int | Time slot size in minutes |
| `schedule_days_ahead` | int | How many days ahead to schedule |

**Example:**
```bash
curl http://localhost:8000/api/v1/scheduler/status
```

---

### POST /api/v1/scheduler/run

Manually trigger a scheduling cycle. Does not wait for the automatic interval.

**Authentication:** None required

**Request Body:** None

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

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether the cycle completed |
| `message` | string | Status message |
| `stats` | object | Scheduling statistics |

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/scheduler/run
```

---

### GET /api/v1/scheduler/health

Health check for the scheduler subsystem.

**Authentication:** None required

**Response (healthy):**
```json
{
  "status": "operational",
  "healthy": true,
  "last_run": "2025-10-14T15:30:00-05:00",
  "last_stats": {
    "scheduled": 5,
    "rescheduled": 2,
    "skipped": 1,
    "errors": 0
  }
}
```

**Response (not initialized):**
```json
{
  "status": "not_initialized",
  "healthy": false
}
```

**Response (error):**
```json
{
  "status": "error",
  "healthy": false,
  "error": "Error message here"
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/scheduler/health
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LIVEPEER_NOTION_API_KEY` | (required) | Notion integration token |
| `LIVEPEER_NOTION_DB_ID` | (required) | Notion database ID |
| `LIVEPEER_NOTION_USER_ID` | evan | User name/ID for task filtering |
| `SCHEDULER_INTERVAL_MINUTES` | 10 | Minutes between automatic runs |
| `WORK_START_HOUR` | 9 | Work day start hour (24h format) |
| `WORK_END_HOUR` | 17 | Work day end hour (24h format) |
| `SLOT_DURATION_MINUTES` | 15 | Size of time slots in minutes |
| `SCHEDULE_DAYS_AHEAD` | 7 | Number of days to look ahead |
| `TIMEZONE` | America/Chicago | IANA timezone for scheduling |

### Timezone Examples

```bash
TIMEZONE=America/New_York      # Eastern
TIMEZONE=America/Los_Angeles   # Pacific
TIMEZONE=America/Chicago       # Central (default)
TIMEZONE=Europe/London         # UK
TIMEZONE=UTC                   # UTC
```

The scheduler handles Daylight Saving Time transitions automatically.

---

## Notion Database Requirements

Your Notion database must have these properties for the scheduler to work:

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| **Rank** | Number | Priority ranking (lower = scheduled first) |
| **Duration** | Number | Task duration in minutes |
| **Due Date** | Date | Tasks without due dates are skipped |
| **Assignee** | People | Must match `LIVEPEER_NOTION_USER_ID` |
| **Status** | Select | Must include "Done", "Backlog" options |
| **Scheduled Date** | Date (with time) | Auto-populated by scheduler |

### Optional Properties

| Property | Type | Description |
|----------|------|-------------|
| **Last Scheduled** | Date (with time) | Timestamp of last scheduling |

---

## How Scheduling Works

### Task Selection

The scheduler fetches tasks that:
1. Are assigned to the configured user (`LIVEPEER_NOTION_USER_ID`)
2. Have a due date set
3. Are NOT in status: "Done", "Completed", "Canceled", "Backlog"
4. Have a Rank value (unranked tasks are skipped)

### Slot Generation

Time slots are generated for:
- Work hours only (default: 9 AM - 5 PM)
- Weekdays only (Monday - Friday)
- Configured number of days ahead (default: 7)
- In the configured time slot size (default: 15 minutes)

### Assignment Algorithm

1. Sort tasks by Rank (ascending - lower rank = higher priority)
2. For each task:
   - Calculate required slots based on Duration
   - Find first available consecutive slots
   - Prefer slots before the task's due date
   - Assign task to those slots
   - Mark slots as occupied
3. Update Notion with the scheduled date/time

### Rescheduling

Tasks are rescheduled if:
- Their scheduled time has passed but they're not complete
- Their rank has changed
- The scheduler is manually triggered

---

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

---

## Source Files

| File | Description |
|------|-------------|
| `apps/agent/routes/scheduler.py` | API endpoints |
| `apps/agent/services/task_scheduler.py` | Main service class |
| `apps/agent/scheduler/scheduling_algorithm.py` | Core algorithm |
| `apps/agent/scheduler/time_slots.py` | Slot generation |

---

## Errors

### 503 Service Unavailable

```json
{"detail": "Scheduler service not initialized"}
```

**Cause:** `LIVEPEER_NOTION_API_KEY` or `LIVEPEER_NOTION_DB_ID` not set.

**Fix:** Add the required environment variables and restart the service.

### 500 Internal Server Error

**Possible causes:**
- Invalid Notion credentials
- Database missing required properties
- Network issues with Notion API

Check the Agent logs for details.

---

## Future Enhancements

- [ ] Pull existing calendar events and schedule around them
- [ ] Add visual indicators for overdue tasks
- [ ] Multi-workspace support (Hub, Vanquish)
- [ ] Smart task fitting (fit small tasks in remaining slots)
- [ ] Configurable work hours per day of week
