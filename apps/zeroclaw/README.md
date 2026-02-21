# ZeroClaw Service

A ZeroClaw AI agent gateway deployed as a Railway service behind the existing bearer-token auth.

## Architecture

```
Browser → /claw (Next.js auth middleware) → /claw/api/* (proxy) → ZeroClaw gateway :3000
```

The Next.js web app proxies authenticated requests from `/claw/api/*` to the ZeroClaw gateway's OpenAI-compatible `/v1/chat/completions` endpoint.

## Environment Variables

Set these in the Railway dashboard for the **ZeroClaw service**:

| Variable | Required | Description |
|----------|----------|-------------|
| `ZEROCLAW_API_KEY` | Yes | Anthropic API key (`sk-ant-...`) from console.anthropic.com |
| `ZEROCLAW_PROVIDER` | No | Provider name (default: `anthropic`) |
| `ZEROCLAW_MODEL` | No | Model to use (default: `claude-sonnet-4-20250514`) |

Set this on the **Web service**:

| Variable | Required | Description |
|----------|----------|-------------|
| `ZEROCLAW_URL` | Yes | ZeroClaw's internal Railway URL (e.g. `http://zeroclaw.railway.internal:3000`) |

### API Key

You need an **Anthropic API key** from [console.anthropic.com](https://console.anthropic.com). A Claude Max subscription (claude.ai) does not include API access -- those are separate products. The API has its own pay-as-you-go billing.

Alternatively you can use **OpenRouter** (openrouter.ai) which gives you access to Claude and many other models under a single API key. Set `ZEROCLAW_PROVIDER=openrouter` and `ZEROCLAW_MODEL=anthropic/claude-sonnet-4-20250514` in that case.

## Local Development

```bash
# Option 1: Run ZeroClaw directly (requires Rust)
git clone https://github.com/zeroclaw-labs/zeroclaw.git /tmp/zeroclaw
cd /tmp/zeroclaw && cargo build --release --locked
cargo install --path . --force --locked
zeroclaw onboard --api-key sk-ant-YOUR_KEY --provider anthropic
zeroclaw gateway --port 3000

# Option 2: Docker
cd apps/zeroclaw
docker build -t zeroclaw -f Dockerfile ../..
docker run -p 3000:3000 -e ZEROCLAW_API_KEY=sk-ant-YOUR_KEY zeroclaw
```

Then set `ZEROCLAW_URL=http://localhost:3000` in the web app's `.env.local` and visit `http://localhost:3001/claw`.
