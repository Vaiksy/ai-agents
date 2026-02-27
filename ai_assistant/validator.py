"""
Validator module for Local Windows AI Assistant.
Performs path safety checks, action validation, and security enforcement.
"""

import json
import os
from pathlib import Path
from typing import Any

from config import (
    ALLOWED_ACTIONS,
    ALLOWED_ROOTS,
    DESTRUCTIVE_ACTIONS,
    PATH_EXEMPT_ACTIONS,
)


class ValidationError(Exception):
    """Raised when a validation check fails."""
    pass


class Validator:
    """Validates parsed JSON commands against security rules."""

    def __init__(self) -> None:
        self.allowed_roots: list[Path] = [
            Path(r).resolve() for r in ALLOWED_ROOTS
        ]

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def validate(self, command: dict[str, Any]) -> dict[str, Any]:
        """
        Run all validation checks on a parsed command dict.
        Returns the (potentially modified) command dict on success.
        Raises ValidationError on failure.
        """
        self._validate_structure(command)
        action = command["action"]

        # Passthrough actions (clarify / denied) need no further checks
        if action in ("clarify", "denied"):
            return command

        self._validate_action(action)
        self._validate_paths(command)
        self._enforce_confirmation(command)
        return command

    def parse_json(self, raw: str) -> dict[str, Any]:
        """
        Safely parse a raw JSON string from the LLM.
        Strips markdown fences if present.
        """
        text = raw.strip()

        # Strip markdown code fences the LLM sometimes adds
        if text.startswith("```"):
            lines = text.splitlines()
            # Remove first and last lines (``` markers)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid JSON from LLM: {exc}") from exc

        if not isinstance(data, dict):
            raise ValidationError("LLM response is not a JSON object.")

        return data

    # ------------------------------------------------------------------
    # INTERNAL CHECKS
    # ------------------------------------------------------------------

    def _validate_structure(self, cmd: dict[str, Any]) -> None:
        """Ensure the command has the minimum required keys."""
        if "action" not in cmd:
            raise ValidationError("Missing 'action' key in command.")

        action = cmd["action"]

        if action in ("clarify", "denied"):
            return  # these don't need parameters

        if "parameters" not in cmd:
            raise ValidationError("Missing 'parameters' key in command.")

        if not isinstance(cmd["parameters"], dict):
            raise ValidationError("'parameters' must be a JSON object.")

    def _validate_action(self, action: str) -> None:
        """Reject actions not in the allow-list."""
        if action not in ALLOWED_ACTIONS:
            raise ValidationError(
                f"Action '{action}' is not allowed. "
                f"Permitted actions: {', '.join(ALLOWED_ACTIONS)}"
            )

    def _validate_paths(self, cmd: dict[str, Any]) -> None:
        """Ensure every path in the command falls under an allowed root."""
        action = cmd["action"]
        params = cmd.get("parameters", {})

        if action in PATH_EXEMPT_ACTIONS:
            return

        # Collect all path-like values that need checking
        paths_to_check: list[str] = []

        if "path" in params:
            paths_to_check.append(params["path"])
        if "source" in params:
            paths_to_check.append(params["source"])
        if "destination" in params:
            paths_to_check.append(params["destination"])

        if not paths_to_check:
            raise ValidationError(
                f"Action '{action}' requires a path but none was provided."
            )

        for p in paths_to_check:
            self._check_path_allowed(p)

    def _check_path_allowed(self, path_str: str) -> None:
        """Resolve a path and verify it sits under an allowed root."""
        try:
            resolved = Path(path_str).resolve()
        except (OSError, ValueError) as exc:
            raise ValidationError(f"Invalid path '{path_str}': {exc}") from exc

        # Block obvious system paths regardless of resolution tricks
        dangerous = [
            "windows", "system32", "program files", "program files (x86)",
            "programdata", "appdata", "$recycle.bin", "boot",
        ]
        lower = str(resolved).lower()
        for d in dangerous:
            if f"\\{d}" in lower or lower.startswith(d):
                raise ValidationError(
                    f"Access denied — '{path_str}' is a protected system path."
                )

        # Must be under at least one allowed root
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root)
                return  # path is allowed
            except ValueError:
                continue

        raise ValidationError(
            f"Access denied — '{path_str}' is outside allowed directories: "
            f"{', '.join(str(r) for r in self.allowed_roots)}"
        )

    def _enforce_confirmation(self, cmd: dict[str, Any]) -> None:
        """Force requires_confirmation=True on destructive actions."""
        if cmd["action"] in DESTRUCTIVE_ACTIONS:
            cmd["requires_confirmation"] = True
