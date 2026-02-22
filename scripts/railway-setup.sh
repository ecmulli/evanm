#!/usr/bin/env bash
set -euo pipefail

#
# One-time Railway project setup for the evanm monorepo.
#
# Prerequisites:
#   npm install -g @railway/cli
#   railway login
#   railway link          (link to your existing project)
#
# Usage:
#   ./scripts/railway-setup.sh
#
# This creates all services and wires up env vars. You still need to:
#   1. Add secrets (API keys, tokens) in the Railway dashboard
#   2. Assign custom domains in the Railway dashboard
#

echo "==> Creating services..."

railway add --service web \
  --variables "NODE_ENV=production"

railway add --service agent

railway add --service zeroclaw \
  --variables "ZEROCLAW_ALLOW_PUBLIC_BIND=true" --variables "PROVIDER=openrouter"

echo ""
echo "==> Services created. Next steps:"
echo ""
echo "  1. In the Railway dashboard, connect each service to this GitHub repo"
echo ""
echo "  2. Set the config file path for each service:"
echo "     - web       → apps/web/railway.toml"
echo "     - agent     → apps/agent/railway.toml"
echo "     - zeroclaw  → apps/zeroclaw/railway.toml"
echo ""
echo "  3. Add these env vars in the dashboard:"
echo ""
echo "     web:"
echo "       BEARER_TOKEN        = <your token>"
echo "       BACKEND_URL         = \${{agent.RAILWAY_PRIVATE_DOMAIN}}:8000"
echo "       ZEROCLAW_URL        = http://\${{zeroclaw.RAILWAY_PRIVATE_DOMAIN}}:3000"
echo ""
echo "     agent:"
echo "       BEARER_TOKEN        = <same token as web>"
echo "       OPENAI_API_KEY      = <your openai key>"
echo "       HUB_NOTION_API_KEY  = <your notion key>"
echo "       HUB_NOTION_DB_ID    = <your notion db id>"
echo ""
echo "     zeroclaw:"
echo "       API_KEY             = <your openrouter key>"
echo "       BEARER_TOKEN        = <same token as web>"
echo ""
echo "  4. Assign custom domains:"
echo "     - web      → agent.evanm.xyz"
echo "     - zeroclaw → gateway.evanm.xyz"
echo ""
echo "Done! Push to your deploy branch to trigger builds."
