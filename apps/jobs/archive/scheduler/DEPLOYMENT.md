# Deployment Guide

Options for running the Notion Calendar Auto-Scheduler continuously in production.

## Option 1: Railway (Recommended)

Railway is perfect for long-running background services.

### Steps:

1. **Create Railway account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create new project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure service**
   - Set root directory: `apps/jobs/scheduler`
   - Set start command: `python calendar_scheduler.py --mode continuous`

4. **Add environment variables**
   ```
   LIVEPEER_NOTION_API_KEY=secret_...
   LIVEPEER_NOTION_DB_ID=...
   SCHEDULER_INTERVAL_MINUTES=10
   WORK_START_HOUR=9
   WORK_END_HOUR=17
   SLOT_DURATION_MINUTES=15
   SCHEDULE_DAYS_AHEAD=7
   ```

5. **Deploy**
   - Railway will automatically deploy
   - Service will start running continuously
   - Check logs in Railway dashboard

### Cost:
- Railway Free tier: $5 credit/month
- Hobby plan: $5/month (includes more resources)

## Option 2: Render

Similar to Railway, good for background workers.

### Steps:

1. **Create Render account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create new Background Worker**
   - Click "New +" → "Background Worker"
   - Connect your GitHub repository
   - Select branch

3. **Configure worker**
   - Name: `notion-calendar-scheduler`
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python apps/jobs/scheduler/calendar_scheduler.py --mode continuous`

4. **Add environment variables**
   - Go to "Environment" tab
   - Add all required variables (same as Railway)

5. **Deploy**
   - Click "Create Background Worker"
   - Service will deploy and start running

### Cost:
- Free tier: Limited hours/month
- Starter plan: $7/month

## Option 3: Local Server (macOS/Linux)

Run on your own always-on computer.

### Using systemd (Linux)

Create `/etc/systemd/system/notion-scheduler.service`:

```ini
[Unit]
Description=Notion Calendar Auto-Scheduler
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/Users/evanmullins/Projects/evanm/apps/jobs/scheduler
Environment="PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/Users/evanmullins/Projects/evanm/.env.dev
ExecStart=/opt/homebrew/bin/python3 calendar_scheduler.py --mode continuous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable notion-scheduler
sudo systemctl start notion-scheduler
sudo systemctl status notion-scheduler

# View logs
sudo journalctl -u notion-scheduler -f
```

### Using LaunchAgent (macOS)

Create `~/Library/LaunchAgents/com.evanm.notion-scheduler.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.evanm.notion-scheduler</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/python3</string>
        <string>/Users/evanmullins/Projects/evanm/apps/jobs/scheduler/calendar_scheduler.py</string>
        <string>--mode</string>
        <string>continuous</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/evanmullins/Projects/evanm/apps/jobs/scheduler</string>
    
    <key>StandardOutPath</key>
    <string>/Users/evanmullins/Projects/evanm/apps/jobs/scheduler/scheduler.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/evanmullins/Projects/evanm/apps/jobs/scheduler/scheduler.error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>LIVEPEER_NOTION_API_KEY</key>
        <string>your_api_key_here</string>
        <key>LIVEPEER_NOTION_DB_ID</key>
        <string>your_db_id_here</string>
    </dict>
</dict>
</plist>
```

Load and start:
```bash
launchctl load ~/Library/LaunchAgents/com.evanm.notion-scheduler.plist
launchctl start com.evanm.notion-scheduler

# View status
launchctl list | grep notion-scheduler

# View logs
tail -f /Users/evanmullins/Projects/evanm/apps/jobs/scheduler/scheduler.log
```

### Using screen (Simple, any OS)

```bash
# Start
screen -S scheduler
cd /Users/evanmullins/Projects/evanm/apps/jobs/scheduler
python3 calendar_scheduler.py --mode continuous

# Detach: Ctrl+A then D

# Reattach
screen -r scheduler

# Kill
screen -X -S scheduler quit
```

### Using nohup (Simple, any OS)

```bash
cd /Users/evanmullins/Projects/evanm/apps/jobs/scheduler
nohup python3 calendar_scheduler.py --mode continuous > scheduler.log 2>&1 &

# Save the process ID
echo $! > scheduler.pid

# View logs
tail -f scheduler.log

# Stop
kill $(cat scheduler.pid)
```

## Option 4: Docker

Containerize for easy deployment anywhere.

### Dockerfile

Create `apps/jobs/scheduler/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scheduler code
COPY . .

# Run scheduler
CMD ["python", "calendar_scheduler.py", "--mode", "continuous"]
```

### Build and run:

```bash
# Build
cd /Users/evanmullins/Projects/evanm/apps/jobs/scheduler
docker build -t notion-scheduler .

# Run
docker run -d \
  --name notion-scheduler \
  --restart unless-stopped \
  -e LIVEPEER_NOTION_API_KEY="secret_..." \
  -e LIVEPEER_NOTION_DB_ID="..." \
  -e SCHEDULER_INTERVAL_MINUTES=10 \
  -e WORK_START_HOUR=9 \
  -e WORK_END_HOUR=17 \
  notion-scheduler

# View logs
docker logs -f notion-scheduler

# Stop
docker stop notion-scheduler
docker rm notion-scheduler
```

## Monitoring

### Health Checks

The scheduler logs activity every cycle. Monitor for:
- ✅ Successful scheduling cycles
- ❌ Error messages
- Connection issues
- Notion API rate limits

### Alerting

Set up alerts for:
1. **Service down**: No log activity for > 15 minutes
2. **Errors**: More than 3 errors in a row
3. **API failures**: Notion API connection issues

### Logs

All deployment options provide logs. Key things to watch:

```
🔄 Starting scheduling cycle...          ← Cycle started
✅ Scheduled 'Task' from 9:00 to 10:00  ← Task scheduled
🔄 Rescheduled 'Task' ...               ← Task moved
⏭️  Skipping ...                        ← Task skipped (already scheduled)
❌ Error ...                            ← Problem occurred
📊 Scheduling cycle complete            ← Cycle finished
⏸️  Waiting 10 minutes ...              ← Sleeping until next cycle
```

## Recommendations

**For development/testing:**
- Use `screen` or `nohup` on local machine
- Easy to start/stop/modify

**For personal use:**
- Railway or Render (set and forget)
- Automatic restarts if crashes
- Easy to view logs

**For production/team use:**
- Docker + orchestration (Kubernetes, Docker Swarm)
- Full monitoring and alerting
- High availability

## Troubleshooting

### Service stops unexpectedly

**systemd/LaunchAgent:**
- Check logs for errors
- Verify environment variables are set
- Ensure Python path is correct

**Railway/Render:**
- Check dashboard logs
- Verify environment variables
- Check resource limits

**Docker:**
```bash
docker logs notion-scheduler
docker restart notion-scheduler
```

### High memory usage

The scheduler is lightweight, but if you notice high memory:
1. Reduce `SCHEDULE_DAYS_AHEAD` (default: 7)
2. Increase `SCHEDULER_INTERVAL_MINUTES` (default: 10)
3. Check for Notion API connection leaks

### Notion API rate limits

If you hit rate limits:
1. Increase `SCHEDULER_INTERVAL_MINUTES` to 15 or 20
2. Reduce number of schedulable tasks
3. The scheduler automatically respects limits

## Next Steps

After deployment:
1. Monitor first few cycles
2. Verify tasks are being scheduled correctly
3. Check Notion Calendar displays tasks
4. Set up alerting for errors
5. Document your deployment configuration

See `SETUP.md` for initial setup instructions.
See `README.md` for full documentation.

