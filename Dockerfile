FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    fonts-liberation \
    fonts-dejavu \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Create directories with appuser ownership
RUN mkdir -p uploads outputs logs && chown -R appuser:appuser /app

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser app/ ./app/

# Switch to non-root user
USER appuser

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Run the application using PORT env variable (defaults to 8000)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
