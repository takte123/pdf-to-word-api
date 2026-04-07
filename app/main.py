"""
Main FastAPI application - Minimal version for debugging
"""

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    status,
    Request,
    BackgroundTasks,
)
from fastapi.responses import FileResponse
from datetime import datetime
from pathlib import Path
import os


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

# Ensure directories exist on module load
Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
Path(settings.outputs_dir).mkdir(parents=True, exist_ok=True)
Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)


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
