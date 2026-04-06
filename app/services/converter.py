"""
PDF to DOCX conversion service with fallback
"""

import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import shutil

from pdf2docx import Converter
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import get_settings
from app.core.logging import logger


class ConversionError(Exception):
    """Custom exception for conversion errors"""

    pass


class PDFConverterService:
    """Service for converting PDF to DOCX"""

    def __init__(self):
        self.settings = get_settings()

    async def convert(self, input_path: Path, output_path: Path) -> bool:
        """
        Convert PDF to DOCX with fallback

        Args:
            input_path: Path to input PDF file
            output_path: Path for output DOCX file

        Returns:
            True if conversion successful

        Raises:
            ConversionError: If conversion fails
        """
        # Try pdf2docx first
        try:
            logger.info(f"Attempting pdf2docx conversion: {input_path}")
            success = await self._convert_with_pdf2docx(input_path, output_path)
            if success and output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"pdf2docx conversion successful: {output_path}")
                return True
        except Exception as e:
            logger.warning(f"pdf2docx failed: {e}")

        # Fallback to LibreOffice
        try:
            logger.info(f"Attempting LibreOffice conversion: {input_path}")
            success = await self._convert_with_libreoffice(input_path, output_path)
            if success and output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"LibreOffice conversion successful: {output_path}")
                return True
        except Exception as e:
            logger.error(f"LibreOffice conversion failed: {e}")
            raise ConversionError(f"Both conversion methods failed. Last error: {e}")

        raise ConversionError("Conversion failed - empty output file")

    async def _convert_with_pdf2docx(self, input_path: Path, output_path: Path) -> bool:
        """Convert using pdf2docx library"""
        try:
            # Run in thread pool to not block
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._sync_pdf2docx_convert, input_path, output_path
            )
        except Exception as e:
            logger.error(f"pdf2docx error: {e}")
            return False

    def _sync_pdf2docx_convert(self, input_path: Path, output_path: Path) -> bool:
        """Synchronous pdf2docx conversion"""
        try:
            cv = Converter(str(input_path))
            cv.convert(str(output_path), start=0, end=None)
            cv.close()
            return True
        except Exception as e:
            logger.error(f"pdf2docx sync error: {e}")
            return False

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def _convert_with_libreoffice(
        self, input_path: Path, output_path: Path
    ) -> bool:
        """Convert using LibreOffice headless mode"""
        try:
            # Create temporary directory for LibreOffice output
            with tempfile.TemporaryDirectory() as tmpdir:
                cmd = [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    tmpdir,
                    str(input_path),
                ]

                logger.debug(f"Running command: {' '.join(cmd)}")

                # Run LibreOffice with timeout
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=120,  # 2 minute timeout
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    raise ConversionError("LibreOffice conversion timeout")

                if process.returncode != 0:
                    stderr_str = stderr.decode() if stderr else "Unknown error"
                    raise ConversionError(f"LibreOffice failed: {stderr_str}")

                # Find and move output file
                tmp_path = Path(tmpdir)
                docx_files = list(tmp_path.glob("*.docx"))

                if not docx_files:
                    raise ConversionError("LibreOffice did not produce output file")

                # Move to final destination
                shutil.move(str(docx_files[0]), str(output_path))
                return True

        except Exception as e:
            logger.error(f"LibreOffice error: {e}")
            raise

    def validate_pdf(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate if file is a valid PDF

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not file_path.exists():
                return False, "File not found"

            if file_path.stat().st_size == 0:
                return False, "File is empty"

            # Check PDF magic number
            with open(file_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    return False, "Invalid PDF format"

            return True, None

        except Exception as e:
            logger.error(f"PDF validation error: {e}")
            return False, f"Validation error: {str(e)}"


# Singleton instance
_converter_service: Optional[PDFConverterService] = None


def get_converter_service() -> PDFConverterService:
    """Get or create converter service singleton"""
    global _converter_service
    if _converter_service is None:
        _converter_service = PDFConverterService()
    return _converter_service
