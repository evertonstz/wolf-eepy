import os
import fcntl
from datetime import datetime, timezone
from typing import Optional, TextIO


class HealthLockfile:
    """Handles lockfile-based health and liveness reporting."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.file: Optional[TextIO] = None
        self._acquire_lock()

    def _acquire_lock(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        # Open for update without implicit append so writes can overwrite
        # the file (we keep a single canonical status line).
        if os.path.exists(self.path):
            self.file = open(self.path, "r+")
        else:
            # create the file if it doesn't exist
            self.file = open(self.path, "w+")
        fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def write_status(self, status: str) -> None:
        """Write a health status and UTC timestamp."""
        if not self.file:
            return
        ts = (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        # Overwrite the file with a single status line and persist to disk.
        try:
            self.file.seek(0)
            self.file.write(f"{status}|{ts}\n")
            # truncate any leftover data from previous writes
            self.file.truncate(self.file.tell())
            self.file.flush()
            try:
                # make sure data hits disk
                os.fsync(self.file.fileno())
            except OSError:
                # fsync may not be available in some environments; ignore
                pass
        except Exception:
            # best-effort: if the locked file becomes invalid, ignore to avoid
            # crashing the monitor; caller will log if necessary
            return

    def close(self) -> None:
        if self.file:
            self.file.close()
            self.file = None
