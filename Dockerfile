# Multi-Agent Audio Processing System - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs backups

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from src.system import create_system; s=create_system(); s.start(); h=s.get_health(); s.stop(); exit(0 if h['health_score'] > 50 else 1)"

# Expose port (if you add API later)
EXPOSE 8000

# Run the application
CMD ["python", "my_audio_app.py"]
