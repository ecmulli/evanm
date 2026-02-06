# CLAUDE.md

This file provides guidance for AI assistants working in the EvanM monorepo.

## Project Overview

Personal monorepo for **evanm.xyz** -- a retro Mac OS-themed personal website with an AI-powered task creation agent backend and Python job automation services. Deployed on Railway.

## Repository Structure

```
evanm/
├── apps/
│   ├── web/           # Next.js 15 frontend (evanm.xyz) - port 3001
│   ├── agent/         # FastAPI backend (AI task creator) - port 8000
│   └── jobs/          # Python automation scripts (scheduled tasks)
├── docs/              # Documentation per app
├── .github/workflows/ # CI/CD (mostly archived)
├── package.json       # Root monorepo config (npm workspaces)
├── AGENTS.md          # Content management guide for AI agents
├── CONTRIBUTING.md    # Development guidelines
└── DEPLOYMENT.md      # Railway deployment guide
```

## Quick Commands

### Root-Level (from repo root)

```bash
npm install              # Install all Node.js dependencies
npm run dev              # Run agent + web concurrently
npm run web:dev          # Run Next.js dev server (port 3001)
npm run web:build        # Build Next.js for production
npm run agent:run        # Run FastAPI agent server (port 8000)
npm run jobs:install     # Install Python deps for jobs
npm run jobs:run         # Run Python jobs
npm run clean            # Remove all node_modules
```

### Web App (`apps/web/`)

```bash
npm run dev              # Dev server with content generation (port 3001)
npm run build            # Generate content + Next.js build
npm run lint             # ESLint (next/core-web-vitals + next/typescript)
npm run generate-content # Rebuild generated-content.json from markdown
```

### Agent (`apps/agent/`)

```bash
pip install -r requirements.txt           # Install deps (or use uv)
pip install -e ".[dev]"                    # Install with dev deps
python app.py                             # Run server (port 8000)
python -m pytest tests/                   # Run tests
black app.py routes/ services/ models/ utils/ tests/   # Format
flake8 app.py routes/ services/ models/ utils/ tests/  # Lint
```

### Jobs (`apps/jobs/`)

```bash
pip install -r requirements.txt    # Install deps
python -m pytest                   # Run tests
```

## Tech Stack

| App | Language | Framework | Key Libraries |
|-----|----------|-----------|---------------|
| web | TypeScript | Next.js 15 (App Router) | React 19, Tailwind CSS 4, react-draggable, react-markdown, lucide-react |
| agent | Python 3.12+ | FastAPI | Hypercorn, OpenAI, Notion Client, Pydantic 2 |
| jobs | Python 3.8+ | schedule | requests, notion-client, openai |

## Code Conventions

### TypeScript/React (web)

- **Indentation**: 2 spaces
- **Naming**: camelCase for variables/functions, PascalCase for components
- **Imports**: Use `@/*` path alias (maps to `./src/*`)
- **State management**: React Context (ViewContext, WindowContext)
- **Components**: Functional components with hooks
- **Styling**: Tailwind CSS utility classes
- **Strict mode**: TypeScript strict enabled

### Python (agent, jobs)

- **Indentation**: 4 spaces
- **Line length**: 88 characters (black default)
- **Formatter**: black (`target-version = ['py312']` for agent)
- **Linter**: flake8 (ignores E203, W503)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Type hints**: Required -- use Pydantic models for request/response schemas
- **Docstrings**: Required for all public functions and classes
- **Testing**: pytest (test files in `tests/` directory)

### Commit Messages

Follow conventional commit format:
- `feat(web): add dark mode toggle`
- `fix(agent): handle timeout in task creation`
- `docs: update deployment guide`

## Architecture Details

### Web App Content System

Content is file-based markdown in `apps/web/src/content/`. The build pipeline:

1. Markdown files with frontmatter live in `src/content/`
2. `scripts/generate-content.js` reads them and produces `src/data/generated-content.json`
3. `src/data/content.ts` exports the generated data for use in components
4. Directories become desktop folders; `.md` files become desktop files

To add content: create a `.md` file in the appropriate `src/content/` subdirectory with `title` frontmatter. Run `npm run generate-content` or it runs automatically on `dev`/`build`.

### Agent API Architecture

- **Entry point**: `apps/agent/app.py` (FastAPI + Hypercorn)
- **Routes**: `routes/task_creator.py`, `routes/scheduler.py`
- **Services**: `services/task_creation.py` (OpenAI + Notion), `services/task_scheduler.py`
- **Models**: `models/task_models.py` (Pydantic schemas)
- **Auth**: Bearer token via `utils/auth.py`
- **Config**: Environment-based via `utils/config.py`
- **Docs**: Available at `/docs` (Swagger) and `/redoc` when running

### Key API Endpoints

- `POST /api/v1/task_creator` -- Create tasks via AI
- `GET /api/v1/scheduler/status` -- Scheduler status
- `POST /api/v1/scheduler/run` -- Trigger scheduling cycle
- `GET /api/v1/health` -- Health check

### Deployment

- **Platform**: Railway.io
- **Web**: Dockerized Next.js, deployed to `evanm.xyz`
- **Agent**: Dockerized FastAPI, internal Railway service
- **Web proxies to Agent**: `next.config.ts` rewrites `/api/*` to the agent backend via `BACKEND_URL`

## Environment Variables

### Agent (required)

- `BEARER_TOKEN` -- API authentication
- `OPENAI_API_KEY` -- OpenAI API access
- `HUB_NOTION_API_KEY` / `HUB_NOTION_DB_ID` -- Primary Notion workspace

### Agent (optional)

- `LIVEPEER_NOTION_API_KEY` / `LIVEPEER_NOTION_DB_ID` -- Livepeer workspace + scheduler
- `VANQUISH_NOTION_API_KEY` / `VANQUISH_NOTION_DB_ID` -- Vanquish workspace
- `LIVEPEER_NOTION_USER_ID` -- Scheduler assignee filter (default: "evan")
- `WORK_START_HOUR` / `WORK_END_HOUR` -- Scheduler work hours (default: 9-17)
- `TIMEZONE` -- Scheduler timezone (default: "America/Chicago")
- `SCHEDULER_INTERVAL_MINUTES` -- Background scheduling interval (default: 10)

### Web

- `BACKEND_URL` -- Agent backend URL (default: `http://localhost:8000`)
- `BEARER_TOKEN` -- For authenticated requests
- `NODE_ENV` -- production/development

## Testing

Only the agent app currently has tests:

```bash
cd apps/agent && python -m pytest tests/ -v
```

The web app has no test suite -- rely on `npm run lint` and `npm run build` to catch issues.

## Things to Watch Out For

- `generated-content.json` is committed to git. After changing content files, run `npm run generate-content` and commit the updated JSON.
- The root `package.json` workspaces list includes `apps/desktop` (legacy name for `apps/web`). Both names may appear in docs.
- The agent uses `venv/bin/python` in some root scripts -- Python virtualenv may need to be set up locally.
- The Guestbook/Stickies feature exists in code but is hidden (needs persistence backend). See `AGENTS.md` for details.
- Never commit `.env` files -- they contain API keys and secrets.
