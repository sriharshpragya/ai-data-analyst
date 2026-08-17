# ============================================
# AI Data Analyst - Production Dockerfile
# Multi-stage build for smaller final image
# ============================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r analyst && useradd -r -g analyst analyst

# Copy Python packages from builder
COPY --from=builder /root/.local /home/analyst/.local

# Copy application code
COPY --chown=analyst:analyst app/ ./app/
COPY --chown=analyst:analyst database/ ./database/

# Create charts directory
RUN mkdir -p /app/charts && chown -R analyst:analyst /app/charts

# Environment variables
ENV PATH=/home/analyst/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

# Switch to non-root user
USER analyst

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:$\{APP_PORT\}/health || exit 1

# Expose port
EXPOSE 8000

# Run the API
CMD ["python", "-m", "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
