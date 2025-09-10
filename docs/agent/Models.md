# Agent Models

Defined in `apps/agent/models/task_models.py`.

## TaskCreationRequest
Fields:
- **text_inputs** (List[str], required): one or more natural language inputs
- **image_urls** (List[str], optional): image URLs or data URLs for OCR
- **suggested_workspace** (str, optional): one of Personal | Livepeer | Vanquish
- **dry_run** (bool, default False): if true, validate only

Example:
```json
{
  "text_inputs": [
    "Create onboarding flow with OAuth",
    "Due next Monday"
  ],
  "suggested_workspace": "Personal",
  "dry_run": true
}
```

## ParsedTaskData
- **task_name** (str)
- **workspace** (str)
- **priority** (str)
- **estimated_hours** (float)
- **due_date** (str, YYYY-MM-DD)
- **description** (str)
- **acceptance_criteria** (str)
- **labels** (List[str], default [])
- **status** (str, default "Todo")
- **team** (str, default "Personal")

## TaskCreationResponse
- **success** (bool)
- **message** (str)
- **task_id** (str | null)
- **task_url** (str | null)
- **parsed_data** (ParsedTaskData)
- **dry_run** (bool)

Example:
```json
{
  "success": true,
  "message": "Task 'Onboarding flow' created successfully in Personal",
  "task_id": "<notion-page-id>",
  "task_url": "https://www.notion.so/<id>",
  "parsed_data": { /* see ParsedTaskData */ },
  "dry_run": false
}
```

## ErrorResponse
- **success**: always false
- **error** (str): error category
- **details** (str | null): human-readable details