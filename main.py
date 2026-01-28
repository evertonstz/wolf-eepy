from monitor import WolfGuardian
from healthlock import HealthLockfile
from logging_config import setup_logging


def main():
    setup_logging()
    healthlock = HealthLockfile("/tmp/wolf/healthstatus.lock")
    WolfGuardian(healthlock).run()


if __name__ == "__main__":
    main()
