"""
Executor module for Local Windows AI Assistant.
Safely executes validated JSON commands on the local Windows OS.
"""

from __future__ import annotations

import ctypes
import fnmatch
import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from config import LOG_FILE

# ========================
# LOGGING SETUP
# ========================

logger = logging.getLogger("ai_assistant")
logger.setLevel(logging.INFO)
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(_fh)

# Map of friendly app names → executables
APP_ALIASES: dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "code": "code.exe",
    "vscode": "code.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "spotify": "spotify.exe",
    "terminal": "wt.exe",
}


class ExecutionError(Exception):
    """Raised when command execution fails."""
    pass


class Executor:
    """Executes validated commands against the Windows OS."""

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def execute(self, command: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch a validated command dict to the appropriate handler.
        Returns a result dict with 'status' and 'message' / 'data'.
        """
        action = command["action"]
        params = command.get("parameters", {})

        # Passthrough informational actions
        if action == "clarify":
            return {"status": "clarify", "message": command.get("message", "")}
        if action == "denied":
            return {"status": "denied", "reason": command.get("reason", "")}

        handler = getattr(self, f"_do_{action}", None)
        if handler is None:
            raise ExecutionError(f"No handler for action '{action}'.")

        logger.info("EXEC  action=%s  params=%s", action, params)

        try:
            result = handler(params)
            logger.info("OK    action=%s  result=%s", action, _trunc(result))
            return result
        except Exception as exc:
            logger.error("FAIL  action=%s  error=%s", action, exc)
            return {"status": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    # ACTION HANDLERS
    # ------------------------------------------------------------------

    def _do_open_folder(self, params: dict) -> dict:
        path = params["path"]
        if not Path(path).is_dir():
            return {"status": "error", "message": f"Directory not found: {path}"}
        os.startfile(path)
        return {"status": "success", "message": f"Opened folder: {path}"}

    def _do_open_file(self, params: dict) -> dict:
        path = params["path"]
        if not Path(path).is_file():
            return {"status": "error", "message": f"File not found: {path}"}
        os.startfile(path)
        return {"status": "success", "message": f"Opened file: {path}"}

    def _do_open_application(self, params: dict) -> dict:
        name = params.get("name", "").lower().strip()
        exe = APP_ALIASES.get(name, name)
        try:
            subprocess.Popen(
                exe,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {"status": "success", "message": f"Launched: {exe}"}
        except Exception as exc:
            return {"status": "error", "message": f"Could not launch '{exe}': {exc}"}

    def _do_list_directory(self, params: dict) -> dict:
        path = Path(params["path"])
        if not path.is_dir():
            return {"status": "error", "message": f"Directory not found: {path}"}
        entries = []
        for entry in sorted(path.iterdir()):
            kind = "DIR" if entry.is_dir() else "FILE"
            size = entry.stat().st_size if entry.is_file() else "-"
            entries.append({"name": entry.name, "type": kind, "size": size})
        return {"status": "success", "data": entries, "count": len(entries)}

    def _do_search_file(self, params: dict) -> dict:
        root = Path(params["path"])
        pattern = params.get("pattern", "*")
        if not root.is_dir():
            return {"status": "error", "message": f"Directory not found: {root}"}
        matches: list[str] = []
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                if fnmatch.fnmatch(fname.lower(), pattern.lower()):
                    matches.append(str(Path(dirpath) / fname))
            if len(matches) >= 200:  # safety cap
                break
        return {"status": "success", "matches": matches, "count": len(matches)}

    def _do_create_folder(self, params: dict) -> dict:
        path = Path(params["path"])
        if path.exists():
            return {"status": "info", "message": f"Folder already exists: {path}"}
        path.mkdir(parents=True, exist_ok=True)
        return {"status": "success", "message": f"Created folder: {path}"}

    def _do_delete_file(self, params: dict) -> dict:
        path = Path(params["path"])
        if not path.exists():
            return {"status": "error", "message": f"Path not found: {path}"}
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return {"status": "success", "message": f"Deleted: {path}"}

    def _do_move_file(self, params: dict) -> dict:
        src = Path(params["source"])
        dst = Path(params["destination"])
        if not src.exists():
            return {"status": "error", "message": f"Source not found: {src}"}
        shutil.move(str(src), str(dst))
        return {"status": "success", "message": f"Moved {src} → {dst}"}

    def _do_copy_file(self, params: dict) -> dict:
        src = Path(params["source"])
        dst = Path(params["destination"])
        if not src.exists():
            return {"status": "error", "message": f"Source not found: {src}"}
        if src.is_dir():
            shutil.copytree(str(src), str(dst))
        else:
            dst_path = dst
            if dst.is_dir():
                dst_path = dst / src.name
            shutil.copy2(str(src), str(dst_path))
        return {"status": "success", "message": f"Copied {src} → {dst}"}

    def _do_change_wallpaper(self, params: dict) -> dict:
        path = params["path"]
        if not Path(path).is_file():
            return {"status": "error", "message": f"Image not found: {path}"}
        SPI_SETDESKWALLPAPER = 0x0014
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            str(Path(path).resolve()),
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
        )
        if result:
            return {"status": "success", "message": f"Wallpaper set to: {path}"}
        return {"status": "error", "message": "Failed to set wallpaper."}

    def _do_close_application(self, params: dict) -> dict:
        name = params.get("name", "").lower().strip()
        exe = APP_ALIASES.get(name, name)
        # Ensure it ends with .exe for taskkill
        if not exe.endswith(".exe"):
            exe += ".exe"
        try:
            result = subprocess.run(
                ["taskkill", "/IM", exe, "/F"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return {"status": "success", "message": f"Closed: {exe}"}
            return {"status": "error", "message": result.stderr.strip()}
        except Exception as exc:
            return {"status": "error", "message": f"Failed to close '{exe}': {exc}"}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _trunc(obj: Any, max_len: int = 200) -> str:
    """Truncate a repr for safe logging."""
    s = str(obj)
    return s[:max_len] + "…" if len(s) > max_len else s
