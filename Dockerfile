FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    httpx \
    pydantic \
    pyyaml \
    faker \
    fastapi[standard] \
    uvicorn[standard] \
    websockets \
    aiokafka \
    asyncio-throttle \
    numpy \
    python-multipart

# Copy application code
COPY simulator/ ./simulator/
COPY scenarios/ ./scenarios/
COPY run.py ./

# Create directories for logs and exports
RUN mkdir -p /app/logs /app/exports

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8095

# Create non-root user
RUN useradd --create-home --shell /bin/bash simulator
RUN chown -R simulator:simulator /app
USER simulator

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8095/api/health || exit 1

# Default command
CMD ["python", "run.py", "--scenario", "normal_day", "--dashboard", "--dashboard-port", "8095"]