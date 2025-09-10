# TaskCreationService Reference

Defined in `apps/agent/services/task_creation.py`.

```python
from services.task_creation import TaskCreationService
```

## class TaskCreationService(dry_run: bool = False)
Service for creating tasks using OpenAI and Notion integration.

- **dry_run**: if True, validates and synthesizes but does not create Notion pages

### __init__(dry_run: bool = False)
Initializes OpenAI and Notion clients using environment variables.

Raises `ValueError` if required env vars are missing.

### extract_urls_from_text(text: str) -> List[str]
Extracts all URLs from a single text string.

### extract_all_urls_from_inputs(text_inputs: List[str]) -> List[str]
Aggregates unique URLs from a list of text inputs.

### convert_markdown_to_notion_rich_text(text: str) -> List[Dict]
Converts markdown text to Notion rich text JSON (preserves links and plain URLs).

### extract_text_from_image_url(image_url: str) -> str
Uses the OpenAI Vision model to OCR text content from an image URL or data URL.

### synthesize_task_info(text_inputs: List[str], image_texts: List[str] = None, suggested_workspace: Optional[str] = None) -> Dict[str, Any]
Uses OpenAI to synthesize a normalized task object with fields:
- task_name, workspace, priority, estimated_hours, due_date, description, acceptance_criteria, labels[], status, team

Applies validation and sensible defaults.

### create_notion_task(task_info: Dict[str, Any]) -> Optional[str]
Creates a Notion page in the Hub database using the provided task info. Returns the Notion page ID or `None` in dry-run mode.

### create_task_from_inputs(text_inputs: List[str], image_urls: List[str] = None, suggested_workspace: Optional[str] = None) -> Dict[str, Any]
High-level method that OCRs images (if any), synthesizes task info, and creates the Notion page.

Returns:
```json
{
  "task_info": { ... },
  "page_id": "string|null",
  "page_url": "string|null"
}
```

## Usage Examples

### Dry-run preview (no Notion write)
```python
service = TaskCreationService(dry_run=True)
result = service.create_task_from_inputs([
    "Build landing page hero; due next Friday; high priority; add link https://example.com/brief"
])
print(result["task_info"])  # inspect parsed fields
```

### Create task in Notion
```python
service = TaskCreationService(dry_run=False)
result = service.create_task_from_inputs([
    "Prepare Q3 marketing plan; labels Strategic; estimate 8 hours"
], suggested_workspace="Vanquish")
print(result["page_id"], result["page_url"])  # Notion identifiers
```