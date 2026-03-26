"""
Logging configuration — call setup_logging() once at app start.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=numeric,
        format=fmt,
        datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Quieten noisy libs
    for noisy in ("httpx", "httpcore", "urllib3", "asyncio", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
