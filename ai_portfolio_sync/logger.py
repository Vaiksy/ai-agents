"""
logger.py — Structured, coloured console logging for AI Portfolio Sync.
"""

from __future__ import annotations

import logging
import sys


# ---------------------------------------------------------------------------
# ANSI colour codes for terminal output
# ---------------------------------------------------------------------------
_COLOURS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[1;31m", # bold red
    "RESET":    "\033[0m",
}


class _ColouredFormatter(logging.Formatter):
    """Formatter that adds ANSI colours based on log level."""

    FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FMT = "%H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        reset = _COLOURS["RESET"]
        record.levelname = f"{colour}{record.levelname}{reset}"
        formatter = logging.Formatter(self.FMT, datefmt=self.DATE_FMT)
        return formatter.format(record)


def setup_logger(debug: bool = False) -> logging.Logger:
    """
    Configure and return the root application logger.

    Args:
        debug: If True, set level to DEBUG; otherwise INFO.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger("ai_portfolio_sync")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Avoid duplicate handlers on repeated calls
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_ColouredFormatter())
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the application namespace.

    Args:
        name: Module or component name.

    Returns:
        A logging.Logger scoped to ``ai_portfolio_sync.<name>``.
    """
    return logging.getLogger(f"ai_portfolio_sync.{name}")
