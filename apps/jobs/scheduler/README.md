# Notion Calendar Auto-Scheduler

Automatically schedules Notion tasks into calendar time slots based on priority ranking, with continuous rescheduling every 5-10 minutes.

## Overview

This service reads tasks from your Notion Task Tracker database (Livepeer), ranks them by priority/duration/due date, and automatically schedules them into 15-minute time slots during work hours (9am-5pm, Mon-Fri). Tasks that aren't completed are automatically rescheduled to the next available slot.

## Features

- **Automated Scheduling**: Tasks scheduled based on rank (priority + duration + due date)
- **Continuous Rescheduling**: Incomplete tasks automatically moved to next available slot
- **Work Hours Only**: Scheduling constrained to 9am-5pm, Monday-Friday
- **15-Minute Slots**: Granular time management
- **Notion Calendar Integration**: Scheduled times sync automatically to Notion Calendar app
- **Dry-Run Mode**: Test scheduling logic without making changes

## Prerequisites

### 1. Notion Database Setup

Your Livepeer Task Tracker database should have these properties:

**Required (existing):**
- `Task name` (Title)
- `Rank` (Formula) - Combines priority, duration, due date
- `Status` (Status)
- `Est Duration Hrs` (Number)
- `Due date` (Date)

**New properties to add:**
- `Scheduled Date` (Date with time range) - Where scheduled times are stored
- `Last Scheduled` (Date with time) - Timestamp of last scheduling update
- `Auto Schedule` (Checkbox) - Whether to include in auto-scheduling (default: true)

### 2. Environment Variables

Create or update `.env.dev` or `.env` with:

```bash
# Livepeer Notion Configuration
LIVEPEER_NOTION_API_KEY=secret_your_livepeer_notion_api_key
LIVEPEER_NOTION_DB_ID=your_livepeer_database_id

# Scheduler Configuration (optional, defaults shown)
SCHEDULER_INTERVAL_MINUTES=10  # How often to reschedule
WORK_START_HOUR=9              # Work day start (9am)
WORK_END_HOUR=17               # Work day end (5pm)
SLOT_DURATION_MINUTES=15       # Time slot size
SCHEDULE_DAYS_AHEAD=7          # How many days to schedule in advance

# Logging (optional)
SCHEDULER_LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR
```

### 3. Dependencies

The scheduler uses the existing project dependencies:
- `notion-client` - Notion API integration
- `python-dotenv` - Environment variable management

Install if needed:
```bash
cd apps/jobs
pip install -r requirements.txt
```

## Usage

### Test Mode (Dry Run)

Test the scheduler without making any changes to Notion:

```bash
cd apps/jobs
venv/bin/python scheduler/calendar_scheduler.py --mode test
```

This will:
- Fetch all schedulable tasks
- Show what would be scheduled and when
- Not update Notion

### Run Once

Schedule all tasks once and exit:

```bash
python calendar_scheduler.py --mode once
```

### Continuous Mode

Run the scheduler continuously (recommended for production):

```bash
python calendar_scheduler.py --mode continuous
```

This will:
- Schedule tasks every 10 minutes (configurable)
- Detect and reschedule incomplete tasks
- Run indefinitely until stopped (Ctrl+C)

## How It Works

### Scheduling Logic

Every scheduling cycle:

1. **Fetch Tasks**: Query all active tasks (not Completed/Canceled/Backlog)
2. **Sort by Rank**: Higher rank = higher priority
3. **Generate Slots**: Create 15-minute slots for next 7 days (work hours only)
4. **Schedule Tasks**: For each task (highest rank first):
   - Find earliest available slot that fits task duration
   - Prefer slots before due date (but schedule anyway if overdue)
   - Update Notion with scheduled time range
5. **Detect Overdue**: Find tasks that passed their scheduled time but aren't completed
6. **Reschedule**: Move overdue incomplete tasks to next available slots

### Time Slot Allocation

- Task duration is converted to number of slots needed
  - Example: 2-hour task = 8 slots (8 × 15 minutes)
- Tasks are assigned to contiguous available slots
- Tasks don't span across days
- Weekends are skipped

### Rescheduling Rules

A task is rescheduled if:
1. It has no scheduled date yet (new task)
2. Its scheduled start time has passed but status isn't "Completed"

## Notion Calendar Integration

### Setup

1. Open Notion Calendar app
2. Connect to your Livepeer Task Tracker database
3. The calendar will automatically display tasks using the `Scheduled Date` property

### Date Range Property

The `Scheduled Date` property contains both start and end times in a single date range:
- **Start**: When the task is scheduled to begin
- **End**: When the task is scheduled to end

