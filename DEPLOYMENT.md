# Deployment Guide

## Architecture Overview

This monorepo contains three services deployed to Railway:

| Service | Domain | Description |
|---------|--------|-------------|
| **Desktop** | `evanm.xyz` | Retro Mac OS desktop personal website |
| **Web** | `agent.evanm.xyz` | Agent chat UI |
| **Agent** | (internal) | FastAPI backend for agent |
| **ZeroClaw** | (internal) | ZeroClaw AI agent gateway, proxied via Web |

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

## ZeroClaw Agent (`apps/zeroclaw/`)

ZeroClaw AI agent gateway, proxied through the web app at `/claw` behind bearer-token auth.

**Files:**
- `apps/zeroclaw/Dockerfile`
- `apps/zeroclaw/railway.toml`

**Environment Variables (set on the ZeroClaw service):**
```
ZEROCLAW_API_KEY=sk-or-...           # OpenRouter API key from openrouter.ai
ZEROCLAW_PROVIDER=openrouter         # or: anthropic, openai, ollama, etc.
ZEROCLAW_MODEL=anthropic/claude-sonnet-4-20250514
```

**Environment Variable (set on the Web service):**
```
ZEROCLAW_URL=http://zeroclaw.railway.internal:3000
```

**How it works:**
1. User visits `evanm.xyz/claw` (or `agent.evanm.xyz/claw`)
2. Next.js middleware checks for bearer token -- redirects to `/login` if missing
3. Authenticated requests to `/claw/api/*` are proxied to ZeroClaw's gateway at `/v1/*`
4. ZeroClaw exposes an OpenAI-compatible `/v1/chat/completions` endpoint

**Local Development:**
```bash
# Install and run ZeroClaw locally
git clone https://github.com/zeroclaw-labs/zeroclaw.git /tmp/zeroclaw
cd /tmp/zeroclaw && cargo build --release --locked && cargo install --path . --force --locked
zeroclaw onboard --api-key sk-or-YOUR_KEY --provider openrouter
zeroclaw gateway --port 3000

# Then in another terminal, set env and start the web app
ZEROCLAW_URL=http://localhost:3000 npm run web:dev
# Visit http://localhost:3001/claw
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

The script creates the `web`, `agent`, and `zeroclaw` services, then prints the env vars and config paths you need to set in the dashboard.

### Subsequent Deploys

After initial setup, deploys happen automatically on push. To deploy manually:

```bash
# Deploy a specific service
railway up --service web
railway up --service agent
railway up --service zeroclaw
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
