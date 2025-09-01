# GitHub Secrets Setup for Motion & Notion Sync

To enable the automated GitHub Actions workflow, you need to configure these repository secrets.

## 🔑 Required GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions → Repository secrets

### Notion API Secrets (already configured)
- `PERSONAL_NOTION_API_KEY` - Your personal Notion integration token
- `LIVEPEER_NOTION_API_KEY` - Livepeer workspace Notion token  
- `VANQUISH_NOTION_API_KEY` - Vanquish workspace Notion token

### Notion Database IDs (already configured)
- `PERSONAL_NOTION_DB_ID` - Personal hub database ID
- `LIVEPEER_NOTION_DB_ID` - Livepeer database ID
- `VANQUISH_NOTION_DB_ID` - Vanquish database ID

### Notion User IDs (already configured)  
- `PERSONAL_NOTION_USER_ID` - Your user ID in personal workspace
- `LIVEPEER_NOTION_USER_ID` - Your user ID in Livepeer workspace
- `VANQUISH_NOTION_USER_ID` - Your user ID in Vanquish workspace

### Motion API Secret (NEW - needs to be added)
- `MOTION_API_KEY` - Your Motion AI API token
  - **Value**: `ccTqv8nhwgo6y8Oz7zSJBojPDcYf2dkIgh22KLWr9XM=`

## 🚀 GitHub Actions Workflow

The workflow (`notion_motion_sync.yaml`) will:

### Scheduled Runs
- **Every 30 minutes** during work hours (8 AM - 8 PM UTC, Monday-Friday)
- **Daily backup** at 6 AM UTC

### Manual Runs
- Go to Actions → "Notion & Motion Task Sync" → "Run workflow"
- Choose mode: `test` (dry run), `full`, or `incremental`

### What It Does
1. **Notion Sync**: Syncs between your personal hub and external workspaces
2. **Motion Sync**: Bidirectional sync between Notion and Motion AI
   - Creates Motion tasks from Notion
   - Updates Notion with Motion changes (status, priority, etc.)
   - Handles orphaned task recreation
   - Smart retry logic with rate limiting

## 🔧 Current Sync Status

### ✅ Fully Working
- **Livepeer**: 10/10 tasks synced bidirectionally
- **Vanquish**: 6/6 tasks synced bidirectionally  
- **Personal**: 0 active tasks

### 🎯 Features
- ✅ **Bidirectional sync** (Notion ↔ Motion)
- ✅ **Auto-scheduling** for work hours
- ✅ **Custom fields** (Notion ID/URL references)
- ✅ **Smart retry logic** (handles rate limits automatically)
- ✅ **Field mapping** (priority, status, duration, due dates)
- ✅ **Content sync** (Notion blocks → Motion descriptions)
- ✅ **Orphaned task recreation** (404 error handling)

## 🐛 Troubleshooting

### Check Workflow Status
- Go to Actions tab to see sync results
- Download logs if there are failures
- Check individual step outputs

### Common Issues
- **Rate limiting**: The workflow includes smart retry logic
- **Missing secrets**: Ensure all secrets are configured
- **API permissions**: Verify Notion integrations have database access

### Manual Testing
```bash
# Test locally (dry run)
cd packages/jobs
python motion/motion_sync.py --mode test

# Test specific workspace
python -c "
from motion.motion_sync import MotionNotionSync
sync = MotionNotionSync(dry_run=True)
results = sync.sync_full()
print(results)
"
```

## 📊 Expected Results

After setup, you should see in Actions:
- ✅ **Notion sync**: Updates between workspaces
- ✅ **Motion sync**: Bidirectional task synchronization
- 📈 **Summary**: Task counts and any errors

The automation will keep your Notion and Motion tasks in perfect sync! 🎉
