# Notion Calendar Auto-Scheduler Setup Guide

Complete step-by-step instructions to get the auto-scheduler running.

## Step 1: Add Required Properties to Notion Database

Open your **Livepeer Task Tracker** database in Notion and add these three new properties:

### 1. Scheduled Date (Date property)
- **Type**: Date
- **Name**: `Scheduled Date`
- **Settings**: 
  - ✅ Include time
  - ✅ Include end date (this makes it a date range)
- **Purpose**: Stores when tasks are scheduled (both start and end time)

### 2. Last Scheduled (Date property)
- **Type**: Date  
- **Name**: `Last Scheduled`
- **Settings**:
  - ✅ Include time
  - ❌ Include end date (single timestamp)
- **Purpose**: Tracks when a task was last scheduled/rescheduled

### 3. Auto Schedule (Checkbox property)
- **Type**: Checkbox
- **Name**: `Auto Schedule`
- **Default**: Checked (true)
- **Purpose**: Control which tasks to include in auto-scheduling

**How to add properties:**
1. Open your Livepeer database
2. Click the `+` button in the table header
3. Select property type
4. Name it exactly as shown above
5. Configure settings

## Step 2: Set Environment Variables

Add these variables to `.env.dev` or `.env` file in the project root (`/Users/evanmullins/Projects/evanm/.env.dev`):

```bash
# Required
LIVEPEER_NOTION_API_KEY=secret_your_api_key_here
LIVEPEER_NOTION_DB_ID=your_database_id_here

# Optional (defaults shown)
SCHEDULER_INTERVAL_MINUTES=10
WORK_START_HOUR=9
WORK_END_HOUR=17
SLOT_DURATION_MINUTES=15
SCHEDULE_DAYS_AHEAD=7
SCHEDULER_LOG_LEVEL=INFO
```

**Where to find these values:**

### Notion API Key
1. Go to https://www.notion.so/my-integrations
2. Find your Livepeer integration (or create one)
3. Copy the "Internal Integration Token"
4. Paste as `LIVEPEER_NOTION_API_KEY`

### Notion Database ID
1. Open your Livepeer Task Tracker in Notion
2. Look at the URL: `https://notion.so/workspace/DATABASE_ID?v=...`
3. The DATABASE_ID is the long string before `?v=`
4. Paste as `LIVEPEER_NOTION_DB_ID`

### Grant Database Access
Don't forget to share your database with the integration:
1. Open the Livepeer Task Tracker database
2. Click "..." menu (top right)
3. Select "Connections" or "Add connections"
4. Add your Livepeer integration
5. Grant "Full access"

## Step 3: Verify Setup

Run the test suite to verify everything is configured correctly:

```bash
cd /Users/evanmullins/Projects/evanm/apps/jobs/scheduler
python3 test_scheduler.py
```

Expected output:
```
🧪 NOTION CALENDAR AUTO-SCHEDULER - TEST SUITE
...
✅ PASS - Time Slot Generation
✅ PASS - Slot Finding
✅ PASS - Day Boundary

3/3 tests passed
🎉 All tests passed!
```

## Step 4: Test with Dry Run

Test the scheduler against your actual Notion database without making changes:

```bash
python3 calendar_scheduler.py --mode test
```

This will:
- Connect to your Notion database
- Fetch all schedulable tasks
- Show what would be scheduled and when
- **NOT** update anything in Notion

**Expected output:**
```
🧪 Running in DRY RUN mode - no changes will be made
📋 Configuration loaded:
  Work hours: 9:00 - 17:00
  Slot duration: 15 minutes
  Scheduling interval: 10 minutes
  Days ahead: 7
✅ Notion client initialized
🔄 Starting scheduling cycle...
Fetched 15 schedulable tasks (out of 20 active tasks)
Generated 224 total work hour slots
🧪 DRY RUN: Would schedule 'Fix bug in API' from 2025-10-14 09:00 to 10:00
🧪 DRY RUN: Would schedule 'Write docs' from 2025-10-14 10:00 to 11:30
...
📊 Scheduling cycle complete:
  ✅ Scheduled: 12
  🔄 Rescheduled: 3
  ⏭️  Skipped: 5
  ⏱️  Duration: 2.15s
✅ Scheduling complete
```

## Step 5: Run Once (First Real Scheduling)

Once you've verified the dry run looks good, run a real scheduling cycle:

```bash
python3 calendar_scheduler.py --mode once
```

This will:
- Schedule all tasks into time slots
- Update Notion with scheduled times
- Run once and exit

