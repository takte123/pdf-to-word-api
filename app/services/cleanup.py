"""
File cleanup service
"""

import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Set

from app.core.config import get_settings
from app.core.logging import logger


class FileCleanupService:
    """Service for cleaning up old files"""

    def __init__(self):
        self.settings = get_settings()
        self.running = False
        self._task: asyncio.Task | None = None
        self._protected_files: Set[str] = set()

    def start(self):
        """Start the cleanup service"""
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._cleanup_loop())
            logger.info("File cleanup service started")

    def stop(self):
        """Stop the cleanup service"""
        self.running = False
        if self._task:
            self._task.cancel()
            logger.info("File cleanup service stopped")

    def protect_file(self, file_path: str):
        """Mark a file as protected (don't delete)"""
        self._protected_files.add(file_path)

    def unprotect_file(self, file_path: str):
        """Remove file protection"""
        self._protected_files.discard(file_path)

    async def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.running:
            try:
                await self._cleanup_old_files()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

            # Run every 5 minutes
            await asyncio.sleep(300)

    async def _cleanup_old_files(self):
        """Delete files older than retention period"""
        retention = timedelta(minutes=self.settings.file_retention_minutes)
        cutoff_time = datetime.now() - retention

        dirs_to_clean = [
            Path(self.settings.uploads_dir),
            Path(self.settings.outputs_dir),
        ]

        for dir_path in dirs_to_clean:
            if not dir_path.exists():
                continue

            for file_path in dir_path.iterdir():
                if not file_path.is_file():
                    continue

                # Skip protected files
                if str(file_path) in self._protected_files:
                    continue

                try:
                    stat = file_path.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime)

                    if mtime < cutoff_time:
                        file_path.unlink()
                        logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")


# Singleton instance
_cleanup_service: FileCleanupService | None = None


def get_cleanup_service() -> FileCleanupService:
    """Get or create cleanup service singleton"""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = FileCleanupService()
    return _cleanup_service
