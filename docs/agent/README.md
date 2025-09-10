# Agent API (FastAPI)

Base URL: `/` (see service config for port and domain)

- OpenAPI docs: `/docs`
- ReDoc: `/redoc`

## Overview
The Agent service exposes endpoints for task creation and health/auth checks. Routers are mounted under the `api/v1` prefix.

- Root: `GET /` – service info
- API Info: `GET /api/v1` – endpoint listing
- Health: `GET /api/v1/health`
- Auth Validate: `GET /api/v1/auth/validate`
- Task Creator: `POST /api/v1/task_creator`

Authentication uses a Bearer token. If `BEARER_TOKEN` is unset, auth is bypassed for local development.

## Authentication
Send an `Authorization: Bearer <token>` header. Validate via:

```bash
curl -i \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  "$BASE_URL/api/v1/auth/validate"
```

Success (200):
```json
{"status":"authenticated","message":"Token is valid"}
```

Missing/invalid token returns 401.

## Endpoints

### GET /
Returns service status and links.

Example:
```bash
curl -s "$BASE_URL/"
```

### GET /api/v1
Returns API info and available endpoints.

```bash
curl -s "$BASE_URL/api/v1"
```

### GET /api/v1/health
Health probe for readiness/liveness.

```bash
curl -s "$BASE_URL/api/v1/health"
```

Response:
```json
{"status":"healthy","service":"agent"}
```

### POST /api/v1/task_creator
Create a task using AI synthesis (OpenAI) and Notion integration. When `dry_run=true`, the task is parsed and validated without creating a Notion page.

- Auth: `Authorization: Bearer <token>` (unless disabled)
- Body: `TaskCreationRequest`
- Response: `TaskCreationResponse`

Request schema (from `TaskCreationRequest`):
```json
{
  "text_inputs": ["string"],
  "image_urls": ["string"],
  "suggested_workspace": "Personal|Livepeer|Vanquish",
  "dry_run": true
}
```

Response schema (from `TaskCreationResponse`):
```json
{
  "success": true,
  "message": "string",
  "task_id": "string|null",
  "task_url": "string|null",
  "parsed_data": {
    "task_name": "string",
    "workspace": "Personal|Livepeer|Vanquish",
    "priority": "Low|Medium|High|ASAP",
    "estimated_hours": 1.0,
    "due_date": "YYYY-MM-DD",
    "description": "string",
    "acceptance_criteria": "string",
    "labels": ["Planned","Fire Drill","Support","Strategic","Admin"],
    "status": "Todo|Completed|Backlog",
    "team": "Personal|Email/Creative|Ads|DevX|Infra|Product|Marketing|Ops/HR|GTM|BizDev|Ops"
  },
  "dry_run": true
}
```

Example (dry run):
```bash
curl -s -X POST "$BASE_URL/api/v1/task_creator" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -d '{
    "text_inputs": [
      "Draft newsletter copy for next week; prioritize DevX; due Friday; include links: https://example.com/spec"
    ],
    "dry_run": true
  }'
```

Example (create):
```bash
curl -s -X POST "$BASE_URL/api/v1/task_creator" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BEARER_TOKEN" \
  -d '{
    "text_inputs": ["Create onboarding flow with OAuth and session storage"],
    "suggested_workspace": "Personal",
    "dry_run": false
  }'
```

### Errors
- 400 Validation Error: invalid inputs or synthesis output
- 401 Unauthorized: missing/invalid token
- 500 Internal Server Error: unexpected failure

Error response structure:
```json
{"success": false, "error": "string", "details": "string"}
```

## Models
Defined in `apps/agent/models/task_models.py`.

- `TaskCreationRequest`
- `ParsedTaskData`
- `TaskCreationResponse`
- `ErrorResponse`

## Environment
The Agent requires:
- `OPENAI_API_KEY`
- `HUB_NOTION_API_KEY`
- `HUB_NOTION_DB_ID`
- Optional: `BEARER_TOKEN`, `PORT`, `DEBUG`