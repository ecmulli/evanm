# Use Python 3.12 slim image
FROM python:3.12-slim

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Set working directory
WORKDIR /app

# Copy pyproject.toml first for better caching
COPY apps/agent/pyproject.toml ./apps/agent/

# Install Python dependencies using uv
WORKDIR /app/apps/agent
RUN uv pip install --system --no-cache \
    fastapi>=0.115.6 \
    hypercorn>=0.17.3 \
    python-dotenv>=1.0.1 \
    requests>=2.32.3 \
    notion-client>=2.2.1 \
    openai>=1.57.3 \
    pydantic>=2.10.5 \
    python-multipart>=0.0.17

# Copy application code
WORKDIR /app
COPY apps/agent/ ./apps/agent/

# Set final working directory
WORKDIR /app/apps/agent

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app/apps/agent

# Run the application
CMD ["python", "app.py"]
