# Troubleshooting Guide

Common issues and their solutions for the evanm.xyz monorepo.

## Table of Contents

- [Agent API Issues](#agent-api-issues)
- [Scheduler Issues](#scheduler-issues)
- [Web App Issues](#web-app-issues)
- [Deployment Issues](#deployment-issues)
- [Local Development Issues](#local-development-issues)

---

## Agent API Issues

### Server Won't Start

**Symptom:** `python app.py` fails immediately

**Check 1: Missing environment variables**
```bash
# Error: "Missing required environment variables: OPENAI_API_KEY, ..."
```

**Solution:** Ensure these are set:
```bash
export OPENAI_API_KEY=your_key
export HUB_NOTION_API_KEY=your_key
export HUB_NOTION_DB_ID=your_db_id
```

**Check 2: Python dependencies missing**
```bash
# Error: "ModuleNotFoundError: No module named 'fastapi'"
```

**Solution:**
```bash
cd apps/agent
uv sync  # or: pip install -r requirements.txt
```

**Check 3: Port already in use**
```bash
# Error: "Address already in use"
```

**Solution:**
```bash
# Find and kill the process
lsof -i :8000
kill <PID>
```

---

### 401 Unauthorized on API Calls

**Symptom:** API returns `{"detail": "Unauthorized"}`

**Check 1: BEARER_TOKEN is set but not matching**

The request must include:
```bash
curl -H "Authorization: Bearer $BEARER_TOKEN" ...
```

**Check 2: Token format is wrong**

Must be `Bearer <token>`, not just `<token>`.

**Solution for local development:** Unset `BEARER_TOKEN` to disable auth:
```bash
unset BEARER_TOKEN
python app.py
```

---

### 500 Internal Server Error on Task Creation

**Symptom:** POST to `/api/v1/task_creator` returns 500

**Check 1: OpenAI API key invalid**
```bash
# In logs: "OpenAI API error" or "Invalid API key"
```

**Solution:** Verify your OpenAI API key is valid and has credits.

**Check 2: Notion credentials invalid**
```bash
# In logs: "Notion API error" or "Could not find database"
```

**Solution:**
1. Verify `HUB_NOTION_API_KEY` is a valid integration token
2. Verify `HUB_NOTION_DB_ID` is correct
3. Ensure the integration has access to the database

**Check 3: Notion database missing required properties**

The database needs these properties:
- Name (title)
- Priority (select)
- Status (select)
- Due Date (date)
- Description (rich text)

---

### API Timeout

**Symptom:** Requests hang and eventually timeout

**Possible causes:**
1. OpenAI API is slow (especially with vision/images)
2. Notion API rate limiting
3. Large image processing

**Solution:** Use `dry_run: true` first to test parsing:
```bash
curl -X POST http://localhost:8000/api/v1/task_creator \
  -H "Content-Type: application/json" \
  -d '{"text_inputs": ["Test task"], "dry_run": true}'
```

---

## Scheduler Issues

### Scheduler Not Starting

**Symptom:** No "Scheduler background task started" in logs

**Check:** Livepeer credentials not set
```bash
# In logs: "Task Scheduler not configured (LIVEPEER_NOTION_API_KEY/DB_ID not set)"
```

**Solution:** Set both variables:
```bash
export LIVEPEER_NOTION_API_KEY=your_key
export LIVEPEER_NOTION_DB_ID=your_db_id
```

---

### Tasks Not Being Scheduled

**Symptom:** Scheduler runs but no tasks are scheduled

**Check 1: User filter mismatch**

The scheduler only schedules tasks assigned to `LIVEPEER_NOTION_USER_ID`.

```bash
# Default is "evan"
export LIVEPEER_NOTION_USER_ID=your_notion_name
```

**Check 2: Tasks missing required fields**

Tasks must have:
- **Due Date** set (required)
- **Rank** value (tasks without rank are skipped)
- **Status** not "Done", "Completed", "Canceled", or "Backlog"

**Check 3: Tasks already scheduled**

If tasks have a future "Scheduled Date", they won't be rescheduled unless past due.

**Debug:** Check scheduler status:
```bash
curl http://localhost:8000/api/v1/scheduler/status
```

---

### Scheduler Health Check Failing

**Symptom:** `/api/v1/scheduler/health` returns `healthy: false`

**Check 1: Service not initialized**
```json
{"status": "not_initialized", "healthy": false}
```

**Solution:** Set `LIVEPEER_NOTION_API_KEY` and `LIVEPEER_NOTION_DB_ID`.

**Check 2: Error state**
```json
{"status": "error", "healthy": false, "error": "..."}
```

**Solution:** Check the error message and Agent logs for details.

---

### Wrong Timezone

**Symptom:** Tasks scheduled at wrong times

**Check:** Timezone configuration
```bash
# Default is America/Chicago
export TIMEZONE=America/New_York  # or your timezone
```

Use IANA timezone names (e.g., `America/Los_Angeles`, `Europe/London`, `UTC`).

---

## Web App Issues

### Content Not Appearing on Desktop

**Symptom:** New markdown file doesn't show up

**Check 1: Content not generated**

```bash
cd apps/web
npm run generate-content
```

**Check 2: Invalid frontmatter**

Frontmatter must be valid YAML:
```markdown
---
title: My Title.md
---
```

Common issues:
- Missing `---` delimiters
- Missing `title:` field
- Special characters need quoting

**Check 3: File in wrong directory**

- Desktop files: `apps/web/src/content/`
- Thoughts: `apps/web/src/content/thoughts/`
- Projects: `apps/web/src/content/projects/`

---

### Chat Page Not Working

**Symptom:** Chat page shows error or doesn't load

**Check 1: Not authenticated**

Go to `/login` first and enter a valid bearer token.

**Check 2: Agent API not running/accessible**

The chat page calls the Agent API. Verify:
```bash
curl http://localhost:8000/api/v1/health
```

**Check 3: CORS issues (in browser console)**

The Agent API should allow the web app's origin. Check `app.py` CORS configuration.

---

### Styling Issues

**Symptom:** Components look broken

**Check 1: Tailwind not processing**

```bash
cd apps/web
npm run build
```

Look for Tailwind errors in the output.

**Check 2: CSS not loading**

Clear browser cache or hard refresh (Cmd+Shift+R / Ctrl+Shift+R).

---

## Deployment Issues

### Railway Build Failing

**Symptom:** Railway deployment fails at build step

**Check 1: Missing dependencies**

Ensure `requirements.txt` (agent) or `package.json` (web) lists all dependencies.

**Check 2: Build command wrong**

Check `railway.toml`:
```toml
[build]
builder = "nixpacks"
```

**Check 3: Environment variables missing**

Required vars must be set in Railway dashboard, not just locally.

---

### Railway Deploy Succeeds but App Doesn't Work

**Symptom:** Deploy shows success but app errors

**Check 1: Environment variables**

Go to Railway → Service → Variables and verify all required vars are set.

**Check 2: Check deploy logs**

Railway → Deployments → Latest → View Logs

**Check 3: Health check failing**

```bash
curl https://your-service.railway.app/api/v1/health
```

---

### Auto-Deploy Not Triggering

**Symptom:** Push to GitHub but Railway doesn't deploy

**Check 1: Correct branch**

- Web: must push to `desktop-app` branch
- Agent: must push to `main` branch

**Check 2: Railway connected to repo**

Railway → Settings → Check GitHub connection

---

## Local Development Issues

### `uv sync` Fails

**Symptom:** Can't install Python dependencies with uv

**Solution 1:** Install uv first
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Solution 2:** Fall back to pip
```bash
pip install -r requirements.txt
```

---

### `npm install` Fails

**Symptom:** Node dependencies won't install

**Check 1: Node version**
```bash
node --version  # Should be >= 18.0.0
```

**Check 2: Clear cache**
```bash
rm -rf node_modules package-lock.json
npm install
```

---

### Virtual Environment Issues

**Symptom:** Python can't find installed packages

**Solution:** Activate the virtual environment
```bash
# With uv
source .venv/bin/activate

# Or create one manually
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Tests Failing

**Symptom:** `pytest` returns errors

**Check 1: Wrong directory**
```bash
cd apps/agent
pytest tests/
```

**Check 2: Missing test dependencies**
```bash
pip install pytest pytest-asyncio
```

**Check 3: Environment not set up**

Some tests may require environment variables. Check test file for requirements.

---

## Getting Help

If you can't resolve an issue:

1. **Check the logs** - Most errors are logged with context
2. **Read the docs** - See related documentation files
3. **Check the code** - Look at error handling in the relevant file
4. **Test locally first** - Reproduce before debugging production

### Useful Commands

```bash
# Agent health
curl http://localhost:8000/api/v1/health

# Scheduler status
curl http://localhost:8000/api/v1/scheduler/status

# Test task creation
curl -X POST http://localhost:8000/api/v1/task_creator \
  -H "Content-Type: application/json" \
  -d '{"text_inputs": ["Test"], "dry_run": true}'

# Regenerate web content
cd apps/web && npm run generate-content

# Check Python environment
which python
python --version
pip list
```

### Log Locations

| Environment | Location |
|-------------|----------|
| Local (Agent) | Terminal stdout |
| Local (Web) | Terminal stdout |
| Railway | Dashboard → Deployments → Logs |
