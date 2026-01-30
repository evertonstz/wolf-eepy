import logging
from typing import Optional, IO, List

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"


def setup_logging(level: int = logging.INFO, stream: Optional[IO[str]] = None) -> None:
    """
    Standardize logging across wolf-eepy: always include time, level, message.
    Set 'level' as desired (default INFO); use stream if you want to log elsewhere (default stderr)
    """
    handlers: Optional[List[logging.Handler]] = None
    if stream:
        handlers = [logging.StreamHandler(stream)]
    logging.basicConfig(
        level=level, format=LOG_FORMAT, datefmt=LOG_DATEFMT, handlers=handlers
    )
