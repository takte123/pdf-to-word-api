"""
File utilities
"""

import uuid
import magic
from pathlib import Path
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.logging import logger


ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/x-pdf",
}

ALLOWED_EXTENSIONS = {".pdf"}


def generate_file_id() -> str:
    """Generate unique file ID"""
    return str(uuid.uuid4())


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension"""
    return Path(filename).suffix.lower()


def validate_file_type(file_path: Path) -> bool:
    """
    Validate file type using magic number detection

    Args:
        file_path: Path to file to validate

    Returns:
        True if file is valid PDF
    """
    try:
        mime = magic.from_file(str(file_path), mime=True)
        return mime in ALLOWED_MIME_TYPES
    except Exception as e:
        logger.error(f"File type validation error: {e}")
        return False


def validate_upload_file(filename: str) -> tuple[bool, str | None]:
    """
    Validate uploaded file by extension

    Args:
        filename: Name of uploaded file

    Returns:
        Tuple of (is_valid, error_message)
    """
    ext = get_file_extension(filename)

    if ext not in ALLOWED_EXTENSIONS:
        return (
            False,
            f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    return True, None


async def save_upload_file(upload_file: UploadFile, file_id: str) -> Path:
    """
    Save uploaded file to uploads directory

    Args:
        upload_file: FastAPI UploadFile
        file_id: Unique file ID

    Returns:
        Path to saved file
    """
    settings = get_settings()
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Get extension from original filename
    ext = get_file_extension(upload_file.filename or "document.pdf")
    file_path = uploads_dir / f"{file_id}{ext}"

    # Write file in chunks
    content = await upload_file.read()
    file_path.write_bytes(content)

    logger.info(f"Saved upload: {file_path} ({len(content)} bytes)")
    return file_path


def get_output_path(file_id: str) -> Path:
    """Get path for output DOCX file"""
    settings = get_settings()
    outputs_dir = Path(settings.outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir / f"{file_id}.docx"
