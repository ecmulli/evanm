# Notion Sync Setup Guide

## Quick Start

### 1. Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name it "Task Sync" 
4. Copy the **Internal Integration Token**

### 2. Share Databases with Integration

For each database (Personal Hub, Livepeer, Vanquish):
1. Open the database in Notion
2. Click "Share" in top right
3. Click "Add people, emails, groups, or integrations"
4. Search for your "Task Sync" integration
5. Give it "Edit" permissions

### 3. Get Database IDs

Database IDs are in the URL when viewing a database:
```
https://www.notion.so/workspace/VIEW_DATABASE_ID?v=view_id
                           ^^^^^^^^^^^^^^^^^^^^
                           This is your database ID
```

Copy the database ID for:
- Personal Hub (main task database)
- Livepeer workspace database  
- Vanquish workspace database

### 4. Get Your User ID

Your User ID can be found by:
1. Go to any task assigned to you
2. Right-click your profile picture → "Copy link to user"
3. The URL will be: `https://notion.so/workspace/USER_ID`
4. Copy the USER_ID part

### 5. Add GitHub Secrets

In your GitHub repo, go to Settings → Secrets and variables → Actions → New repository secret:

- `HUB_NOTION_API_KEY` = Your hub workspace integration token
- `LIVEPEER_NOTION_API_KEY` = Your Livepeer workspace integration token  
- `VANQUISH_NOTION_API_KEY` = Your Vanquish workspace integration token
- `HUB_NOTION_DB_ID` = Hub database ID
- `LIVEPEER_NOTION_DB_ID` = Livepeer database ID  
- `VANQUISH_NOTION_DB_ID` = Vanquish database ID
- `NOTION_USER_ID` = Your user ID from step 4

### 6. Test the Setup

Run a test sync manually:

1. Go to Actions tab in GitHub
2. Click "Notion Task Sync" 
3. Click "Run workflow"
4. Select "test" mode
5. Click "Run workflow"

This will do a dry run and show you what would be synced without making changes.

### 7. Verify Database Schema

Make sure your databases have these fields with exact names:

**Required in ALL databases:**
- `Task name` (Title)
- `Status` (Status) 
- `Est Duration Hrs` (Number)
- `Due date` (Date)
- `Priority` (Select: Low, Medium, High, ASAP)
- `Description` (Text)
- `Assignee` (Person) - must be set for tasks to sync

**Personal Hub only:**
- `Workspace` (Select: Personal, Livepeer, Vanquish)
- `External Notion ID` (Text)
- `Motion ID` (Text)

## Automation Schedule

The GitHub Action runs:
- **Incremental sync**: Every 2 hours during work hours (weekdays 8 AM - 8 PM UTC)
- **Full sync**: Daily at 6 AM UTC
- **Manual**: Anytime via Actions tab

## Troubleshooting

### Common Issues

**"Database not found"**
- Check database ID is correct
- Verify integration has access to database

**"No tasks found"** 
- Check your User ID is correct
- Make sure tasks are assigned to you
- Verify `Assignee` field exists and is set

**"Property not found"**
- Check field names match exactly (case sensitive)
- Ensure all required fields exist in both databases

### Testing Locally

```bash
# Install dependencies
cd packages/jobs
pip install -r requirements.txt

# Set environment variables  
export HUB_NOTION_API_KEY="your_hub_token_here"
export LIVEPEER_NOTION_API_KEY="your_livepeer_token_here" 
export VANQUISH_NOTION_API_KEY="your_vanquish_token_here"
export HUB_NOTION_DB_ID="your_hub_db_id"
# ... etc

# Test sync
cd notion
python notion_motion_sync.py --mode test
```

## Next Steps

Once the sync is working:

1. **Monitor the first few runs** to ensure everything syncs correctly
2. **Adjust the schedule** if needed by editing the GitHub Action
3. **Add Motion.ai sync** when ready (Motion ID field is already prepared)

The sync is designed to be safe - it only updates existing properties and won't delete tasks or overwrite data unexpectedly.
