# ZeroClaw Service

A ZeroClaw AI agent gateway deployed as a Railway service behind the existing bearer-token auth.

## Architecture

```
Browser → /zeroclaw (Next.js auth middleware) → /zeroclaw/api/* (proxy) → ZeroClaw gateway :3000
```

The Next.js web app proxies authenticated requests from `/zeroclaw/api/*` to the ZeroClaw gateway's OpenAI-compatible `/v1/chat/completions` endpoint.

## Environment Variables

Set these in the Railway dashboard:

| Variable | Required | Description |
|----------|----------|-------------|
| `ZEROCLAW_API_KEY` | Yes | API key for your AI provider (OpenRouter, OpenAI, etc.) |
| `ZEROCLAW_PROVIDER` | No | Provider name (default: `openrouter`) |
| `ZEROCLAW_MODEL` | No | Model to use (default: `anthropic/claude-sonnet-4-20250514`) |

The web app needs the ZeroClaw service URL:

| Variable | Required | Where |
|----------|----------|-------|
| `ZEROCLAW_URL` | Yes | Set on the **web** service, pointing to ZeroClaw's internal Railway URL |

## Local Development

```bash
# Option 1: Run ZeroClaw directly (requires Rust)
git clone https://github.com/zeroclaw-labs/zeroclaw.git /tmp/zeroclaw
cd /tmp/zeroclaw && cargo build --release --locked
cargo install --path . --force --locked
zeroclaw onboard --interactive
zeroclaw gateway --port 3000

# Option 2: Docker
cd apps/zeroclaw
docker build -t zeroclaw -f Dockerfile ../..
docker run -p 3000:3000 -e ZEROCLAW_API_KEY=your_key zeroclaw
```

Then set `ZEROCLAW_URL=http://localhost:3000` in the web app's `.env.local`.
