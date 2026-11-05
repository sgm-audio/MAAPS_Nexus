# Multi-Agent Audio Processing System - Production Dockerfile
# SECURITY HARDENED - BULLETPROOF BUILD

# ============================================
# Stage 1: Builder (compile Python packages)
# ============================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install ONLY build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libsndfile1-dev \
       libffi-dev \
       libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-api.txt ./

# Create virtual environment and install packages
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip==25.3 setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt -r requirements-api.txt

# ============================================
# Stage 2: Runtime (minimal production image)
# ============================================
FROM python:3.11-slim-bookworm

# Install ONLY runtime dependencies (NO dev packages)
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
       libsndfile1 \
       ffmpeg \
       curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r maaps && useradd -r -g maaps -s /sbin/nologin maaps

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=maaps:maaps . .

# Create necessary directories with proper permissions
RUN mkdir -p data logs backups \
    && chown -R maaps:maaps /app/data /app/logs /app/backups

# Security: Drop privileges
USER maaps

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AGENT_LOG_LEVEL=INFO \
    PORT=8000

# Health check (lightweight, no requests library needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose API port
EXPOSE 8000

# Run API with gunicorn for production (better than uvicorn alone)
CMD ["gunicorn", "api.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--timeout", "120", \
     "--graceful-timeout", "30"]
