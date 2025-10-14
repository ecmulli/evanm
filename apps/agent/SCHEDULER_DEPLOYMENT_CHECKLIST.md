# 🚀 Task Scheduler Deployment Checklist

The task scheduler is now integrated into the agent service and ready to deploy to Railway!

## ✅ What Was Done

### 1. **Migrated Scheduler to Agent Service**
- Moved core logic from `apps/jobs/scheduler/` to `apps/agent/scheduler/`
- Created service wrapper in `apps/agent/services/task_scheduler.py`
- Added API routes in `apps/agent/routes/scheduler.py`
- Integrated background task into `apps/agent/app.py`

### 2. **Architecture Benefits**
- ✅ Single Railway deployment (saves costs)
- ✅ Reuses existing Notion credentials
- ✅ API control via REST endpoints
- ✅ Better service-oriented design
- ✅ Background task runs every 10 minutes automatically

### 3. **Documentation**
- ✅ Updated `apps/agent/README.md`
- ✅ Updated `apps/agent/DEPLOYMENT.md`
- ✅ Created `apps/agent/scheduler/README.md`
- ✅ Added migration note in `apps/jobs/scheduler/MIGRATED.md`

## 📋 Railway Deployment Steps

### 1. **Set Environment Variables in Railway**

Go to your Railway dashboard and add these variables:

**Required (you probably already have these):**
```
OPENAI_API_KEY=sk-xxxxx
HUB_NOTION_API_KEY=secret_xxxxx
HUB_NOTION_DB_ID=xxxxxxxx
BEARER_TOKEN=your_token
```

**Required for Scheduler:**
```
LIVEPEER_NOTION_API_KEY=secret_xxxxx
LIVEPEER_NOTION_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Optional Scheduler Config (defaults shown):**
```
SCHEDULER_INTERVAL_MINUTES=5
WORK_START_HOUR=9
WORK_END_HOUR=17
SLOT_DURATION_MINUTES=15
SCHEDULE_DAYS_AHEAD=7
```

### 2. **Deploy**

Push to GitHub (Railway auto-deploys):
```bash
git push origin motion-dupe
```

Or merge to main if ready:
```bash
git checkout main
git merge motion-dupe
git push origin main
```

### 3. **Verify Deployment**

Once deployed, check these endpoints:

**Check if scheduler started:**
```bash
curl https://your-agent.railway.app/api/v1/scheduler/health \
  -H "Authorization: Bearer your_token"
```

**Check scheduler status:**
```bash
curl https://your-agent.railway.app/api/v1/scheduler/status \
  -H "Authorization: Bearer your_token"
```

**Manually trigger (optional):**
```bash
curl -X POST https://your-agent.railway.app/api/v1/scheduler/run \
  -H "Authorization: Bearer your_token"
```

### 4. **Monitor Logs**

In Railway dashboard, watch for these logs:
```
🚀 Starting Agent Server
📅 Initializing Task Scheduler Service...
✅ Task Scheduler Service started
📅 Scheduler background task started (interval: 10 min)
```

Every 10 minutes you should see:
```
🔄 Running scheduled task scheduling cycle...
📊 Scheduling cycle complete:
  ✅ Scheduled: X
  🔄 Rescheduled: Y
  ⏭️  Skipped: Z
  ⏱️  Duration: X.XXs
```

## 🧪 Local Testing

Test locally before deploying:

```bash
cd apps/agent

# Activate venv (if using one)
source venv/bin/activate

# Run the agent
python app.py
```

Then test the endpoints:
```bash
# Health check
curl http://localhost:8000/api/v1/scheduler/health

# Status
curl http://localhost:8000/api/v1/scheduler/status

# Manual trigger
curl -X POST http://localhost:8000/api/v1/scheduler/run
```

## 📊 Expected Behavior

### On Startup
1. Agent server starts
2. If `LIVEPEER_NOTION_API_KEY` and `LIVEPEER_NOTION_DB_ID` are set:
   - Scheduler service initializes
   - Background task starts
   - Runs every 10 minutes (configurable)

### Every Cycle (Default: 10 minutes)
1. Fetches all unscheduled or past-scheduled tasks
2. Sorts by Rank (ascending - lower rank = higher priority)
3. Assigns tasks to 15-minute time slots during work hours
4. Updates Notion "Scheduled Date" property
5. Logs statistics

### Notion Calendar
Tasks appear on your Notion Calendar automatically when scheduled!

## 🎯 What's Working

✅ **Core Scheduling**
- Priority-based task assignment (lower rank = higher priority)
- 15-minute time slots
- Work hours enforcement (9 AM - 5 PM, Mon-Fri)
- Continuous rescheduling of incomplete tasks
- Timezone-aware (uses local system timezone)

✅ **API Control**
- Status endpoint
- Manual trigger endpoint
- Health check endpoint

✅ **Integration**
- Direct Notion Calendar integration via date range property
- Reuses existing agent infrastructure
- Background task (non-blocking)

## 🔮 Future Enhancements

These are noted but not yet implemented:

- [ ] Pull existing calendar events and schedule around them
- [ ] Visual indicators for overdue tasks
- [ ] Multi-workspace support (Hub, Vanquish)
- [ ] Smart task fitting for remaining day slots
- [ ] Configurable work hours per day

## 📝 Git Commits

Three commits were created:

1. `56554a2` - Initial standalone scheduler implementation
2. `3dcaec3` - **Migration to agent service** (main commit)
3. `141d596` - Migration documentation

## 🆘 Troubleshooting

### Scheduler doesn't start
- Check that `LIVEPEER_NOTION_API_KEY` and `LIVEPEER_NOTION_DB_ID` are set
- Look for initialization errors in logs

### No tasks scheduled
- Verify tasks exist in Notion database
- Check that tasks have a "Rank" value
- Ensure tasks aren't already scheduled in the future
- Check work hours configuration

### API returns 503
- Scheduler service failed to initialize
- Check environment variables
- Review startup logs for errors

## 🎉 You're Ready!

Your Motion AI calendar duplicate is ready to deploy! The scheduler will:
1. Auto-start when agent deploys
2. Schedule tasks every 10 minutes
3. Update Notion Calendar automatically
4. Provide API control via REST endpoints

**Next step:** Set environment variables in Railway and deploy! 🚀

