# Deployment Guide

## Architecture Overview

This monorepo contains the following services deployed to Railway:

| Service | Domain | Description |
|---------|--------|-------------|
| **Desktop** | `evanm.xyz` | Retro Mac OS desktop personal website |
| **Web** | `agent.evanm.xyz` | Agent chat UI + Task Dashboard |
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

### Initial Setup (one-time)

Railway doesn't auto-discover `railway.toml` files -- each service must be created once. Use the setup script to do it from the CLI instead of clicking through the dashboard:

```bash
# Install Railway CLI and log in
npm install -g @railway/cli
railway login

# Link to your project (or create one)
railway link

# Create all services
./scripts/railway-setup.sh
```

The script creates the services and prints the env vars and config paths you need to set in the dashboard.

### Subsequent Deploys

After initial setup, deploys happen automatically on push. To deploy manually:

```bash
# Deploy a specific service
railway up --service web
railway up --service agent
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
