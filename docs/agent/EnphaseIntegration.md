# Enphase Solar Integration

This document describes how to set up and use the Enphase Solar integration with the Agent API.

## Overview

The Enphase integration allows the Agent to:
- Query solar production data (how much energy your panels generated)
- Query energy consumption data (how much energy your home used)
- Calculate net energy usage (production minus consumption)
- Get current system status (real-time production, system health)
- Create tasks based on solar data (e.g., "Production is low, create a task to check panels")

## Architecture

```
┌─────────────────┐     ┌─────────────────────────────────────────┐
│   Chat Agent    │────▶│           FastAPI Agent Server          │
│   (Next.js)     │     │  ┌──────────────────────────────────┐   │
│                 │     │  │  POST /api/v1/agent              │   │
└─────────────────┘     │  │  - OpenAI function calling       │   │
                        │  │  - Tool dispatch to Enphase API  │   │
                        │  └──────────────────────────────────┘   │
                        │  ┌──────────────────────────────────┐   │
                        │  │  EnphaseService                  │   │
                        │  │  - OAuth token management        │   │
                        │  │  - Enphase v4 API calls          │   │
                        │  └──────────────────────────────────┘   │
                        └─────────────────────────────────────────┘
                                          │
                                          ▼
                        ┌─────────────────────────────────────────┐
                        │         Enphase Cloud API (v4)          │
                        └─────────────────────────────────────────┘
```

## Setup

### 1. Register an Enphase Developer App

