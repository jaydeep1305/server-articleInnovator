# Multi-stage build for monitoring-service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Development stage
FROM base as development

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5006

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5006/health || exit 1

# Run the application
CMD ["python", "run.py"]

# Production stage
FROM base as production

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn

# Copy application code
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5006

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5006/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5006", "--workers", "4", "--timeout", "120", "run:app"]
