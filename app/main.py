"""
Main FastAPI application
"""

from contextlib import asynccontextmanager

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
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime


from app.core.config import get_settings
from app.core.logging import logger
from app.api.auth import APIKeyMiddleware
from app.api.schemas import HealthResponse, ErrorResponse
from app.services.converter import get_converter_service, ConversionError
from app.services.cleanup import get_cleanup_service
from app.utils.file import (
    generate_file_id,
    validate_upload_file,
    validate_file_type,
    save_upload_file,
    get_output_path,
)

# Settings
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting PDF to Word Converter API")
    cleanup_service = get_cleanup_service()
    cleanup_service.start()
    yield
    # Shutdown
    logger.info("Shutting down PDF to Word Converter API")
    cleanup_service.stop()


# Create FastAPI app
app = FastAPI(
    title="PDF to Word Converter API",
    description="Production-ready REST API for converting PDF files to DOCX format",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(APIKeyMiddleware)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "status": "ok",
        "message": "PDF to Word Converter API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", timestamp=datetime.utcnow())


@app.post(
    "/convert/pdf-to-word",
    responses={
        200: {"description": "Converted DOCX file"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Conversion failed"},
    },
)
@limiter.limit(settings.rate_limit)
async def convert_pdf_to_word(
    request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    """
    Convert a PDF file to DOCX format.

    - **file**: PDF file to convert (max 20MB)
    - Returns the converted DOCX file as a download
    """
    # Check file size
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size / 1024 / 1024}MB",
        )

    # Reset file pointer
    await file.seek(0)

    # Validate file extension
    is_valid, error = validate_upload_file(file.filename or "")
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Generate unique file ID
    file_id = generate_file_id()
    input_path = None

    try:
        # Save uploaded file
        input_path = await save_upload_file(file, file_id)

        # Validate file type (magic number check)
        if not validate_file_type(input_path):
            # Clean up invalid file
            input_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PDF files are allowed.",
            )

        # Validate PDF structure
        converter_service = get_converter_service()
        is_valid_pdf, pdf_error = converter_service.validate_pdf(input_path)
        if not is_valid_pdf:
            input_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid PDF file: {pdf_error}",
            )

        # Convert file
        output_path = get_output_path(file_id)
        await converter_service.convert(input_path, output_path)

        # Protect file from cleanup during download
        cleanup_service = get_cleanup_service()
        cleanup_service.protect_file(str(output_path))

        # Schedule unprotection after response
        def unprotect_and_cleanup():
            cleanup_service.unprotect_file(str(output_path))

        background_tasks.add_task(unprotect_and_cleanup)

        # Return file response
        return FileResponse(
            path=output_path,
            filename=f"{file_id}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    except ConversionError as e:
        logger.error(f"Conversion failed for {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error for {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        # Clean up input file
        if input_path is not None:
            input_path.unlink(missing_ok=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
