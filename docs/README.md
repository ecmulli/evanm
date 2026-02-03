# Documentation

Welcome to the evanm.xyz monorepo documentation.

## Quick Links

| Document | Description |
|----------|-------------|
| [AGENTS.md](../AGENTS.md) | **Start here** - Main guide for AI agents |
| [Quick Start](./QUICK_START.md) | Fast onboarding for new agents |
| [Common Tasks](./COMMON_TASKS.md) | Step-by-step task guides |
| [Architecture](./ARCHITECTURE.md) | System design and diagrams |
| [Troubleshooting](./TROUBLESHOOTING.md) | Common issues and solutions |

## API Reference

| Document | Description |
|----------|-------------|
| [Agent API](./agent/README.md) | Task creation API reference |
| [Scheduler API](./agent/Scheduler.md) | Task scheduling API reference |
| [Config](./agent/Config.md) | Environment variables |
| [Models](./agent/Models.md) | Pydantic model reference |
| [TaskCreationService](./agent/TaskCreationService.md) | Service class reference |

## App Documentation

| Document | Description |
|----------|-------------|
| [Web App](./web/README.md) | Next.js website documentation |
| [Jobs](./jobs/README.md) | Sync scripts documentation |

## Quick Navigation by Task

### Working on the Website

1. Read [AGENTS.md - Web Content Management](../AGENTS.md#web-content-management)
2. Add files to `apps/web/src/content/`
3. See [Common Tasks - Adding Website Content](./COMMON_TASKS.md#adding-website-content)

### Working on the API

1. Read [AGENTS.md - Agent API](../AGENTS.md#agent-api)
2. Modify files in `apps/agent/`
3. See [Common Tasks - API Development](./COMMON_TASKS.md#api-development)

### Working on the Scheduler

1. Read [Scheduler API Reference](./agent/Scheduler.md)
2. Modify files in `apps/agent/scheduler/`
3. See [Common Tasks - Scheduler Modifications](./COMMON_TASKS.md#scheduler-modifications)

### Deploying Changes

1. Read [AGENTS.md - Deployment](../AGENTS.md#deployment)
2. Push to appropriate branch
3. See [Common Tasks - Deployment](./COMMON_TASKS.md#deployment)

### Debugging Issues

1. Check [Troubleshooting](./TROUBLESHOOTING.md)
2. Look at relevant app logs
3. Test locally first

## Repository Structure

```
evanm/
├── apps/
│   ├── web/          # Next.js website
│   ├── agent/        # FastAPI backend
│   └── jobs/         # Sync scripts (archived)
├── docs/             # This documentation
├── AGENTS.md         # Main AI agent guide
├── CONTRIBUTING.md   # Development guidelines
└── README.md         # Project overview
```

## Documentation Conventions

- **AGENTS.md** is the main entry point for AI agents
- **docs/** contains detailed reference documentation
- Each app has its own README with setup instructions
- Task-oriented guides are in COMMON_TASKS.md
- Troubleshooting covers common issues across all components

## Contributing to Documentation

When updating documentation:

1. Keep AGENTS.md as the main entry point
2. Link between documents rather than duplicating content
3. Use consistent formatting (markdown tables, code blocks)
4. Include practical examples
5. Update the relevant index when adding new docs
