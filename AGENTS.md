# AI Agent Guide for evanm.xyz Monorepo

This guide helps AI agents (Cursor, Claude, etc.) understand and work with the evanm.xyz monorepo.

## Quick Navigation

| What you're doing | Go to |
|-------------------|-------|
| Add/edit website content | [Web Content Management](#web-content-management) |
| Modify the API | [Agent API](#agent-api) |
| Work with the scheduler | [Task Scheduler](#task-scheduler) |
| Understand the architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Common tasks reference | [docs/COMMON_TASKS.md](docs/COMMON_TASKS.md) |
| Troubleshooting | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

## Repository Overview

```
evanm/
├── apps/
│   ├── web/          # Next.js website (retro Mac OS desktop)
│   ├── agent/        # FastAPI backend (task creation + scheduler)
│   └── jobs/         # Python sync scripts (archived)
├── docs/             # Detailed documentation
├── AGENTS.md         # This file (main entry point)
└── CONTRIBUTING.md   # Development guidelines
```

### Architecture at a Glance

```
┌─────────────────┐     ┌─────────────────┐
│   evanm.xyz     │     │   Agent API     │
│   (Next.js)     │────▶│   (FastAPI)     │
│                 │     │                 │
│ • Desktop UI    │     │ • Task Creator  │
│ • Chat page     │     │ • Scheduler     │
│ • Login         │     │                 │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │     Notion      │
                        │   Databases     │
                        └─────────────────┘
```

### Key URLs

| Environment | Web | Agent API |
|-------------|-----|-----------|
| Production | evanm.xyz | agent.evanm.xyz |
| Local | localhost:3000 | localhost:8000 |

---

## Web Content Management

The website is a Next.js app with a retro Mac OS desktop interface. Content appears as files and folders on the desktop.

### Content Directory Structure

```
apps/web/src/content/
├── about-me.md               → Desktop file "About Me.md"
├── site-inspiration.md       → Desktop file "Site Inspiration.md"
├── projects/                 → Desktop folder "Projects"
│   ├── evanm-xyz.md          → File inside Projects folder
│   └── task-agent.md         → File inside Projects folder
└── thoughts/                 → Desktop folder "Thoughts"
    ├── on-simplicity.md      → File inside Thoughts folder
    ├── digital-gardens.md    → File inside Thoughts folder
    └── hello-world.md        → File inside Thoughts folder
```

**Adding content is as simple as adding a `.md` file to the appropriate directory.**

### File Format

Each `.md` file uses frontmatter + markdown content:

```markdown
---
title: Display Title.md
---
# Your Title

Your **markdown** content here with *formatting*!

- Bullet points
- [Links](https://example.com)
- Images, code blocks, etc.
```

### Markdown Features

Full markdown support including:

- **Bold** and *italic* text
- [Links](https://example.com) (open in new tab)
- Headers (`#`, `##`, `###`)
- Bullet and numbered lists
- `inline code` and code blocks
- > Blockquotes
- Horizontal rules (`---`)
- Images: `![alt text](/images/photo.png)`

### Images

Place images in `apps/web/public/images/` and reference them:

```markdown
![Screenshot](/images/my-screenshot.png)
```

### Content Examples

#### Adding a New Thought

Create `apps/web/src/content/thoughts/my-new-thought.md`:

```markdown
---
title: My New Thought.md
---
# My New Thought

*January 24, 2026*

Your thought content here with **bold** and *italic* text.

> A blockquote for emphasis

- Point one
- Point two
```

#### Adding a New Project

Create `apps/web/src/content/projects/my-project.md`:

```markdown
---
title: My Project.md
---
# My Project Name

**Status:** Active  
**Tech:** React, Node.js, PostgreSQL

## Description

What the project does and why it matters.

![Screenshot](/images/my-project.png)

## Links

- [Live Site](https://example.com)
- [Source Code](https://github.com/user/repo)

---

*Tagline here.*
```

#### Adding a New Folder

Create a new directory: `apps/web/src/content/my-folder/`

Then add `.md` files inside it. The folder will automatically appear on the desktop.

### Content Quick Reference

| Task | Action |
|------|--------|
| Add a thought | Create `src/content/thoughts/filename.md` |
| Add a project | Create `src/content/projects/filename.md` |
| Add desktop file | Create `src/content/filename.md` |
| Add new folder | Create `src/content/foldername/` directory |
| Add an image | Place in `public/images/`, reference as `/images/name.png` |
| Edit About Me | Edit `src/content/about-me.md` |

### How Content Works

1. Content files live in `apps/web/src/content/`
2. `npm run generate-content` reads all files and creates `generated-content.json`
3. The app imports this JSON at build time
4. Directory structure → Desktop folders
5. `.md` files → Files inside folders (or on desktop if at root)

The `generate-content` script runs automatically before `dev` and `build`.

---

## Agent API

The Agent API is a FastAPI backend providing AI-powered task creation and automatic scheduling.

### Location

```
apps/agent/
├── app.py                  # FastAPI application entry point
├── routes/                 # API endpoints
│   ├── task_creator.py     # POST /api/v1/task_creator
│   └── scheduler.py        # /api/v1/scheduler/*
├── services/               # Business logic
│   ├── task_creation.py    # Task creation with OpenAI + Notion
│   └── task_scheduler.py   # Scheduling logic
├── scheduler/              # Scheduling algorithm
│   ├── scheduling_algorithm.py
│   └── time_slots.py
├── models/                 # Pydantic models
│   └── task_models.py
└── utils/                  # Config, auth
    ├── config.py
    └── auth.py
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/api/v1` | GET | Available endpoints |
| `/api/v1/health` | GET | Health check |
| `/api/v1/auth/validate` | GET | Validate bearer token |
| `/api/v1/task_creator` | POST | Create task via AI |
| `/api/v1/scheduler/status` | GET | Scheduler status |
| `/api/v1/scheduler/run` | POST | Trigger scheduling |
| `/api/v1/scheduler/health` | GET | Scheduler health |

### Task Creation

The task creator uses OpenAI to parse natural language into structured tasks and creates them in Notion.

**Request:**
```json
{
  "text_inputs": ["Fix the urgent bug by tomorrow. Livepeer, 2 hours."],
  "image_urls": ["https://example.com/screenshot.png"],
  "suggested_workspace": "Livepeer",
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Task created successfully",
  "task_id": "notion-page-id",
  "task_url": "https://notion.so/...",
  "parsed_data": {
    "task_name": "Fix urgent bug",
    "workspace": "Livepeer",
    "priority": "ASAP",
    "estimated_hours": 2,
    "due_date": "2025-09-02"
  },
  "dry_run": false
}
```

### Common API Modifications

| Task | Files to modify |
|------|-----------------|
| Add new endpoint | Create in `routes/`, register in `app.py` |
| Modify task parsing | `services/task_creation.py` |
| Change Notion integration | `services/task_creation.py` |
| Add new model | `models/task_models.py` |
| Update config | `utils/config.py` |

### Environment Variables

**Required:**
```bash
OPENAI_API_KEY=your_key
HUB_NOTION_API_KEY=your_key
HUB_NOTION_DB_ID=your_db_id
```

**Optional:**
```bash
BEARER_TOKEN=auth_token          # If unset, auth bypassed
PORT=8000                        # Default: 8000
DEBUG=false                      # Default: false
LIVEPEER_NOTION_API_KEY=key      # External workspace
LIVEPEER_NOTION_DB_ID=id
LIVEPEER_NOTION_USER_ID=evan     # For scheduler filtering
```

See [docs/agent/Config.md](docs/agent/Config.md) for full configuration reference.

---

## Task Scheduler

The scheduler automatically assigns tasks to calendar time slots based on priority.

### How It Works

1. Runs as a background task every 10 minutes (configurable)
2. Fetches tasks from Notion that:
   - Are assigned to the configured user
   - Have a due date
   - Are not completed/canceled/backlog
3. Sorts by Rank column (lower = higher priority)
4. Assigns to available work hour slots (default 9 AM - 5 PM)
5. Updates Notion with scheduled date/time

### Scheduler Configuration

```bash
SCHEDULER_INTERVAL_MINUTES=10    # How often to run
WORK_START_HOUR=9                # Work day start (24h)
WORK_END_HOUR=17                 # Work day end (24h)
SLOT_DURATION_MINUTES=15         # Time slot size
SCHEDULE_DAYS_AHEAD=7            # How far to look ahead
TIMEZONE=America/Chicago         # Timezone for scheduling
```

### Scheduler Endpoints

```bash
# Get status
curl http://localhost:8000/api/v1/scheduler/status

# Manually trigger
curl -X POST http://localhost:8000/api/v1/scheduler/run

# Health check
curl http://localhost:8000/api/v1/scheduler/health
```

### Required Notion Properties

Your Notion database must have:
- **Rank** (Number): Priority (lower = higher)
- **Duration** (Number): Minutes
- **Due Date** (Date): Required
- **Assignee** (People): Required
- **Status** (Select): Must include "Done"
- **Scheduled Date** (Date with time): Auto-populated

See [docs/agent/Scheduler.md](docs/agent/Scheduler.md) for full scheduler documentation.

---

## Jobs (Sync Scripts)

Located in `apps/jobs/`. Contains Python scripts for syncing tasks between Notion and Motion.

**Status:** Currently archived in `apps/jobs/archive/`

### Available Jobs

- **Notion Sync** (`archive/notion/`): Sync between Hub and external Notion workspaces
- **Motion Sync** (`archive/motion/`): Bidirectional Notion ↔ Motion sync

See [docs/jobs/README.md](docs/jobs/README.md) for details.

---

## Local Development

### Web App

```bash
cd apps/web
npm install
npm run dev
# Visit http://localhost:3000
```

### Agent API

```bash
cd apps/agent
uv sync                    # or: pip install -r requirements.txt
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
python app.py
# API at http://localhost:8000, docs at /docs
```

### Running Tests

```bash
# Agent tests
cd apps/agent
pytest tests/

# Web tests (if configured)
cd apps/web
npm test
```

---

## Deployment

### Railway (Production)

Both apps deploy via Railway:

- **Web**: Auto-deploys from `desktop-app` branch
- **Agent**: Auto-deploys from `main` branch

### Deploying Changes

1. Make changes
2. Commit to appropriate branch
3. Push to GitHub
4. Railway auto-deploys

### Updating Environment Variables

1. Go to Railway dashboard
2. Select the service
3. Go to Variables tab
4. Add/update variables
5. Redeploy

---

## File Structure Reference

### Web App (`apps/web/`)

```
├── scripts/
│   └── generate-content.js    # Builds content JSON
├── src/
│   ├── content/               # ⭐ CONTENT LIVES HERE
│   ├── data/
│   │   ├── content.ts         # Exports content
│   │   └── generated-content.json
│   ├── app/
│   │   ├── page.tsx           # Homepage (Desktop)
│   │   ├── chat/page.tsx      # Agent chat UI
│   │   └── login/page.tsx     # Auth page
│   └── components/
│       ├── Desktop.tsx        # Main container
│       └── apps/              # Window components
```

### Agent API (`apps/agent/`)

```
├── app.py                     # FastAPI entry point
├── routes/                    # API endpoints
├── services/                  # Business logic
├── scheduler/                 # Scheduling algorithm
├── models/                    # Pydantic models
└── utils/                     # Config, auth
```

---

## TODO: Guestbook Feature (Paused)

**Status:** Hidden from desktop, awaiting persistence implementation

### What Exists

The Guestbook/Stickies feature is fully built in `src/components/apps/Stickies.tsx`:
- Form to submit name + message
- Display list of notes with timestamps
- Retro sticky note styling
- Works perfectly in-memory

### The Problem

Notes don't persist - they're stored in React state and lost on page refresh.

### Recommended Solutions (Simplest First)

1. **Upstash Redis** (Recommended)
   - Free tier: 10k commands/day
   - Simple REST API, no SDK needed
   - Store notes as JSON string with key `guestbook`
   - Setup: https://upstash.com

2. **Cloudflare R2**
   - S3-compatible blob storage
   - Free tier: 10GB storage, 10M reads/mo
   - Store a `guestbook.json` file

3. **JSONBin.io**
   - Free tier: 10k requests/mo
   - Simple REST API for JSON storage

### To Re-enable

1. Choose a persistence solution
2. Add service credentials to `.env`
3. Update `Stickies.tsx` to fetch on mount and POST new entries
4. Uncomment the guestbook icon in `scripts/generate-content.js`:
   ```javascript
   desktopIcons.push({
     id: 'guestbook-icon',
     label: 'Guestbook',
     iconType: 'app',
     appType: 'stickies',
   });
   ```
5. Run `npm run generate-content` and rebuild

### Files Involved

- `src/components/apps/Stickies.tsx` - The guestbook UI
- `src/data/content.ts` - Has `initialNotes` mock data
- `scripts/generate-content.js` - Icon is commented out here
- `src/types/window.ts` - `StickyNote` type definition

---

## Additional Documentation

- [Quick Start](docs/QUICK_START.md) - Fast onboarding
- [Common Tasks](docs/COMMON_TASKS.md) - Step-by-step guides
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Agent API Reference](docs/agent/README.md) - Full API docs
- [Scheduler Reference](docs/agent/Scheduler.md) - Scheduler details
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues
