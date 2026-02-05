#!/usr/bin/env python3
import sys
import fcntl
import logging
from datetime import datetime, timezone

import os

LOCKFILE = os.environ.get("HEALTHCHECK_LOCKFILE", "/tmp/wolf/healthstatus.lock")


FRESHNESS_THRESHOLD_S = int(os.environ.get("GRACE_PERIOD", "300")) / 2


def healthcheck():
    try:
        with open(LOCKFILE, "r+") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                logging.error("UNHEALTHY: lock not held")
                sys.exit(2)
            except BlockingIOError:
                # Lock is held -> process running
                f.seek(0)
                # Read the most recent non-empty line (last written status).
                contents = f.read()
                lines = [l.strip() for l in contents.splitlines() if l.strip()]
                if not lines:
                    logging.error("UNHEALTHY: status line missing or malformed")
                    sys.exit(2)
                line = lines[-1]
                if "|" not in line:
                    logging.error("UNHEALTHY: status line missing or malformed")
                    sys.exit(2)
                status, ts = line.split("|", 1)
                # Parse timestamp and check freshness
                try:
                    t = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(
                        tzinfo=timezone.utc
                    )
                    age = (datetime.now(timezone.utc) - t).total_seconds()
                except Exception:
                    logging.error("UNHEALTHY: could not parse timestamp")
                    sys.exit(2)
                if age > FRESHNESS_THRESHOLD_S:
                    logging.error(f"UNHEALTHY: STALE (age={int(age)}s)")
                    sys.exit(2)
                if status == "healthy":
                    logging.info("HEALTHY")
                    sys.exit(0)
                elif status == "warning":
                    logging.warning("WARNING")
                    sys.exit(1)
                else:
                    logging.error(f"UNHEALTHY: status={status!r}")
                    sys.exit(2)
    except FileNotFoundError:
        logging.error("UNHEALTHY: lockfile not found")
        sys.exit(2)
    except Exception as e:
        logging.error(f"UNHEALTHY: exception {e}")
        sys.exit(2)
