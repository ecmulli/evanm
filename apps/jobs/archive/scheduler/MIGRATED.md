# ⚠️ SCHEDULER MIGRATED TO AGENT SERVICE

**This scheduler implementation has been migrated to the agent service.**

## New Location
📍 **`apps/agent/scheduler/`**

The task scheduler is now integrated into the agent service at `/Users/evanmullins/Projects/evanm/apps/agent/` for better architecture and to leverage the existing Railway deployment.

## Why the Move?

1. **Single Service Deployment** - No need for separate Railway instance
2. **Shared Infrastructure** - Reuses existing Notion API credentials
3. **API Control** - Can trigger/monitor scheduling via REST API
4. **Better Architecture** - Follows service-oriented design pattern
5. **Cost Savings** - One Railway deployment instead of two

## How to Use

### Via Agent API
The scheduler runs automatically as a background task in the agent service:

```bash
# Check status
curl http://localhost:8000/api/v1/scheduler/status

# Manually trigger
curl -X POST http://localhost:8000/api/v1/scheduler/run

# Health check
curl http://localhost:8000/api/v1/scheduler/health
```

### Documentation
See the new documentation:
- **Main README**: `apps/agent/scheduler/README.md`
- **Agent README**: `apps/agent/README.md`
- **Deployment Guide**: `apps/agent/DEPLOYMENT.md`

## Legacy Files

This directory is kept for historical reference. The following files were migrated:

- ✅ `time_slots.py` → `apps/agent/scheduler/time_slots.py`
- ✅ `scheduling_algorithm.py` → `apps/agent/scheduler/scheduling_algorithm.py`
- ✅ `calendar_scheduler.py` → Integrated into `apps/agent/services/task_scheduler.py`
- ✅ Tests → Can be run from agent directory
- ✅ Documentation → Updated in agent directory

## Migration Date
October 14, 2025

## Related Commits
- Initial implementation: `56554a2` (feat: Add Notion Calendar Auto-Scheduler)
- Migration to agent: `3dcaec3` (feat: Integrate task scheduler into agent service)

