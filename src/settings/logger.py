"""Logging configuration helpers for the bot process."""

import logging
import sys

import colorlog


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure colored console logging for the current process."""

    if isinstance(level, str):
        level = logging.getLevelNamesMapping()[level.upper()]

    fmt = "%(log_color)s%(asctime)s.%(msecs)05d | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    log_colors = {
        "DEBUG": "white",
        "INFO": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bg_red,white",
    }

    stream_handler = colorlog.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        colorlog.ColoredFormatter(
            fmt=fmt,
            datefmt=datefmt,
            log_colors=log_colors,
        )
    )

    logging.basicConfig(
        level=level,
        handlers=[stream_handler],
    )
