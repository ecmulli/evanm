# Deployment Guide

## Architecture Overview

This monorepo contains three services deployed to Railway:

| Service | Domain | Description |
|---------|--------|-------------|
| **Desktop** | `evanm.xyz` | Retro Mac OS desktop personal website |
| **Web** | `agent.evanm.xyz` | Agent chat UI |
| **Agent** | (internal) | FastAPI backend for agent |

## Railway Deployment Setup

### Prerequisites
- Railway account
- Domains configured:
  - `evanm.xyz` → Desktop service
  - `agent.evanm.xyz` → Web service

---

## Desktop App (`apps/desktop/`)

The main personal website with retro Mac OS aesthetics.

**Files:**
- `apps/desktop/Dockerfile`
- `apps/desktop/railway.toml`

**Environment Variables:** None required

**Local Development:**
```bash
cd apps/desktop
npm install
npm run dev
# Opens at http://localhost:3002
```

---

## Web App (`apps/web/`)

The agent chat frontend.

**Files:**
- `apps/web/Dockerfile`
- `apps/web/railway.toml`

**Environment Variables:**
```
BEARER_TOKEN=your_secure_token_here
NODE_ENV=production
```

**Local Development:**
```bash
cd apps/web
npm install
npm run dev
# Opens at http://localhost:3001
```

---

## Agent Backend (`apps/agent/`)

FastAPI Python server for task creation.

**Files:**
- `apps/agent/Dockerfile`
- `apps/agent/railway.toml`

**Environment Variables:**
```
BEARER_TOKEN=your_secure_token_here
OPENAI_API_KEY=your_openai_key
HUB_NOTION_API_KEY=your_notion_key
HUB_NOTION_DB_ID=your_notion_db_id
LIVEPEER_NOTION_API_KEY=optional
LIVEPEER_NOTION_DB_ID=optional
VANQUISH_NOTION_API_KEY=optional
VANQUISH_NOTION_DB_ID=optional
```

**Local Development:**
```bash
cd apps/agent
pip install -r requirements.txt
python app.py
# Runs at http://localhost:8000
```

---

## Deploying to Railway

### Option 1: Railway Dashboard
1. Connect your GitHub repo to Railway
2. Create a new service for each app
3. Set the root directory or use the railway.toml config
4. Configure environment variables
5. Assign custom domains

### Option 2: Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

---

## Domain Configuration

1. **Desktop** (`evanm.xyz`):
   - Deploy desktop service
   - Add custom domain `evanm.xyz` in Railway
   - Configure DNS: CNAME to Railway's provided domain

2. **Web** (`agent.evanm.xyz`):
   - Deploy web service
   - Add custom domain `agent.evanm.xyz` in Railway
   - Configure DNS: CNAME to Railway's provided domain

3. **Agent Backend**:
   - Internal service, accessed via Railway's private networking
   - Or expose via Railway URL for web app to proxy to

---

## Local Development (All Services)

From the root directory:
```bash
# Install all dependencies
npm install

# Run all services (if configured in root package.json)
npm run dev
```

Or run individually:
```bash
# Desktop
npm run desktop:dev

# Web
npm run web:dev

# Agent
npm run agent
```
