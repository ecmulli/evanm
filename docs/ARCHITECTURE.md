# Architecture Overview

This document explains the system architecture and helps agents understand when to modify which components.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────────────┐                    ┌─────────────────┐     │
│   │   evanm.xyz     │                    │  Notion Calendar│     │
│   │   (Next.js)     │                    │                 │     │
│   │                 │                    │  (Views tasks   │     │
│   │  • Desktop UI   │                    │   scheduled by  │     │
│   │  • /chat        │                    │   the system)   │     │
│   │  • /login       │                    │                 │     │
│   └────────┬────────┘                    └────────▲────────┘     │
│            │                                      │               │
│            │ API calls                            │ Calendar sync │
│            ▼                                      │               │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                     Agent API (FastAPI)                  │   │
│   │                                                          │   │
│   │  ┌──────────────────┐    ┌──────────────────────┐       │   │
│   │  │  Task Creator    │    │     Scheduler        │       │   │
│   │  │                  │    │                      │       │   │
│   │  │  • Parse text    │    │  • Background task   │       │   │
│   │  │  • OCR images    │    │  • Every 10 min      │       │   │
│   │  │  • AI synthesis  │    │  • Assign time slots │       │   │
│   │  │  • Create tasks  │    │  • Update Notion     │       │   │
│   │  └────────┬─────────┘    └──────────┬───────────┘       │   │
│   │           │                          │                   │   │
│   │           └──────────┬───────────────┘                   │   │
│   │                      │                                   │   │
│   └──────────────────────┼───────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    External Services                     │   │
│   │                                                          │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│   │  │   OpenAI     │  │    Notion    │  │    Notion    │   │   │
│   │  │              │  │   (Hub DB)   │  │  (Livepeer)  │   │   │
│   │  │  • GPT-4o    │  │              │  │              │   │   │
│   │  │  • Vision    │  │  Task store  │  │  Work tasks  │   │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│   │                                                          │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Components

### Web App (Next.js)

**Location:** `apps/web/`

**Purpose:** Personal website with retro Mac OS desktop interface

**Key Features:**
- Static content from markdown files
- Chat interface for task creation
- Authentication via bearer token

**Technology:**
- Next.js 14+ (App Router)
- React
- Tailwind CSS
- TypeScript

**Data Flow:**
1. Content files → `generate-content.js` → JSON → React components
2. Chat page → API calls → Agent API → Notion

### Agent API (FastAPI)

**Location:** `apps/agent/`

**Purpose:** AI-powered task creation and automatic scheduling

**Key Features:**
- Natural language task parsing
- Image OCR for screenshots
- Automatic calendar scheduling
- Notion integration

**Technology:**
- Python 3.8+
- FastAPI
- Pydantic
- OpenAI API
- Notion API

**Subcomponents:**

| Component | Location | Purpose |
|-----------|----------|---------|
| Routes | `routes/` | HTTP endpoints |
| Services | `services/` | Business logic |
| Scheduler | `scheduler/` | Scheduling algorithm |
| Models | `models/` | Data structures |
| Utils | `utils/` | Config, auth |

### Jobs (Python Scripts)

**Location:** `apps/jobs/`

**Purpose:** Sync tasks between Notion workspaces and Motion

**Status:** Currently archived in `apps/jobs/archive/`

**Features:**
- Bidirectional Notion sync
- Motion ↔ Notion sync

---

## Data Flow Diagrams

### Task Creation Flow

```
User Input (text/image)
        │
        ▼
┌───────────────────┐
│  POST /task_creator│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────┐
│  Extract URLs     │     │  OCR Images   │
│  from text        │     │  (OpenAI)     │
└─────────┬─────────┘     └───────┬───────┘
          │                       │
          └───────────┬───────────┘
                      │
                      ▼
          ┌───────────────────┐
          │  Synthesize Task  │
          │  (OpenAI GPT-4)   │
          │                   │
          │  • task_name      │
          │  • priority       │
          │  • due_date       │
          │  • description    │
          │  • etc.           │
          └─────────┬─────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  [dry_run=true]          [dry_run=false]
        │                       │
        ▼                       ▼
  Return parsed           Create Notion
  data only               page in database
                                │
                                ▼
                          Return task_id
                          and task_url
```

### Scheduling Flow

```
Every 10 minutes (or manual trigger)
                │
                ▼
┌───────────────────────────────┐
│  Fetch tasks from Notion       │
│                                │
│  Filters:                      │
│  • Assigned to user            │
│  • Has due date                │
│  • Not completed/backlog       │
│  • Has rank value              │
└─────────────┬─────────────────┘
              │
              ▼
┌───────────────────────────────┐
│  Generate time slots           │
│                                │
│  • Work hours only (9-5)       │
│  • Weekdays only               │
│  • 15-minute slots             │
│  • Next 7 days                 │
└─────────────┬─────────────────┘
              │
              ▼
┌───────────────────────────────┐
│  Sort tasks by Rank            │
│  (lower = higher priority)     │
└─────────────┬─────────────────┘
              │
              ▼
┌───────────────────────────────┐
│  For each task:                │
│                                │
│  1. Calculate slots needed     │
│  2. Find available slots       │
│  3. Prefer before due date     │
│  4. Assign task                │
│  5. Mark slots as used         │
└─────────────┬─────────────────┘
              │
              ▼
┌───────────────────────────────┐
│  Update Notion                 │
│                                │
│  Set "Scheduled Date" property │
└───────────────────────────────┘
```

---

## When to Modify What

