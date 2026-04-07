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

# Create directories
RUN mkdir -p uploads outputs logs

# Copy requirements and install as root (to ensure it's in PATH)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user and set permissions
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Use shell form to expand PORT variable
ENV PYTHONUNBUFFERED=1
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
