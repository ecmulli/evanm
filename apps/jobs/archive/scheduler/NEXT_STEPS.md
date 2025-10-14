# Next Steps - Getting Started with Your Auto-Scheduler

## 🎉 What's Ready

Your Notion Calendar Auto-Scheduler is **fully implemented and ready to use**!

✅ Core scheduling engine  
✅ Time slot management (15-min intervals, work hours only)  
✅ Task ranking and prioritization  
✅ Automatic rescheduling for incomplete tasks  
✅ Notion API integration  
✅ Dry-run testing mode  
✅ Comprehensive documentation  
✅ Unit tests (all passing!)

## 📋 Quick Setup Checklist

Follow these steps to get your auto-scheduler running:

### ☐ Step 1: Add Notion Properties (5 minutes)

Open your **Livepeer Task Tracker** database and add three new properties:

1. **Scheduled Date** (Date with time range)
2. **Last Scheduled** (Date with time)
3. **Auto Schedule** (Checkbox, default checked)

📖 **Detailed instructions**: See `SETUP.md` → Step 1

### ☐ Step 2: Set Environment Variables (2 minutes)

Add to `/Users/evanmullins/Projects/evanm/.env.dev`:

```bash
LIVEPEER_NOTION_API_KEY=secret_your_api_key_here
LIVEPEER_NOTION_DB_ID=your_database_id_here
```

📖 **How to find these**: See `SETUP.md` → Step 2

### ☐ Step 3: Test the Setup (1 minute)

```bash
cd /Users/evanmullins/Projects/evanm/apps/jobs/scheduler
python3 test_scheduler.py
```

Expected: **"3/3 tests passed 🎉"**

### ☐ Step 4: Dry Run Test (2 minutes)

```bash
python3 calendar_scheduler.py --mode test
```

This will show you what would be scheduled without making changes.

### ☐ Step 5: Schedule Tasks (1 minute)

```bash
python3 calendar_scheduler.py --mode once
```

This will schedule all your tasks for real! Check your Notion database.

### ☐ Step 6: Connect Notion Calendar (3 minutes)

1. Open **Notion Calendar** app (desktop or web)
2. Click "Add calendar" or "+"
3. Select "Database"
4. Choose "Livepeer Task Tracker"
5. Click "Add"

Your scheduled tasks should now appear as time blocks in the calendar!

### ☐ Step 7: Deploy for Continuous Running (10-30 minutes)

Choose one option:

**Option A: Quick Local (5 min)**
```bash
screen -S scheduler
python3 calendar_scheduler.py --mode continuous
# Press Ctrl+A then D to detach
```

**Option B: Railway Cloud (15 min)**
- Deploy to Railway for 24/7 running
- See `DEPLOYMENT.md` → Railway section

**Option C: Local Service (30 min)**
- Set up systemd (Linux) or LaunchAgent (macOS)
- See `DEPLOYMENT.md` → Local Service section

## 📚 Documentation Guide

All documentation is in `/Users/evanmullins/Projects/evanm/apps/jobs/scheduler/`:

| File | Purpose |
|------|---------|
| `SETUP.md` | **START HERE** - Step-by-step setup instructions |
| `README.md` | Complete user guide and architecture |
| `DEPLOYMENT.md` | Deployment options (Railway, Docker, systemd, etc.) |
| `IMPLEMENTATION_SUMMARY.md` | What was built and how it works |
| `NEXT_STEPS.md` | This file - quick start checklist |

## 🧪 Testing Commands

```bash
# Run unit tests
python3 test_scheduler.py

# Dry run (no Notion updates)
python3 calendar_scheduler.py --mode test

# Schedule once and exit
python3 calendar_scheduler.py --mode once

# Continuous mode (every 10 minutes)
python3 calendar_scheduler.py --mode continuous
```

## ⚙️ Configuration Options

Edit your `.env.dev` to customize:

