import subprocess
import time
import requests
import requests_unixsocket  # type: ignore
import os
import logging
from typing import Optional
from .healthlock import HealthLockfile

# Configuration
WOLF_SOCKET_PATH = os.environ.get("WOLF_SOCKET_PATH", "/var/run/wolf/wolf.sock")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "30"))
GRACE_PERIOD = int(os.environ.get("GRACE_PERIOD", "300"))

WOLF_SESSIONS_API_URL = (
    f"http+unix://{WOLF_SOCKET_PATH.replace('/', '%2F')}/api/v1/sessions"
)


class WolfGuardian:
    def __init__(self, healthlock: HealthLockfile) -> None:
        self.session = requests_unixsocket.Session()
        self.inhibit_proc: Optional[subprocess.Popen[bytes]] = None
        self.idle_since: Optional[float] = None
        self.wolf_ready: bool = False
        self.healthlock = healthlock

    def wait_for_wolf(self) -> None:
        """Polls until the socket exists and the API responds with 200 OK."""
        logging.info(f"Status: Waiting for Wolf socket at {WOLF_SOCKET_PATH}...")
        while not self.wolf_ready:
            if os.path.exists(WOLF_SOCKET_PATH):
                try:
                    # Just a quick ping to see if the API is actually listening
                    response = self.session.get(WOLF_SESSIONS_API_URL, timeout=2)
                    if response.status_code == 200:
                        logging.info("Status: Wolf API is UP. Starting monitor.")
                        self.wolf_ready = True
                        self.healthlock.write_status("healthy")
                        return
                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError,
                ):
                    self.healthlock.write_status("warning")  # Wolf is still booting
            else:
                self.healthlock.write_status("warning")
            time.sleep(2)

    def get_session_count(self) -> int:
        try:
            response = self.session.get(WOLF_SESSIONS_API_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            return len(data.get("sessions", []))
        except Exception:
            # If Wolf disappears (restart/crash), reset readiness
            logging.warning("Lost connection to Wolf. Re-verifying...")
            self.wolf_ready = False
            self.healthlock.write_status("warning")
            self.wait_for_wolf()
            return 0

    def inhibit(self) -> None:
        if not self.inhibit_proc:
            logging.info(
                "Action: Active session detected. Locking host sleep (trying systemd-inhibit)."
            )
            try:
                self.inhibit_proc = subprocess.Popen(
                    [
                        "systemd-inhibit",
                        "--mode=block",
                        "--why=Wolf Stream Active",
                        "--who=WolfMonitor",
                        "sleep",
                        "infinity",
                    ]
                )
                logging.info(f"systemd-inhibit started, PID={self.inhibit_proc.pid}")
            except Exception as e:
                logging.error(f"Failed to launch systemd-inhibit: {e}")
                self.inhibit_proc = None

    def release(self) -> None:
        if self.inhibit_proc:
            logging.info("Action: Cooldown finished. Releasing sleep lock.")
            self.inhibit_proc.terminate()
            self.inhibit_proc.wait()
            self.inhibit_proc = None

    def run(self) -> None:
        logging.info("Wolf Monitor: Python Guardian initialized.")
        self.wait_for_wolf()
        while True:
            count = self.get_session_count()
            if count > 0:
                self.idle_since = None
                self.inhibit()
            else:
                if self.inhibit_proc:
                    if self.idle_since is None:
                        logging.info(
                            f"Status: No sessions. Starting {GRACE_PERIOD}s cooldown..."
                        )
                        self.idle_since = time.time()
                    if (time.time() - self.idle_since) >= GRACE_PERIOD:
                        self.release()
            time.sleep(CHECK_INTERVAL)
            # Refresh the health lockfile timestamp so external healthcheck
            # processes see the monitor is still alive. We write 'healthy'
            # when we've verified the Wolf API is ready, otherwise 'warning'.
            try:
                status = "healthy" if self.wolf_ready else "warning"
                self.healthlock.write_status(status)
            except Exception:
                logging.exception("Failed to refresh health status")