### Decision Tree

```
What are you trying to do?
│
├─► Add/edit website content
│   └─► apps/web/src/content/*.md
│
├─► Change website appearance
│   ├─► Layout → apps/web/src/components/Desktop.tsx
│   ├─► Windows → apps/web/src/components/WindowFrame.tsx
│   └─► Styles → apps/web/src/app/globals.css
│
├─► Modify chat functionality
│   └─► apps/web/src/app/chat/page.tsx
│
├─► Change API behavior
│   ├─► Endpoints → apps/agent/routes/
│   ├─► Business logic → apps/agent/services/
│   └─► Data models → apps/agent/models/
│
├─► Change task parsing
│   └─► apps/agent/services/task_creation.py
│
├─► Change scheduling
│   ├─► Algorithm → apps/agent/scheduler/scheduling_algorithm.py
│   ├─► Time slots → apps/agent/scheduler/time_slots.py
│   └─► Service → apps/agent/services/task_scheduler.py
│
├─► Add environment variable
│   └─► apps/agent/utils/config.py
│
└─► Change deployment
    └─► railway.toml in respective app
```

### Quick Reference Table

| Goal | Primary File(s) | Secondary File(s) |
|------|-----------------|-------------------|
| Add blog post | `content/thoughts/*.md` | - |
| Add project | `content/projects/*.md` | - |
| New API endpoint | `routes/*.py` | `app.py`, `models/` |
| Modify task parsing | `services/task_creation.py` | - |
| Change scheduling logic | `scheduler/scheduling_algorithm.py` | `services/task_scheduler.py` |
| Add config option | `utils/config.py` | `app.py` |
| Change desktop layout | `components/Desktop.tsx` | `globals.css` |
| Modify chat UI | `app/chat/page.tsx` | - |
| Add authentication | `utils/auth.py`, `middleware.ts` | - |

---

## Technology Stack

### Web App

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14+ (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Deployment | Railway |

### Agent API

| Layer | Technology |
|-------|------------|
| Framework | FastAPI |
| Language | Python 3.8+ |
| Validation | Pydantic |
| AI | OpenAI API (GPT-4, Vision) |
| Database | Notion API |
| Server | Hypercorn (ASGI) |
| Deployment | Railway |

### External Services

| Service | Purpose |
|---------|---------|
| OpenAI | Task synthesis, OCR |
| Notion | Task storage, calendar |
| Railway | Hosting, deployment |
| GitHub | Source control |

---

## Directory Structure

```
evanm/
├── apps/
│   ├── web/                      # Next.js website
│   │   ├── src/
│   │   │   ├── app/              # Pages (App Router)
│   │   │   │   ├── page.tsx      # Homepage
│   │   │   │   ├── chat/         # Chat page
│   │   │   │   └── login/        # Login page
│   │   │   ├── components/       # React components
│   │   │   ├── content/          # Markdown content
│   │   │   ├── data/             # Generated JSON
│   │   │   ├── context/          # React contexts
│   │   │   ├── hooks/            # Custom hooks
│   │   │   ├── types/            # TypeScript types
│   │   │   └── utils/            # Utilities
│   │   ├── public/               # Static assets
│   │   └── scripts/              # Build scripts
│   │
│   ├── agent/                    # FastAPI backend
│   │   ├── app.py                # Application entry
│   │   ├── routes/               # API endpoints
│   │   ├── services/             # Business logic
│   │   ├── scheduler/            # Scheduling core
│   │   ├── models/               # Pydantic models
│   │   ├── utils/                # Config, auth
│   │   └── tests/                # Test files
│   │
│   └── jobs/                     # Sync scripts
│       └── archive/              # Archived jobs
│
├── docs/                         # Documentation
│   ├── agent/                    # API docs
│   ├── web/                      # Web docs
│   └── jobs/                     # Jobs docs
│
├── AGENTS.md                     # AI agent guide
├── CONTRIBUTING.md               # Dev guidelines
└── README.md                     # Project overview
```

---

## Deployment Architecture

```
GitHub Repository
        │
        ├───────────────────┬───────────────────┐
        │                   │                   │
        ▼                   ▼                   │
   main branch        desktop-app branch        │
        │                   │                   │
        ▼                   ▼                   │
┌───────────────┐   ┌───────────────┐          │
│   Railway     │   │   Railway     │          │
│   (Agent)     │   │   (Web)       │          │
│               │   │               │          │
│  agent.       │   │  evanm.xyz    │          │
│  evanm.xyz    │   │               │          │
└───────────────┘   └───────────────┘          │
                                                │
                    Environment Variables ◄─────┘
                    (stored in Railway)
```

### Branch Strategy

| Branch | Purpose | Deploys To |
|--------|---------|------------|
| `main` | Agent API development | agent.evanm.xyz |
| `desktop-app` | Web app development | evanm.xyz |

---

## Security Model

### Authentication

- **Web → Agent:** Bearer token in `Authorization` header
- **Agent → Notion:** Notion integration tokens (per workspace)
- **Agent → OpenAI:** API key

### Environment Variables

All secrets are stored in Railway and injected at runtime. Never commit secrets to the repository.

### CORS

Agent API allows all origins (configured for production appropriately).

---

## Scalability Considerations

### Current State

- Single Railway instance per service
- Scheduler runs in-process (same as API)
- Notion as the only database

### Future Considerations

- Separate scheduler into its own service
- Add caching layer (Redis) for frequent queries
- Consider PostgreSQL for application data
- Add rate limiting for API endpoints