```bash
# Required
LIVEPEER_NOTION_API_KEY=secret_...
LIVEPEER_NOTION_DB_ID=...

# Optional (defaults shown)
SCHEDULER_INTERVAL_MINUTES=10    # How often to reschedule
WORK_START_HOUR=9                # 9am
WORK_END_HOUR=17                 # 5pm
SLOT_DURATION_MINUTES=15         # 15-minute slots
SCHEDULE_DAYS_AHEAD=7            # Schedule next 7 days
SCHEDULER_LOG_LEVEL=INFO         # Logging verbosity
```

## 🎯 Expected Behavior

Once running, the scheduler will:

1. **Every 10 minutes** (configurable):
   - Fetch all active tasks from Notion (sorted by Rank)
   - Generate available time slots (9am-5pm, Mon-Fri, 15-min intervals)
   - Assign tasks to earliest available slots
   - Update Notion with scheduled date ranges

2. **Automatic rescheduling**:
   - Tasks that passed their scheduled time but aren't completed
   - Moved to next available slot automatically
   - You'll see this in the logs as "🔄 Rescheduled"

3. **Notion Calendar sync**:
   - Scheduled tasks appear in Notion Calendar app
   - Displayed as time blocks with task names
   - Updates automatically when scheduler changes times

## 📊 Example Log Output

```
2025-10-14 09:00:00 - INFO - 🔄 Starting scheduling cycle...
2025-10-14 09:00:01 - INFO - Fetched 15 schedulable tasks
2025-10-14 09:00:01 - INFO - Generated 224 total work hour slots
2025-10-14 09:00:02 - INFO - ✅ Scheduled 'Fix API bug' from 2025-10-14 09:00 to 10:00
2025-10-14 09:00:02 - INFO - 🔄 Rescheduled 'Write docs' from 2025-10-14 10:00 to 11:30
2025-10-14 09:00:03 - INFO - ⏭️  Skipped 'Design mockups' (already scheduled)
2025-10-14 09:00:03 - INFO - 📊 Scheduling cycle complete:
2025-10-14 09:00:03 - INFO -   ✅ Scheduled: 5
2025-10-14 09:00:03 - INFO -   🔄 Rescheduled: 3
2025-10-14 09:00:03 - INFO -   ⏭️  Skipped: 7
2025-10-14 09:00:03 - INFO -   ⏱️  Duration: 2.15s
2025-10-14 09:00:03 - INFO - ⏸️  Waiting 10 minutes until next cycle...
```

## 🚨 Common Issues

### "Missing required environment variables"
→ Check that `.env.dev` has `LIVEPEER_NOTION_API_KEY` and `LIVEPEER_NOTION_DB_ID`

### "No tasks being scheduled"
→ Tasks must have:
  - Status: NOT Completed/Canceled/Backlog
  - Est Duration Hrs: Set to a number
  - Auto Schedule: Not explicitly unchecked

### "Tasks not in Notion Calendar"
→ Make sure:
  - Notion Calendar is connected to Livepeer database
  - Scheduled Date property has "Include time" and "Include end date" enabled

See `SETUP.md` → Troubleshooting for more help.

## 🔮 Future Enhancements

Already planned for Phase 2:
- **Past due highlighting**: Add 🔴 emoji to overdue task names
- **Calendar event integration**: Read existing events, schedule around them
- **Advanced optimization**: Fit small tasks into remaining day slots
- **Multi-workspace**: Support Hub, Livepeer, Vanquish all at once

## 💡 Pro Tips

1. **Start with dry-run mode** to verify scheduling looks correct
2. **Check Notion Calendar** after first real run to see results
3. **Watch the logs** for the first few cycles to understand behavior
4. **Use Auto Schedule checkbox** to exclude specific tasks from scheduling
5. **Adjust work hours** via environment variables if needed

## 🎬 Ready to Start?

1. Open `SETUP.md` for detailed step-by-step instructions
2. Follow the Quick Setup Checklist above
3. Run your first dry-run test
4. Schedule some tasks!
5. Connect Notion Calendar to see the magic ✨

**Estimated time to first scheduled tasks: 15-20 minutes**

---

Questions? Check:
- `SETUP.md` - Step-by-step setup
- `README.md` - Complete documentation
- `DEPLOYMENT.md` - Deployment options
- `IMPLEMENTATION_SUMMARY.md` - How it works

**Happy scheduling! 📅✨**

