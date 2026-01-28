import os
import fcntl
from datetime import datetime, timezone
from typing import Optional, TextIO

class HealthLockfile:
    '''Handles lockfile-based health and liveness reporting.'''
    def __init__(self, path: str) -> None:
        self.path = path
        self.file: Optional[TextIO] = None
        self._acquire_lock()

    def _acquire_lock(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.file = open(self.path, 'a+')
        fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def write_status(self, status: str) -> None:
        '''Write a health status and UTC timestamp.'''
        if not self.file:
            return
        ts = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        self.file.seek(0)
        self.file.write(f'{status}|{ts}\n')
        self.file.truncate()
        self.file.flush()

    def close(self) -> None:
        if self.file:
            self.file.close()
            self.file = None
