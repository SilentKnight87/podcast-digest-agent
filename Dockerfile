# Multi-stage build for optimized production image
FROM python:3.11-slim AS builder

# Set work directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install runtime dependencies (ffmpeg for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy Python dependencies from builder and set ownership
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser ./src /app/src

# Create necessary directories (don't copy from local as they may not exist)
RUN mkdir -p /app/input /app/output_audio && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Make sure we can find the installed packages
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Expose port (Cloud Run sets PORT env variable)
EXPOSE 8080

# Remove health check for now - Cloud Run has its own health checks

# Set default PORT for local testing
ENV PORT=8080

# Run the application with uvicorn
# Use shell form to properly expand PORT variable
CMD uvicorn src.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --proxy-headers \
    --forwarded-allow-ips="*"
