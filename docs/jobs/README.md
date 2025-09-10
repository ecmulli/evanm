# Jobs (Sync Utilities)

Located in `apps/jobs/`. Contains scripts to synchronize tasks across Notion workspaces and Motion.

- Notion sync: `notion/notion_sync.py`
- Motion sync: `motion/motion_sync.py`

Both support .env configuration and have a dry-run mode.

## Notion Task Sync
Script: `apps/jobs/notion/notion_sync.py`

Synchronizes tasks between the personal Hub database and external workspace databases (e.g., Livepeer, Vanquish).

### Required environment
- `HUB_NOTION_API_KEY`, `HUB_NOTION_DB_ID`, `HUB_NOTION_USER_ID`
- For each external workspace (auto-discovered):
  - `<WORKSPACE>_NOTION_API_KEY`
  - `<WORKSPACE>_NOTION_DB_ID`
  - `<WORKSPACE>_NOTION_USER_ID`

### Usage
```bash
python apps/jobs/notion/notion_sync.py --mode full
python apps/jobs/notion/notion_sync.py --mode incremental
python apps/jobs/notion/notion_sync.py --mode test --sync-content
```

### Capabilities
- External → Hub: creates hub tasks for items assigned to you in external DBs
- Hub → External: creates/updates external tasks; preserves hub as source of truth
- Optional content sync (page blocks)


## Motion ↔ Notion Sync
Script: `apps/jobs/motion/motion_sync.py`

Bidirectional synchronization between Motion AI and Notion databases. Uses custom fields in Motion to store Notion ID/URL and last sync time.

### Required environment
- `MOTION_API_KEY`
- `HUB_NOTION_API_KEY`, `HUB_NOTION_DB_ID`, `HUB_NOTION_USER_ID`
- `MOTION_HUB_WORKSPACE_ID`
- For each external workspace (auto-discovered):
  - `<WORKSPACE>_NOTION_API_KEY`, `<WORKSPACE>_NOTION_DB_ID`, `<WORKSPACE>_NOTION_USER_ID`
  - `MOTION_<WORKSPACE>_WORKSPACE_ID`

### Usage
```bash
python apps/jobs/motion/motion_sync.py --mode full
python apps/jobs/motion/motion_sync.py --mode test    # dry run
python apps/jobs/motion/motion_sync.py --mode test-real
```

### Capabilities
- Motion → Notion: mark completed tasks, set actual duration, update fields
- Notion → Motion: create/update Motion tasks based on hub
- Handles field mapping differences across workspaces
- Rate limit handling and retries for Motion API

### Notes
- In dry-run, scripts log intended changes without writing
- Some Motion custom field IDs are hard-coded; consider moving to env vars