Check your Notion database - you should see the `Scheduled Date` column filled in with date ranges!

## Step 6: Connect Notion Calendar

Now that tasks are scheduled, connect Notion Calendar to see them:

1. **Open Notion Calendar app** (desktop or web)
2. **Add database as calendar source:**
   - Click "Add calendar" or "+"
   - Select "Database"
   - Choose your "Livepeer Task Tracker" database
   - Click "Add"
3. **Configure display settings:**
   - Calendar will automatically use the `Scheduled Date` property
   - Tasks will appear as time blocks
   - You can customize colors by status/priority

Your tasks should now appear in the calendar with their scheduled time blocks!

## Step 7: Run Continuously

For ongoing automatic scheduling, run in continuous mode:

```bash
python3 calendar_scheduler.py --mode continuous
```

This will:
- Run every 10 minutes (configurable)
- Detect tasks that passed their scheduled time but aren't completed
- Automatically reschedule them to next available slot
- Run indefinitely until stopped (Ctrl+C)

**Recommended:** Run this in the background or deploy it as a service.

### Option A: Run in Background (macOS/Linux)

Using `screen`:
```bash
screen -S scheduler
cd /Users/evanmullins/Projects/evanm/apps/jobs/scheduler
python3 calendar_scheduler.py --mode continuous

# Press Ctrl+A then D to detach
# To reattach: screen -r scheduler
```

Using `nohup`:
```bash
cd /Users/evanmullins/Projects/evanm/apps/jobs/scheduler
nohup python3 calendar_scheduler.py --mode continuous > scheduler.log 2>&1 &

# View logs: tail -f scheduler.log
# Stop: kill <process_id>
```

### Option B: Deploy to Railway/Render (Recommended for 24/7)

See `DEPLOYMENT.md` for cloud deployment instructions.

## Troubleshooting

### No tasks being scheduled

**Check 1: Task Status**
- Tasks must have status NOT IN (Completed, Canceled, Backlog)
- Active statuses: Todo, In Progress, etc.

**Check 2: Auto Schedule checkbox**
- If the checkbox exists and is unchecked, task won't be scheduled
- Default is checked (true)

**Check 3: Est Duration Hrs**
- Tasks must have a duration value set
- Duration determines how many time slots are needed

**Check 4: Rank property**
- Verify the Rank formula property exists
- Higher rank = higher priority for scheduling

### Tasks not appearing in Notion Calendar

**Check 1: Database connected?**
- Open Notion Calendar app
- Verify Livepeer Task Tracker is added as a calendar source

**Check 2: Scheduled Date property**
- Must be type "Date"
- Must have "Include time" enabled
- Must have "Include end date" enabled (date range)

**Check 3: Date range format**
- Scheduled Date should show: "Oct 14, 2025 9:00 AM → 10:00 AM"
- If only showing start time, the end date isn't enabled

### Environment variable errors

```
❌ Configuration error: Missing required environment variables
```

**Solution:**
1. Verify `.env.dev` or `.env` file exists in project root
2. Check that variables are spelled correctly
3. Ensure no spaces around `=` sign
4. Make sure API key starts with `secret_`

### Notion API errors

```
❌ Failed to initialize Notion client
```

**Solution:**
1. Verify API key is correct
2. Check database ID is correct (from URL)
3. Ensure database is shared with the integration
4. Try regenerating the integration token

### Too many tasks being scheduled

If you want to exclude certain tasks from auto-scheduling:
1. Add the "Auto Schedule" checkbox property (if not already added)
2. Uncheck it for tasks you want to manually schedule
3. Scheduler will skip unchecked tasks

## Next Steps

Once the scheduler is running:

1. **Monitor scheduling:** Watch the logs to see tasks being scheduled
2. **Check Notion Calendar:** Verify tasks appear correctly
3. **Test rescheduling:** Mark a past-scheduled task as incomplete and watch it reschedule
4. **Adjust work hours:** Modify `WORK_START_HOUR`/`WORK_END_HOUR` if needed
5. **Deploy for 24/7:** Set up continuous running via cloud service

## Future Enhancements

Planned features you can help implement:

1. **Past due highlighting:** Add emoji to task names when overdue
2. **Calendar event integration:** Read existing events and schedule around them
3. **Advanced optimization:** Smart fitting of small tasks into remaining day slots
4. **Multi-workspace:** Support scheduling across Hub, Livepeer, Vanquish

See `README.md` for full documentation.

