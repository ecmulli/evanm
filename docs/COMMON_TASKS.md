# Common Agent Tasks

Step-by-step guides for common modifications in this repository.

## Table of Contents

- [Adding Website Content](#adding-website-content)
- [API Development](#api-development)
- [Scheduler Modifications](#scheduler-modifications)
- [Frontend Changes](#frontend-changes)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Adding Website Content

### Add a New Thought/Blog Post

1. Create file at `apps/web/src/content/thoughts/my-thought.md`:

```markdown
---
title: My Thought.md
---
# My Thought Title

*February 3, 2026*

Your content here with **markdown** support.

> A blockquote for emphasis

- Bullet points work
- [Links too](https://example.com)
```

2. The file will appear on the desktop automatically after rebuild.

### Add a New Project

1. Create file at `apps/web/src/content/projects/my-project.md`:

```markdown
---
title: My Project.md
---
# Project Name

**Status:** Active  
**Tech:** React, Python, PostgreSQL

## Description

What the project does.

## Links

- [Live Site](https://example.com)
- [Source](https://github.com/user/repo)
```

### Add a New Desktop Folder

1. Create directory: `apps/web/src/content/my-folder/`
2. Add `.md` files inside it
3. Folder appears on desktop automatically

### Add an Image

1. Place image in `apps/web/public/images/`
2. Reference in markdown: `![Alt text](/images/my-image.png)`

### Update About Me

Edit `apps/web/src/content/about-me.md`

---

## API Development

### Add a New Endpoint

1. **Create route file** `apps/agent/routes/my_route.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/my-feature", tags=["my-feature"])

class MyRequest(BaseModel):
    data: str

class MyResponse(BaseModel):
    success: bool
    result: str

@router.post("/action", response_model=MyResponse)
async def my_action(request: MyRequest):
    """Description of what this does."""
    try:
        # Business logic here
        return MyResponse(success=True, result="Done")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Register route in `apps/agent/app.py`**:

```python
from routes.my_route import router as my_router

# In the app setup section:
app.include_router(my_router)
```

3. **Update API info endpoint** (optional) in `app.py`:

```python
@app.get("/api/v1")
async def api_info():
    return {
        "endpoints": {
            # ... existing endpoints ...
            "my_feature": "/api/v1/my-feature",
        }
    }
```

### Add Business Logic Service

1. **Create service file** `apps/agent/services/my_service.py`:

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MyService:
    def __init__(self, config_value: str):
        self.config_value = config_value
    
    def do_something(self, input_data: str) -> dict:
        """Process input and return result."""
        logger.info(f"Processing: {input_data}")
        
        # Your logic here
        
        return {"result": "processed"}
```

2. **Use in route**:

```python
from services.my_service import MyService

service = MyService(config_value="value")

@router.post("/action")
async def my_action(request: MyRequest):
    result = service.do_something(request.data)
    return MyResponse(success=True, **result)
```

### Add a New Pydantic Model

Edit `apps/agent/models/task_models.py`:

```python
from pydantic import BaseModel
from typing import Optional, List

class MyNewModel(BaseModel):
    required_field: str
    optional_field: Optional[str] = None
    list_field: List[str] = []
```

### Add a New Environment Variable

1. **Update config** `apps/agent/utils/config.py`:

```python
class Config:
    # ... existing vars ...
    MY_NEW_VAR: str = os.getenv("MY_NEW_VAR", "default_value")
```

2. **Add to validation if required**:

```python
@classmethod
def validate_required_env_vars(cls) -> None:
    required_vars = [
        # ... existing ...
        ("MY_NEW_VAR", cls.MY_NEW_VAR),
    ]
```

3. **Document in README** and update `.env.example` if exists.

### Modify Task Creation Logic

Edit `apps/agent/services/task_creation.py`:

- `synthesize_task_info()` - AI parsing logic
- `create_notion_task()` - Notion page creation
- `extract_text_from_image_url()` - OCR logic
- `convert_markdown_to_notion_rich_text()` - Formatting

---

## Scheduler Modifications

### Change Scheduling Algorithm

Edit `apps/agent/scheduler/scheduling_algorithm.py`:

- `assign_tasks_to_slots()` - Main assignment logic
- Task sorting and prioritization

### Modify Time Slot Generation

Edit `apps/agent/scheduler/time_slots.py`:

- `generate_time_slots()` - Slot creation
- Work hours logic
- Weekday filtering

### Change Scheduler Service Behavior

Edit `apps/agent/services/task_scheduler.py`:

- `run_scheduling_cycle()` - Main entry point
- `fetch_tasks_to_schedule()` - Notion query
- `update_task_schedule()` - Notion update

### Add New Scheduler Configuration

1. Add environment variable to `utils/config.py`
2. Pass to `TaskSchedulerService` in `app.py`
3. Use in scheduler logic
4. Update `scheduler/README.md`

---

## Frontend Changes

### Modify the Desktop Layout

Edit `apps/web/src/components/Desktop.tsx`

### Change Window Appearance

Edit `apps/web/src/components/WindowFrame.tsx`

### Modify the Chat Page

Edit `apps/web/src/app/chat/page.tsx`

### Add a New Component

1. Create `apps/web/src/components/MyComponent.tsx`:

```tsx
import React from 'react';

interface MyComponentProps {
  title: string;
}

export const MyComponent: React.FC<MyComponentProps> = ({ title }) => {
  return (
    <div className="p-4">
      <h1>{title}</h1>
    </div>
  );
};
```

2. Import and use where needed.

### Add a New Page

Create `apps/web/src/app/my-page/page.tsx`:

```tsx
export default function MyPage() {
  return (
    <main>
      <h1>My Page</h1>
    </main>
  );
}
```

Accessible at `/my-page`.

### Modify Styling

- Global styles: `apps/web/src/app/globals.css`
- Component styles: Use Tailwind classes inline

---

## Testing

### Run Agent Tests

```bash
cd apps/agent
pytest tests/
```

### Run a Specific Test

```bash
cd apps/agent
pytest tests/test_scheduling_algorithm.py -v
```

### Add a New Test

Create `apps/agent/tests/test_my_feature.py`:

```python
import pytest
from services.my_service import MyService

def test_my_feature_works():
    service = MyService("test_config")
    result = service.do_something("input")
    assert result["result"] == "processed"

def test_my_feature_handles_errors():
    service = MyService("test_config")
    with pytest.raises(ValueError):
        service.do_something(None)
```

### Test API Endpoints Manually

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Task creation (dry run)
curl -X POST http://localhost:8000/api/v1/task_creator \
  -H "Content-Type: application/json" \
  -d '{"text_inputs": ["Test task by Friday"], "dry_run": true}'

# Scheduler status
curl http://localhost:8000/api/v1/scheduler/status

# Trigger scheduling
curl -X POST http://localhost:8000/api/v1/scheduler/run
```

---

## Deployment

### Deploy Web Changes

1. Commit changes
2. Push to `desktop-app` branch
3. Railway auto-deploys

```bash
git add .
git commit -m "feat(web): description"
git push origin desktop-app
```

### Deploy Agent Changes

1. Commit changes
2. Push to `main` branch
3. Railway auto-deploys

```bash
git add .
git commit -m "feat(agent): description"
git push origin main
```

### Update Environment Variables

1. Go to [Railway Dashboard](https://railway.app)
2. Select the service (web or agent)
3. Go to **Variables** tab
4. Add/update variables
5. Click **Deploy** or wait for auto-redeploy

### Check Deployment Logs

1. Go to Railway Dashboard
2. Select the service
3. Click **Deployments**
4. Click on the latest deployment
5. View **Build Logs** or **Deploy Logs**

### Rollback a Deployment

1. Go to Railway Dashboard
2. Select the service
3. Click **Deployments**
4. Find the previous good deployment
5. Click **Redeploy**

---

## Debugging Tips

### Agent Not Starting

1. Check required env vars are set
2. Look at Railway logs for error messages
3. Test locally first

### Scheduler Not Running

1. Verify `LIVEPEER_NOTION_API_KEY` and `LIVEPEER_NOTION_DB_ID` are set
2. Check `/api/v1/scheduler/health`
3. Look for scheduler logs: "Scheduler background task started"

### Content Not Appearing

1. Run `npm run generate-content` in `apps/web`
2. Check frontmatter syntax (must have `title:`)
3. Verify file is in correct directory

### API Returning 401

1. Check `BEARER_TOKEN` is set (or unset for no auth)
2. Verify token in request header matches

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more issues.
