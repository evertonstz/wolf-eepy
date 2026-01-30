from monitor.monitor import WolfGuardian
from monitor.healthlock import HealthLockfile
from logging_config import setup_logging
from healthcheck.healthcheck import healthcheck


def monitor():
    setup_logging()
    healthlock = HealthLockfile("/tmp/wolf/healthstatus.lock")
    WolfGuardian(healthlock).run()


def healthcheck():
    setup_logging()
    healthcheck()


if __name__ == "__main__":
    monitor()
