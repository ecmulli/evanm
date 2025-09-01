# Motion ↔ Notion Sync

Bidirectional synchronization between Motion AI and Notion task databases.

## Overview

This script syncs tasks between your Notion workspaces (Personal, Livepeer, Vanquish) and Motion AI, enabling:

- **Real-time task management** across platforms
- **AI-powered scheduling** via Motion
- **Collaborative task tracking** in Notion
- **Unified workspace management**

## Prerequisites

### 1. Motion AI Setup

**Required Custom Fields in Motion:**
Before running the sync, create these custom fields in your Motion workspace:

1. **Notion ID** (Text field)
   - Used to link Motion tasks back to Notion
   - Enables bidirectional updates

2. **Notion URL** (URL field) 
   - Convenience link to jump to Notion task
   - Helps with navigation between platforms

**Motion Workspace IDs:**
You'll need the workspace IDs for each of your Motion workspaces:
- Personal workspace ID
- Livepeer workspace ID  
- Vanquish workspace ID

### 2. API Keys Required

**Motion AI:**
- API key from Motion dashboard

**Notion (same as existing sync):**
- Personal Notion API key
- Livepeer Notion API key
- Vanquish Notion API key

## Field Mapping

| Notion Field | Motion Field | Direction | Notes |
|-------------|-------------|----------|-------|
| Task name | name | → | One-way sync to Motion |
| Workspace | workspaceId | → | Mapped to Motion workspace IDs |
| Description (blocks) | description | → | Notion blocks converted to plain text |
| Priority | priority | ↔ | Both directions, defaults to Medium |
| Status | status | ↔ | Both directions with status mapping |
| Due date | dueDate | ↔ | Notion date range → start date |
| Est Duration Hrs | durationMinutes | ↔ | Hours converted to minutes (default 60) |

### Priority Mapping
- **Notion → Motion**: Low→LOW, Medium→MEDIUM, High→HIGH, ASAP→URGENT
- **Motion → Notion**: LOW→Low, MEDIUM→Medium, HIGH→High, URGENT→ASAP

### Status Mapping  
- **Notion → Motion**: Not started→TODO, In progress→IN_PROGRESS, Completed→COMPLETED, Canceled→CANCELLED
- **Motion → Notion**: TODO→Not started, IN_PROGRESS→In progress, COMPLETED→Completed, CANCELLED→Canceled

## Environment Variables

Add these to your `.env.dev` file:

```bash
# Motion AI
MOTION_API_KEY="your_motion_api_key"
MOTION_PERSONAL_WORKSPACE_ID="workspace_id_1"
MOTION_LIVEPEER_WORKSPACE_ID="workspace_id_2" 
MOTION_VANQUISH_WORKSPACE_ID="workspace_id_3"

# Notion (if not already configured)
PERSONAL_NOTION_API_KEY="your_personal_notion_key"
LIVEPEER_NOTION_API_KEY="your_livepeer_notion_key"
VANQUISH_NOTION_API_KEY="your_vanquish_notion_key"
PERSONAL_NOTION_DB_ID="your_personal_db_id"
LIVEPEER_NOTION_DB_ID="your_livepeer_db_id"
VANQUISH_NOTION_DB_ID="your_vanquish_db_id"
PERSONAL_NOTION_USER_ID="your_personal_user_id"
LIVEPEER_NOTION_USER_ID="your_livepeer_user_id"
VANQUISH_NOTION_USER_ID="your_vanquish_user_id"
```

## Usage

### Test Mode (Dry Run)
```bash
cd packages/jobs
python motion/motion_sync.py --mode test
```

### Full Sync
```bash
python motion/motion_sync.py --mode full
```

### Incremental Sync (Future)
```bash
python motion/motion_sync.py --mode incremental
```

## How It Works

### Notion → Motion Flow
1. **Query Notion** for assigned tasks (excluding Backlog/Completed/Canceled)
2. **Check Motion ID** field in Notion task
3. **Create or Update** Motion task accordingly
4. **Convert fields** using mapping rules:
   - Notion blocks → Motion description (plain text)
   - Hours → Minutes for duration
   - Priority/Status mapping
5. **Update Notion** with Motion ID for tracking

### Motion → Notion Flow (Future)
1. **Query Motion** for tasks with Notion ID custom field
2. **Compare timestamps** to detect changes
3. **Update Notion** with Motion changes:
   - Status updates (completion, progress)
   - Schedule changes from Motion AI
   - Duration adjustments

## Sync Strategy

### Current Implementation
- **Notion → Motion**: Full sync (creates/updates Motion tasks)
- **Motion → Notion**: Not yet implemented

### Future Enhancements
- **Bidirectional sync**: Motion status/schedule updates back to Notion
- **Smart polling**: Efficient change detection
- **Conflict resolution**: Handle simultaneous edits
- **Webhook integration**: Real-time sync server

## Common Issues

### Motion API Errors
- **Authentication**: Verify `MOTION_API_KEY` is correct
- **Workspace IDs**: Ensure workspace IDs are valid
- **Custom fields**: Verify "Notion ID" and "Notion URL" fields exist

### Field Mapping Issues
- **Unknown priority**: Defaults to "Medium"
- **Unknown status**: Defaults to "TODO" 
- **Missing duration**: Defaults to 60 minutes
- **Date formats**: Ensure Notion dates have start time

### Performance
- **Large task lists**: Consider incremental sync for better performance
- **API rate limits**: Built-in error handling with retries

## Development

### Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run dry run to test configuration
python motion/motion_sync.py --mode test

# Check logs for any issues
```

### Adding Features
- **New field mappings**: Update `get_*_mapping()` methods
- **Custom field handling**: Modify `extract_*_task_data()` methods  
- **API enhancements**: Extend `motion_request()` wrapper

## Future Roadmap

1. **Motion → Notion sync**: Complete bidirectional functionality
2. **Webhook server**: Real-time sync via webhooks
3. **Conflict resolution**: Smart merge for simultaneous edits
4. **Performance optimization**: Incremental sync with change detection
5. **Advanced scheduling**: Leverage Motion's AI scheduling insights
