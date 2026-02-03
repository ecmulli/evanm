# Quick Start for AI Agents

Fast onboarding guide for AI agents working on this repository.

## 5-Second Context

- **What:** Personal website + AI task management tools
- **Stack:** Next.js (web), FastAPI (agent), Python (jobs)
- **Deploys:** Railway (auto-deploy on push)

## Repository Structure

```
apps/
├── web/      # Next.js website (retro Mac OS desktop)
├── agent/    # FastAPI backend (task creation + scheduler)
└── jobs/     # Python sync scripts (archived)
```

## First Steps by Task Type

### "Add content to the website"

1. Navigate to `apps/web/src/content/`
2. Create/edit a `.md` file in the appropriate folder
3. Use frontmatter format:
   ```markdown
   ---
   title: My Title.md
   ---
   # Content here
   ```

**Key paths:**
- Thoughts: `apps/web/src/content/thoughts/`
- Projects: `apps/web/src/content/projects/`
- Desktop files: `apps/web/src/content/`

### "Modify the API"

1. Navigate to `apps/agent/`
2. Routes are in `routes/`
3. Business logic is in `services/`
4. Data models in `models/`

**Key files:**
- Main app: `app.py`
- Task creation: `services/task_creation.py`
- Scheduler: `services/task_scheduler.py`

### "Fix something in the chat UI"

Edit `apps/web/src/app/chat/page.tsx`

### "Work on the scheduler"

- Algorithm: `apps/agent/scheduler/scheduling_algorithm.py`
- Time slots: `apps/agent/scheduler/time_slots.py`
- Service: `apps/agent/services/task_scheduler.py`
- Routes: `apps/agent/routes/scheduler.py`

### "Update website components"

Components are in `apps/web/src/components/`:
- `Desktop.tsx` - Main desktop container
- `WindowFrame.tsx` - Window wrapper
- `apps/` - Individual app windows (Folder, SimpleText, Stickies)

---

## Environment Variables

### Agent API (Required)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `HUB_NOTION_API_KEY` | Notion integration token |
| `HUB_NOTION_DB_ID` | Notion database ID |

### Agent API (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `BEARER_TOKEN` | (none) | Auth token (if unset, auth bypassed) |
| `PORT` | 8000 | Server port |
| `DEBUG` | false | Enable debug logging |
| `LIVEPEER_NOTION_API_KEY` | - | External workspace key |
| `LIVEPEER_NOTION_DB_ID` | - | External workspace DB |
| `LIVEPEER_NOTION_USER_ID` | evan | User for scheduler filtering |

### Scheduler (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `SCHEDULER_INTERVAL_MINUTES` | 10 | How often scheduler runs |
| `WORK_START_HOUR` | 9 | Work day start (24h) |
| `WORK_END_HOUR` | 17 | Work day end (24h) |
| `SLOT_DURATION_MINUTES` | 15 | Time slot size |
| `SCHEDULE_DAYS_AHEAD` | 7 | Planning horizon |
| `TIMEZONE` | America/Chicago | Scheduling timezone |

---

## Local Development

### Web App

```bash
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```

### Agent API

```bash
cd apps/agent
uv sync                      # or: pip install -r requirements.txt
source .venv/bin/activate    # Windows: .venv\Scripts\activate
python app.py
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

---

## Quick Commands

### Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create task (dry run)
curl -X POST http://localhost:8000/api/v1/task_creator \
  -H "Content-Type: application/json" \
  -d '{"text_inputs": ["Test task"], "dry_run": true}'

# Scheduler status
curl http://localhost:8000/api/v1/scheduler/status
```

### Generate content

```bash
cd apps/web
npm run generate-content
```

### Run tests

```bash
cd apps/agent
pytest tests/
```

---

## Key Files Reference

| Purpose | Path |
|---------|------|
| Main agent entry | `apps/agent/app.py` |
| Task creation logic | `apps/agent/services/task_creation.py` |
| Scheduler logic | `apps/agent/services/task_scheduler.py` |
| API models | `apps/agent/models/task_models.py` |
| Config | `apps/agent/utils/config.py` |
| Web homepage | `apps/web/src/app/page.tsx` |
| Chat page | `apps/web/src/app/chat/page.tsx` |
| Desktop component | `apps/web/src/components/Desktop.tsx` |
| Content directory | `apps/web/src/content/` |
| Content generator | `apps/web/scripts/generate-content.js` |

---

## Deployment

| App | Branch | Platform |
|-----|--------|----------|
| Web | `desktop-app` | Railway |
| Agent | `main` | Railway |

Push to the appropriate branch and Railway auto-deploys.

---

## Next Steps

- [AGENTS.md](../AGENTS.md) - Comprehensive guide
- [Common Tasks](./COMMON_TASKS.md) - Step-by-step guides
- [Architecture](./ARCHITECTURE.md) - System design
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues
