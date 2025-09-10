# Agent Configuration

Defined in `apps/agent/utils/config.py`.

## Required Environment Variables
- `OPENAI_API_KEY`
- `HUB_NOTION_API_KEY` (or `PERSONAL_NOTION_API_KEY`)
- `HUB_NOTION_DB_ID` (or `PERSONAL_NOTION_DB_ID`)

If any of the required variables are missing, startup will fail with a validation error.

## Optional Environment Variables
- `BEARER_TOKEN`: when set, enables Bearer auth for all protected endpoints
- `PORT` (default `8000`): HTTP port bound by Hypercorn
- `DEBUG` (default `false`): enables additional logging

### Optional workspace configurations
- `LIVEPEER_NOTION_API_KEY`, `LIVEPEER_NOTION_DB_ID`
- `VANQUISH_NOTION_API_KEY`, `VANQUISH_NOTION_DB_ID`

When present, these are used by the sync jobs to route tasks to external workspaces.

## Loading
`.env` is supported via `python-dotenv` at startup.