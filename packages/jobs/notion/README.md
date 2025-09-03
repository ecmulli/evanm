# Notion Task Sync

Syncs tasks between your personal task hub and external workspace databases (Livepeer, Vanquish).

## Features

- **Bidirectional Sync**: External workspaces ↔ Personal hub
- **Full & Incremental Modes**: Sync all tasks or just recent changes
- **Dry Run Support**: Test changes before applying them
- **GitHub Actions Ready**: Run automatically on schedule

## Setup

### 1. Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the **Internal Integration Token**
4. Share your databases with the integration:
   - Go to each database → Share → Add your integration

### 2. Get Database IDs

Database IDs are in the URL when viewing a database:
```
https://notion.so/your-workspace/DATABASE_ID?v=...
```

### 3. Get Your User ID

Your Notion User ID can be found by:
- Checking any task assigned to you in Notion
- Or using the Notion API to list users

### 4. Environment Variables

Set these environment variables (or add to `.env` file):

```bash
# Notion API Keys (one for each workspace)
HUB_NOTION_API_KEY=secret_your_hub_notion_integration_token_here
LIVEPEER_NOTION_API_KEY=secret_your_livepeer_notion_integration_token_here
VANQUISH_NOTION_API_KEY=secret_your_vanquish_notion_integration_token_here

# Database IDs
HUB_NOTION_DB_ID=your_hub_database_id_here
LIVEPEER_NOTION_DB_ID=your_livepeer_database_id_here
VANQUISH_NOTION_DB_ID=your_vanquish_database_id_here

# Your Notion user ID
NOTION_USER_ID=your_notion_user_id_here
```

## Usage

### Local Testing

```bash
# Install dependencies
pip install -r ../requirements.txt

# Test sync (dry run)
python notion_motion_sync.py --mode test

# Run full sync
python notion_motion_sync.py --mode full

# Run incremental sync (last 24 hours)
python notion_motion_sync.py --mode incremental
```

### Schema Mapping

The script syncs these properties between databases:

| Personal Hub Field | External DB Field | Type | Notes |
|-------------------|-------------------|------|-------|
| Task name | Task name | Title | ✅ Synced |
| Status | Status | Status | ✅ Synced |
| Est Duration Hrs | Est Duration Hrs | Number | ✅ Synced |
| Due date | Due date | Date | ✅ Synced |
| Priority | Priority | Select | ✅ Synced |
| Description | Description | Text | ✅ Synced |
| Workspace | - | Select | 🏠 Personal hub only |
| External Notion ID | - | Text | 🏠 Personal hub only |
| Motion ID | - | Text | 🏠 Personal hub only |
| Projects | Projects | Relation | ⏭️ Ignored during sync |

### Sync Logic

#### External → Personal Hub
- Queries assigned tasks from Livepeer/Vanquish (excluding Backlog/Completed)
- Creates missing tasks in personal hub with appropriate workspace label
- Updates existing tasks if properties have changed

#### Personal Hub → External
- Queries personal hub tasks for each workspace
- Updates corresponding external tasks based on External Notion ID
- Syncs property changes back to source databases

#### Modes

**Full Mode** (`--mode full`):
- Syncs all assigned tasks regardless of when they were updated
- Best for initial setup or fixing discrepancies

**Incremental Mode** (`--mode incremental`):
- Only syncs tasks updated in the last 24 hours
- Efficient for regular scheduled runs

**Test Mode** (`--mode test`):
- Dry run that shows what would be changed without making changes
- Perfect for testing configuration and logic

## GitHub Actions

The sync can run automatically via GitHub Actions. See the workflow file for scheduling options.

## Troubleshooting

### Common Issues

1. **Authentication Error**: Check your `NOTION_TOKEN`
2. **Database Not Found**: Verify database IDs and integration permissions
3. **No Tasks Found**: Check your `NOTION_USER_ID` and task assignments
4. **Property Mismatch**: Ensure field names match between databases

### Logs

The script provides detailed logging:
- ✅ Successful operations
- ❌ Errors with details
- 🔄 Sync progress
- 📊 Summary statistics

### Testing

Always test with `--mode test` before running actual syncs:

```bash
python notion_motion_sync.py --mode test
```

This will show you exactly what changes would be made without actually making them.
