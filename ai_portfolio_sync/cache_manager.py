"""
cache_manager.py — Persistent JSON cache with atomic writes & corruption handling.

Cache structure: ``{ "repo/project": true }``
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict

from logger import get_logger

log = get_logger("cache")


class CacheManager:
    """Manages a local JSON cache to track processed projects."""

    def __init__(self, cache_path: Path) -> None:
        """
        Args:
            cache_path: Absolute path to the JSON cache file.
        """
        self._path = cache_path
        self._data: Dict[str, bool] = {}
        self.load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load cache from disk. Resets to empty dict on corruption."""
        if not self._path.exists():
            self._data = {}
            log.debug("Cache file not found — starting fresh.")
            return
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)
            log.debug("Loaded %d cached entries.", len(self._data))
        except (json.JSONDecodeError, IOError) as exc:
            log.warning("Cache corrupted (%s) — resetting.", exc)
            self._data = {}
            self.save()

    def save(self) -> None:
        """Atomically persist cache to disk (temp-file + os.replace)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd, tmp = tempfile.mkstemp(
                dir=str(self._path.parent), suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
            os.replace(tmp, str(self._path))
            log.debug("Cache saved (%d entries).", len(self._data))
        except IOError as exc:
            log.error("Failed to save cache: %s", exc)

    def is_cached(self, key: str) -> bool:
        """Check if a project key has already been processed."""
        return self._data.get(key, False) is True

    def mark_cached(self, key: str) -> None:
        """Mark a project key as processed and persist."""
        self._data[key] = True
        self.save()

    @property
    def entries(self) -> Dict[str, bool]:
        """Return a copy of the current cache data."""
        return dict(self._data)
