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
| `API_KEY` | Yes | OpenRouter API key (`sk-or-...`) from openrouter.ai |
| `PROVIDER` | No | Provider name (default: `openrouter`) |
| `ZEROCLAW_ALLOW_PUBLIC_BIND` | No | Already set to `true` in Dockerfile |

Set this on the **Web service**:

| Variable | Required | Description |
|----------|----------|-------------|
| `ZEROCLAW_URL` | Yes | ZeroClaw's internal Railway URL (e.g. `http://zeroclaw.railway.internal:3000`) |

### API Key

Get an API key from [openrouter.ai](https://openrouter.ai). OpenRouter gives you access to Claude, GPT, Gemini, Llama, and dozens of other models under a single key with pay-as-you-go billing.

## Local Development

```bash
# Option 1: Run ZeroClaw directly (requires Rust)
git clone https://github.com/zeroclaw-labs/zeroclaw.git /tmp/zeroclaw
cd /tmp/zeroclaw && cargo build --release --locked
cargo install --path . --force --locked
zeroclaw onboard --api-key sk-or-YOUR_KEY --provider openrouter
zeroclaw gateway --port 3000

# Option 2: Docker
cd apps/zeroclaw
docker build -t zeroclaw -f Dockerfile ../..
docker run -p 3000:3000 -e API_KEY=sk-or-YOUR_KEY zeroclaw
```

Then set `ZEROCLAW_URL=http://localhost:3000` in the web app's `.env.local` and visit `http://localhost:3001/claw`.
