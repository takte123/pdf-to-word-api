"""
Request/Response schemas
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response"""

    detail: str


class ConversionResponse(BaseModel):
    """Conversion response"""

    file_id: str
    status: str
    message: Optional[str] = None
    download_url: Optional[str] = None
