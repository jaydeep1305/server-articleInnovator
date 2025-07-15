# Blog Microservice Dockerfile
# This Dockerfile creates a production-ready container for the blog microservice
# with proper security, optimization, and health checks.

# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set metadata labels
LABEL maintainer="Blog Microservice Team"
LABEL version="1.0.0"
LABEL description="Flask-based blog microservice with PostgreSQL"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app

# Create non-root user for security
RUN groupadd -r blogservice && useradd -r -g blogservice -d /app -s /bin/bash blogservice

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R blogservice:blogservice /app

# Switch to non-root user
USER blogservice

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health/live || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]