Notion Calendar reads this directly - no separate API needed!

## Deployment

### Option 1: Local Development

Run the scheduler on your local machine:

```bash
# Terminal 1
cd apps/jobs/scheduler
python calendar_scheduler.py --mode continuous

# Keep terminal open and running
```

### Option 2: Background Service (macOS/Linux)

Create a systemd service or use `screen`/`tmux`:

```bash
# Using screen
screen -S scheduler
cd apps/jobs/scheduler
python calendar_scheduler.py --mode continuous
# Press Ctrl+A then D to detach

# Reattach later
screen -r scheduler
```

### Option 3: Deploy to Railway/Render

1. Create a new service on Railway or Render
2. Connect to your git repository
3. Set environment variables in the dashboard
4. Deploy command: `python apps/jobs/scheduler/calendar_scheduler.py --mode continuous`

## Monitoring

### Logs

The scheduler provides detailed logging:

```
2025-10-14 09:00:00 - INFO - 🔄 Starting scheduling cycle...
2025-10-14 09:00:01 - INFO - Fetched 15 schedulable tasks (out of 20 active tasks)
2025-10-14 09:00:01 - INFO - Generated 224 total work hour slots
2025-10-14 09:00:02 - INFO - ✅ Scheduled 'Fix bug in API' from 2025-10-14 09:00 to 10:00
2025-10-14 09:00:02 - INFO - 🔄 Rescheduling 'Write documentation' (passed scheduled time)
2025-10-14 09:00:03 - INFO - ✅ Scheduled 'Write documentation' from 2025-10-14 10:00 to 11:30
2025-10-14 09:00:03 - INFO - 📊 Scheduling cycle complete:
2025-10-14 09:00:03 - INFO -   ✅ Scheduled: 5
2025-10-14 09:00:03 - INFO -   🔄 Rescheduled: 3
2025-10-14 09:00:03 - INFO -   ⏭️  Skipped: 7
2025-10-14 09:00:03 - INFO -   ⏱️  Duration: 2.15s
```

### Health Checks

Monitor the scheduler by:
- Checking logs for errors
- Verifying tasks appear in Notion Calendar
- Confirming rescheduling happens for overdue tasks

## Troubleshooting

### Common Issues

**No tasks being scheduled:**
- Check that tasks have `Status` not in (Completed, Canceled, Backlog)
- Verify `Auto Schedule` checkbox isn't explicitly unchecked
- Ensure tasks have `Est Duration Hrs` set
- Check `Rank` property exists and has values

**Tasks not appearing in Notion Calendar:**
- Verify you've connected Notion Calendar to the Livepeer database
- Check that `Scheduled Date` property exists and is type "Date"
- Ensure the property has both start and end times

**Configuration errors:**
- Verify environment variables are set correctly
- Check `.env.dev` or `.env` file exists in project root
- Ensure `LIVEPEER_NOTION_API_KEY` and `LIVEPEER_NOTION_DB_ID` are valid

**Rate limiting:**
- Notion API has rate limits (3 requests/second)
- The scheduler includes built-in delays to respect limits
- If you have many tasks, consider increasing `SCHEDULER_INTERVAL_MINUTES`

## Future Enhancements

Planned features:

1. **Past Due Highlighting**: Add emoji/icon to task names when past due date
2. **Calendar Event Integration**: Read existing calendar events and schedule around them
3. **Advanced Optimization**: Fit small tasks into remaining day slots intelligently
4. **Multi-workspace**: Support scheduling across multiple Notion databases
5. **Webhook Integration**: Real-time rescheduling on task updates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  calendar_scheduler.py                       │
│  • Main service loop                                        │
│  • Configuration management                                 │
│  • Orchestrates scheduling cycles                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼──────────┐     ┌─────────▼──────────┐
│ scheduling_      │     │   time_slots.py    │
│ algorithm.py     │     │  • Generate slots  │
│  • Fetch tasks   │◄────┤  • Track occupied  │
│  • Assign slots  │     │  • Availability    │
│  • Update Notion │     └────────────────────┘
└──────────────────┘
        │
        │
┌───────▼──────────────────────────────────────┐
│         Notion API (Livepeer DB)             │
│  • Task Tracker database                     │
│  • Scheduled Date property                   │
└──────────────┬───────────────────────────────┘
               │
               │ (automatic sync)
               │
┌──────────────▼───────────────────────────────┐
│         Notion Calendar App                   │
│  • Displays scheduled tasks                  │
│  • Shows time ranges                         │
└──────────────────────────────────────────────┘
```

## License

Part of the evanm project.