1. Go to [Enphase Developer Portal](https://developer.enphase.com/)
2. Create an account or sign in
3. Create a new application
4. Note down:
   - **Client ID**
   - **Client Secret**
   - **API Key**

### 2. Configure Environment Variables

Add these to your `.env` file or deployment environment:

```bash
# Required for Enphase integration
ENPHASE_CLIENT_ID=your_client_id
ENPHASE_CLIENT_SECRET=your_client_secret
ENPHASE_API_KEY=your_api_key

# Your Enphase system ID (find in Enlighten portal or via API)
ENPHASE_SYSTEM_ID=your_system_id

# OAuth tokens (obtained via OAuth flow below)
ENPHASE_ACCESS_TOKEN=
ENPHASE_REFRESH_TOKEN=

# Optional: Redirect URI (defaults to Enphase's default)
ENPHASE_REDIRECT_URI=https://api.enphaseenergy.com/oauth/redirect_uri

# Optional: Token persistence file
ENPHASE_TOKEN_FILE=/path/to/tokens.json

# Optional: Timezone for date calculations
ENPHASE_TIMEZONE=America/Chicago
```

### 3. Complete OAuth Authorization

The Enphase API requires OAuth 2.0 authorization. Follow these steps:

#### Option A: Using the API Endpoints

1. **Start OAuth flow:**
   ```bash
   curl -H "Authorization: Bearer $BEARER_TOKEN" \
        "$API_URL/api/v1/enphase/oauth/init"
   ```

   Response:
   ```json
   {
     "auth_url": "https://api.enphaseenergy.com/oauth/authorize?...",
     "state": "random_state_string"
   }
   ```

2. **Authorize in browser:**
   - Open the `auth_url` in a browser
   - Log in with your Enphase account
   - Authorize the application
   - You'll be redirected to a URL with a `code` parameter

3. **Exchange code for tokens:**
   ```bash
   curl -X POST "$API_URL/api/v1/enphase/oauth/callback" \
        -H "Authorization: Bearer $BEARER_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
          "code": "authorization_code_from_redirect",
          "state": "state_from_step_1"
        }'
   ```

   Response:
   ```json
   {
     "success": true,
     "message": "Successfully authenticated with Enphase.",
     "access_token": "eyJ...",
     "refresh_token": "eyJ...",
     "expires_in": 86400
   }
   ```

4. **Save tokens to environment:**
   Add the tokens to your `.env` file:
   ```bash
   ENPHASE_ACCESS_TOKEN=full_access_token
   ENPHASE_REFRESH_TOKEN=full_refresh_token
   ```

#### Option B: Find Your System ID

Once authenticated, you can list your systems:
```bash
# The agent will automatically refresh tokens when expired
curl -H "Authorization: Bearer $BEARER_TOKEN" \
     "$API_URL/api/v1/enphase/system"
```

## Usage

### Unified Agent Endpoint

The main endpoint for conversational interactions:

```bash
curl -X POST "$API_URL/api/v1/agent" \
     -H "Authorization: Bearer $BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What was my solar production yesterday?"
     }'
```

Response:
```json
{
  "success": true,
  "message": "Yesterday your system produced 42.5 kWh, which is about 15% above your weekly average of 37 kWh/day.",
  "tool_calls": [
    {
      "tool_name": "get_solar_production",
      "arguments": {"start_date": "2026-01-31", "end_date": "2026-01-31"},
      "result": {"success": true, "data": {...}}
    }
  ],
  "solar_data": {
    "start_date": "2026-01-31",
    "end_date": "2026-01-31",
    "total_kwh": 42.5,
    "average_daily_kwh": 42.5
  }
}
```

### Direct Data Endpoints

For testing or direct access:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/enphase/status` | Check integration status |
| `GET /api/v1/enphase/production?start_date=2026-01-01&end_date=2026-01-31` | Get production data |
| `GET /api/v1/enphase/consumption?start_date=2026-01-01&end_date=2026-01-31` | Get consumption data |
| `GET /api/v1/enphase/net?start_date=2026-01-01&end_date=2026-01-31` | Get net energy data |
| `GET /api/v1/enphase/system` | Get current system status |

### Example Conversations

**Query production:**
> User: "How much solar energy did I produce this week?"
> Agent: "This week your system produced 285.3 kWh, averaging 40.8 kWh per day."

**Query net usage:**
> User: "Am I exporting or importing power?"
> Agent: "This week you exported 45.2 kWh to the grid. Your panels produced 285.3 kWh while your home consumed 240.1 kWh. You're 84% grid-independent!"

**Create task from solar context:**
> User: "Production seems low lately. Create a task to clean the panels."
> Agent: "I've created a task 'Clean solar panels' in your Personal workspace with medium priority. Your recent production (32.1 kWh/day) is 21% below your usual average."

## Available Tools

The agent has access to these tools:

| Tool | Description |
|------|-------------|
| `get_solar_production` | Get production data for a date range |
| `get_energy_consumption` | Get consumption data for a date range |
| `get_net_energy_usage` | Calculate net energy (production - consumption) |
| `get_system_status` | Get current system status |
| `create_task` | Create a task in Notion |

## Token Management

The `EnphaseService` automatically handles:
- **Token refresh**: Access tokens expire after ~24 hours. The service automatically refreshes them using the refresh token.
- **Token persistence**: If `ENPHASE_TOKEN_FILE` is set, tokens are persisted to disk and survive restarts.
- **Retry on 401**: If an API call returns 401, the service refreshes the token and retries.

## Data Models

### SolarProductionData
```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "total_wh": 1250000,
  "total_kwh": 1250.0,
  "intervals": 31,
  "average_daily_kwh": 40.32
}
```

### NetEnergyData
```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "production_kwh": 1250.0,
  "consumption_kwh": 980.5,
  "net_kwh": 269.5,
  "self_consumption_pct": 78.4,
  "grid_independence_pct": 100.0
}
```

### SystemStatusData
```json
{
  "system_id": 123456,
  "current_power_w": 4200,
  "current_power_kw": 4.2,
  "energy_today_kwh": 28.5,
  "energy_lifetime_mwh": 45.2,
  "system_size_kw": 8.5,
  "num_panels": 24,
  "status": "normal",
  "last_report": "2026-01-31T14:30:00-06:00",
  "is_producing": true
}
```

## Troubleshooting

### "Enphase service not available"
- Check that `ENPHASE_CLIENT_ID`, `ENPHASE_CLIENT_SECRET`, and `ENPHASE_API_KEY` are set
- Verify tokens are configured: check `/api/v1/enphase/status`

### "Token refresh failed"
- The refresh token may have expired (rare)
- Re-authorize using the OAuth flow

### "System ID is required"
- Set `ENPHASE_SYSTEM_ID` in your environment
- Or pass it as a query parameter: `?system_id=123456`

### No consumption data
- Consumption monitoring requires an Envoy with consumption metering
- Check if your Enphase system supports consumption data

## Security Notes

- Store tokens securely (environment variables or encrypted file)
- The OAuth endpoints require Bearer token authentication
- Access tokens are short-lived (~24 hours) but refresh tokens are long-lived
- Never commit tokens to source control
