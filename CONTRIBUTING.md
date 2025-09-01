# Contributing to EvanM Monorepo

This document outlines the development practices and guidelines for contributing to the EvanM monorepo.

## Getting Started

### Prerequisites

- Node.js >= 18.0.0
- Python >= 3.8
- npm >= 8.0.0
- Make (optional, for convenience commands)

### Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   make install
   # or
   npm install && make jobs-install
   ```

## Monorepo Structure

This repository follows a package-based monorepo structure:

```
evanm/
├── packages/              # All packages live here
│   ├── jobs/             # Python jobs package
│   └── ...               # Future packages
├── .vscode/              # VS Code configuration
├── package.json          # Root package configuration
├── Makefile             # Development commands
└── README.md
```

## Package Guidelines

### Creating a New Package

1. Create a new directory in `packages/`
2. Follow the naming convention: `packages/<package-name>/`
3. Include appropriate configuration files:
   - `package.json` (for Node.js packages)
   - `requirements.txt` or `pyproject.toml` (for Python packages)
   - `README.md` with package documentation
   - Test directory with appropriate test files

### Package Structure

Each package should be self-contained with:
- Clear documentation
- Comprehensive tests
- Proper dependency management
- Consistent code formatting

## Development Workflow

### Commands

Use the Makefile for common development tasks:

```bash
# General commands
make help          # Show available commands
make install       # Install all dependencies
make clean         # Clean all build artifacts
make test          # Run all tests
make lint          # Lint all packages
make format        # Format all code

# Jobs package specific
make jobs-install  # Install jobs dependencies
make jobs-run      # Run jobs scheduler
make jobs-dev      # Run in development mode
make jobs-test     # Run jobs tests
make jobs-lint     # Lint jobs code
make jobs-format   # Format jobs code
```

### Code Quality

All packages should maintain high code quality standards:

#### Python Packages
- **Formatting**: Use `black` with 88 character line length
- **Linting**: Use `flake8` for style and error checking
- **Testing**: Use `pytest` with good coverage
- **Documentation**: Include docstrings and type hints

#### Node.js Packages (future)
- **Formatting**: Use `prettier`
- **Linting**: Use `eslint`
- **Testing**: Use `jest` or similar

### Testing

- Write comprehensive tests for all functionality
- Aim for high test coverage
- Include both unit and integration tests
- Use appropriate testing frameworks for each language

## Package-Specific Guidelines

### Jobs Package

The jobs package is for scheduled automation tasks:

- All jobs should inherit from `BaseJob`
- Include proper error handling and logging
- Add configuration options via environment variables
- Write tests for job functionality
- Document scheduling and configuration options

Example job structure:
```python
from jobs.base_job import BaseJob

class MyJob(BaseJob):
    def __init__(self, config=None):
        super().__init__("my_job", config)
    
    def run(self) -> bool:
        # Job implementation
        return True
```

## VS Code Integration

The repository includes VS Code configuration for:
- Python development with proper linting and formatting
- Debug configurations for running jobs
- Task definitions for common operations
- Workspace settings optimized for the monorepo structure

## Commit Guidelines

- Use clear, descriptive commit messages
- Include the package name in commits when relevant
- Follow conventional commit format when possible:
  - `feat(jobs): add new status check job`
  - `fix(jobs): handle network timeout gracefully`
  - `docs: update contributing guidelines`

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the guidelines above
3. Ensure all tests pass
4. Update documentation as needed
5. Submit a pull request with a clear description

## Adding Dependencies

### Python Dependencies (jobs package)
- Add to `requirements.txt` with version pins
- Update `pyproject.toml` if using modern Python packaging
- Document any new optional dependencies

### Node.js Dependencies
- Use `npm install <package>` to add to root dependencies
- Use `npm install -w <workspace> <package>` for package-specific deps

## Questions and Support

For questions about contributing or development setup, please:
1. Check existing documentation
2. Look at example implementations
3. Create an issue for clarification

## Future Packages

When adding new packages, consider:
- Language and framework choice
- Integration with existing tooling
- Documentation and testing standards
- Deployment and configuration needs
