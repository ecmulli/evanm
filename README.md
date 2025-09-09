# EvanM Monorepo

A personal monorepo containing multiple applications and utilities.

## Structure

```
evanm/
├── apps/
│   ├── web/           # Next.js website
│   ├── agent/         # Python FastAPI agent service
│   ├── jobs/          # Python scripts for scheduled jobs
│   └── ...            # Future apps
├── package.json       # Root package configuration
└── README.md
```

## Apps

### Web App
Located in `apps/web/`, this is the main Next.js website for evanm.xyz.

### Agent Service
Located in `apps/agent/`, this contains the Python FastAPI service for AI agent functionality.

### Jobs Service
Located in `apps/jobs/`, this contains Python scripts designed to run various scheduled jobs and automation tasks.

## Getting Started

### Prerequisites
- Node.js >= 18.0.0
- Python >= 3.8
- npm >= 8.0.0

### Installation

1. Install root dependencies:
   ```bash
   npm install
   ```

2. Install Python dependencies for jobs package:
   ```bash
   npm run jobs:install
   ```

### Usage

#### Jobs Package
```bash
# Install dependencies
npm run jobs:install

# Run jobs
npm run jobs:run
```

## Development

This monorepo uses npm workspaces to manage multiple packages. Each package can have its own dependencies and build processes.

### Adding New Packages

1. Create a new directory in `apps/`
2. Add appropriate configuration files
3. Update root package.json scripts if needed

### Commands

- `npm run install:all` - Install all dependencies
- `npm run clean` - Clean all node_modules
- `npm run jobs:install` - Install Python dependencies for jobs package
- `npm run jobs:run` - Run the jobs package

## Contributing

This is a personal monorepo, but feel free to suggest improvements or report issues.
