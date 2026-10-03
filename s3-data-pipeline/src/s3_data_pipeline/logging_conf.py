"""Basic structured-ish logging setup shared across the pipeline."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
    )
    # basicConfig is a no-op when handlers already exist (e.g. Lambda pre-installs
    # one), which would leave the level at WARNING and drop our INFO logs.
    logging.getLogger().setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
