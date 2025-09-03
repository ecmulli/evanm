# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY packages/agent/requirements.txt ./packages/agent/

# Install Python dependencies
WORKDIR /app/packages/agent
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
WORKDIR /app
COPY packages/agent/ ./packages/agent/

# Set final working directory
WORKDIR /app/packages/agent

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app/packages/agent
ENV PORT=8000

# Run the application
CMD ["python", "app.py"]
