# 🤖 AI Task Creation Agent

An intelligent agent that creates well-structured Notion tasks from various inputs using AI synthesis.

## Features

### 🧠 **Intelligent Context Parsing**
The agent automatically detects:

**Priority Clues:**
- `"urgent"`, `"ASAP"`, `"blocking"`, `"critical"` → **ASAP**
- `"high priority"`, `"important"`, `"deadline"` → **High** 
- `"low priority"`, `"nice to have"`, `"when time"` → **Low**
- Default: **Medium**

**Duration Clues:**
- `"quick"`, `"15 min"` → **0.25 hours**
- `"30 minutes"`, `"half hour"` → **0.5 hours**
- `"1 hour"`, `"hour task"` → **1 hour**
- `"couple hours"`, `"2 hours"` → **2 hours**  
- `"half day"`, `"4 hours"` → **4 hours**
- `"full day"`, `"8 hours"` → **8 hours**
- Default: **1 hour**

**Workspace Clues:**
- `"Livepeer"`, `"streaming"`, `"analytics dashboard"` → **Livepeer**
- `"Vanquish"`, `"client"`, `"marketing"`, `"campaign"` → **Vanquish**
- Default: **Personal**

### 🎯 **Multi-Input Support**
- **Text descriptions** (user feedback, requirements, context)
- **Screenshots** (OCR text extraction using GPT-4 Vision)
- **File uploads** (text files with requirements)

### 📋 **Rich Task Generation**
- **Smart task titles** (actionable and specific)
- **Detailed descriptions** (comprehensive context)
- **Interactive checklists** (acceptance criteria as checkable Notion to-do items)
- **Proper field mapping** (priority, duration, workspace)

## Setup

### 1. Environment Variables
Add to your `.env.dev` file:
```bash
# OpenAI
OPENAI_API_KEY="your_openai_api_key"

# Notion (already configured for sync)
PERSONAL_NOTION_API_KEY="your_notion_key"
PERSONAL_NOTION_DB_ID="your_database_id"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### 🖥️ **Command Line Interface**

```bash
# Simple text input
python agent/task_creator.py --input "Fix the urgent Livepeer dashboard bug - 2 hour task"

# From file
python agent/task_creator.py --file requirements.txt --workspace Vanquish

# With screenshots  
python agent/task_creator.py --input "User reported this error" --screenshots error1.png,error2.png

# Dry run (test without creating)
python agent/task_creator.py --input "Test task" --dry-run
```

### 📓 **Jupyter Notebook Interface**

Use the interactive notebook: `Task Creation Agent.ipynb`

```python
from agent.task_creator import TaskCreationAgent

# Initialize agent
agent = TaskCreationAgent(dry_run=True)

# Create task from text
page_id = agent.create_task_from_inputs(
    text_inputs=["Urgent Livepeer analytics fix - 2 hour task"],
    suggested_workspace="Livepeer"
)
```

### 🐍 **Python Script Integration**

```python
from agent.task_creator import TaskCreationAgent

def create_task_from_feedback(user_feedback: str):
    agent = TaskCreationAgent(dry_run=False)
    return agent.create_task_from_inputs(
        text_inputs=[user_feedback]
    )

# Example usage
task_id = create_task_from_feedback("""
User John reported: "The mobile app crashes when sharing videos. 
This is blocking our iOS users. High priority fix needed - probably 4 hours of work."
""")
```

## Examples

### Basic Examples

```bash
# High priority, Livepeer workspace, 2 hours
python agent/task_creator.py --input "Urgent: Fix Livepeer dashboard performance - 2 hour task"

# Low priority, Vanquish workspace, 30 minutes  
python agent/task_creator.py --input "Update Vanquish client logo when time permits - quick 30 min task"

# Personal workspace, 1 hour (defaults)
python agent/task_creator.py --input "Organize my project files"
```

### Advanced Examples

```bash
# Multiple inputs with context
python agent/task_creator.py --input "
User feedback: 'Video upload fails on mobile'
Technical note: Memory leak in iOS app
Priority: This is blocking users - urgent fix needed
Estimate: Should take about 4 hours to debug and fix
"

# Screenshot analysis
python agent/task_creator.py --input "
User sent this error screenshot from the Vanquish campaign dashboard.
They can't save their ad settings. Client is frustrated.
" --screenshots dashboard_error.png
```

## Output

The agent provides detailed logging of the AI synthesis:

```
🤖 AI successfully synthesized task information
📋 Task: Fix Livepeer dashboard performance issues
🏢 Workspace: Livepeer
⚡ Priority: High
⏱️ Duration: 2.0 hours
📝 Description: Optimize the Livepeer analytics dashboard loading time...
✅ Acceptance Criteria: - [ ] Dashboard loads in under 3 seconds
- [ ] All charts display correct data
- [ ] No console errors present
- [ ] Performance metrics improved by 50%
🧪 DRY RUN: Would create task in Livepeer database
```

### 📝 **Interactive Checklists**

The agent creates acceptance criteria as interactive Notion to-do items:
- AI automatically formats criteria as markdown checklists
- Each criterion becomes a checkable to-do block in Notion
- Easy to track completion progress
- Clear, specific, and measurable requirements

**Example in Notion:**
```
Description: Optimize the dashboard performance...

Acceptance Criteria:
☐ Dashboard loads in under 3 seconds
☐ All charts display correct data  
☐ No console errors present
☐ Performance metrics improved by 50%
```

## Testing

Run the test examples to see intelligent parsing in action:

```bash
python agent/test_examples.py
```

## Integration with Motion Sync

Tasks created by the agent automatically sync to Motion AI via the existing Motion sync workflow, enabling:
- **AI-scheduled work blocks** in your calendar
- **Bidirectional updates** between Notion and Motion
- **Automated priority-based scheduling**

## Future Enhancements

- **Webhook server** for real-time task creation
- **Slack/Discord integration** for team task requests
- **Email parsing** for task creation from emails
- **Voice input** support for hands-free task creation
- **Template system** for common task types
