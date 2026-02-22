#!/bin/sh
set -e

cleanup() {
    kill "$ZEROCLAW_PID" "$CADDY_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Initialize zeroclaw with API key + provider (skips pairing requirement)
ONBOARD_PROVIDER="${PROVIDER:-openrouter}"
if [ -n "$API_KEY" ]; then
    zeroclaw onboard --api-key "$API_KEY" --provider "$ONBOARD_PROVIDER" 2>&1 || true
fi

# Start zeroclaw gateway on port 3001 (Caddy proxies from 3000)
zeroclaw gateway --port 3001 &
ZEROCLAW_PID=$!

# Start Caddy auth proxy in foreground-ish
caddy run --config /etc/caddy/Caddyfile &
CADDY_PID=$!

# Wait for either to exit
wait
