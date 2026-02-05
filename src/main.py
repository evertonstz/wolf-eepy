from monitor.monitor import WolfGuardian
from monitor.healthlock import HealthLockfile
from logging_config import setup_logging
from healthcheck.healthcheck import healthcheck as _healthcheck_impl


def monitor():
    setup_logging()
    healthlock = HealthLockfile("/tmp/wolf/healthstatus.lock")
    WolfGuardian(healthlock).run()


def healthcheck():
    # wrapper that sets up logging then delegates to the real healthcheck
    setup_logging()
    return _healthcheck_impl()


if __name__ == "__main__":
    monitor()
