"""
Main FastAPI application - Minimal version for debugging
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Print startup info to stderr for debugging
print("=== STARTING APPLICATION ===", file=sys.stderr)
print(f"PORT env: {os.getenv('PORT')}", file=sys.stderr)
print(f"Current dir: {os.getcwd()}", file=sys.stderr)
print(f"Python path: {sys.path}", file=sys.stderr)

from fastapi import FastAPI


# Simple in-memory settings
class Settings:
    api_key = os.getenv("API_KEY", "dev-api-key-change-in-production")
    max_file_size = int(os.getenv("MAX_FILE_SIZE", "20971520"))
    file_retention_minutes = int(os.getenv("FILE_RETENTION_MINUTES", "30"))
    uploads_dir = "uploads"
    outputs_dir = "outputs"
    logs_dir = "logs"


settings = Settings()

# Create FastAPI app - NO lifespan, NO middleware for now
app = FastAPI(
    title="PDF to Word Converter API",
    description="Production-ready REST API for converting PDF files to DOCX format",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

print("=== FASTAPI APP CREATED ===", file=sys.stderr)

# Ensure directories exist on module load
try:
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.outputs_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)
    print("=== DIRECTORIES CREATED ===", file=sys.stderr)
except Exception as e:
    print(f"=== DIRECTORY ERROR: {e} ===", file=sys.stderr)


@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "status": "ok",
        "message": "PDF to Word Converter API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/test")
async def test():
    """Simple test endpoint"""
    return {"test": "ok", "port": os.getenv("PORT", "8000")}


print("=== ROUTES REGISTERED ===", file=sys.stderr)
