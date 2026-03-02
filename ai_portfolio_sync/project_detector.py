"""
project_detector.py — Detect sub-projects within GitHub repository trees.

A folder qualifies as a project if it contains certain marker files.
"""

from __future__ import annotations

import posixpath
from typing import Any, Dict, List, Set

from logger import get_logger

log = get_logger("detector")

# Files whose presence flags a directory as a project root
_MARKER_FILES: Set[str] = {
    "README.md",
    "readme.md",
    "requirements.txt",
    "package.json",
    "main.py",
    "app.py",
    "index.js",
}

# Extensions whose presence also flags a directory
_MARKER_EXTENSIONS: Set[str] = {
    ".ipynb",
    ".pkl",
    ".pt",
    ".h5",
}

# Directories to always exclude
_EXCLUDED_DIRS: Set[str] = {
    ".github",
    ".git",
    "docs",
    "tests",
    "test",
    "dist",
    "build",
    "node_modules",
    "__pycache__",
    ".vscode",
    ".idea",
    "venv",
    ".venv",
    "env",
}


class ProjectDetector:
    """Scans a repo file tree and identifies independent sub-projects."""

    def detect(
        self,
        repo_name: str,
        repo_url: str,
        file_paths: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Identify projects from a flat list of file paths.

        Args:
            repo_name: Name of the repository.
            repo_url: HTTPS URL of the repository.
            file_paths: Flat list of every path in the repo tree.

        Returns:
            List of project dicts with keys: ``repo_name``,
            ``project_name``, ``path``, ``github_url``.
        """
        project_dirs: Set[str] = set()

        for fp in file_paths:
            parts = fp.split("/")
            filename = parts[-1]
            dir_path = "/".join(parts[:-1]) if len(parts) > 1 else ""

            # Skip excluded directories
            if any(ex in parts for ex in _EXCLUDED_DIRS):
                continue

            is_marker = (
                filename in _MARKER_FILES
                or any(filename.endswith(ext) for ext in _MARKER_EXTENSIONS)
            )

            if is_marker:
                # Use the parent directory, or repo root ("")
                project_dirs.add(dir_path)

        # Build result list
        projects: List[Dict[str, Any]] = []
        for d in sorted(project_dirs):
            project_name = d if d else repo_name
            github_url = f"{repo_url}/tree/main/{d}" if d else repo_url
            projects.append(
                {
                    "repo_name": repo_name,
                    "project_name": project_name,
                    "path": d if d else "/",
                    "github_url": github_url,
                }
            )

        log.info(
            "Detected %d project(s) in '%s': %s",
            len(projects),
            repo_name,
            [p["project_name"] for p in projects],
        )
        return projects
