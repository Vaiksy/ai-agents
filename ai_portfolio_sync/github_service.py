"""
github_service.py — GitHub REST API integration.

Fetches user repositories and file trees for sub-project detection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from logger import get_logger

log = get_logger("github")


class GitHubService:
    """Thin wrapper around the GitHub REST API v3."""

    API = "https://api.github.com"

    def __init__(self, token: str, username: str) -> None:
        """
        Args:
            token: GitHub personal access token.
            username: GitHub username whose repos to scan.
        """
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}" if token else "",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        self._username = username
        log.info("GitHub service initialised for user '%s'", username)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_user_repos(self, repo_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return public repos for the configured user.

        Args:
            repo_filter: If provided, return only the repo with this name.

        Returns:
            List of dicts with keys: name, html_url, description,
            language, topics.
        """
        repos: List[Dict[str, Any]] = []
        page = 1
        while True:
            url = f"{self.API}/users/{self._username}/repos"
            params = {"per_page": 100, "page": page, "sort": "updated"}
            resp = self._session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            repos.extend(batch)
            page += 1

        results = []
        for r in repos:
            if r.get("fork"):
                continue
            if repo_filter and r["name"] != repo_filter:
                continue
            results.append(
                {
                    "name": r["name"],
                    "html_url": r["html_url"],
                    "description": r.get("description") or "",
                    "language": r.get("language") or "Unknown",
                    "topics": r.get("topics", []),
                }
            )

        log.info("Fetched %d repo(s).", len(results))
        return results

    def get_repo_tree(self, repo_name: str) -> List[str]:
        """
        Return a flat list of file/directory paths in a repo's default branch.

        Args:
            repo_name: Name of the repository.

        Returns:
            List of path strings, e.g. ``["src/main.py", "README.md"]``.
        """
        url = f"{self.API}/repos/{self._username}/{repo_name}/git/trees/HEAD"
        params = {"recursive": "1"}
        resp = self._session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        tree = resp.json().get("tree", [])
        return [item["path"] for item in tree]

    def get_file_content(self, repo_name: str, file_path: str) -> str:
        """
        Fetch the raw content of a file from a repository.

        Args:
            repo_name: Repository name.
            file_path: Path inside the repo (e.g. ``README.md``).

        Returns:
            Decoded UTF-8 text content, or empty string on failure.
        """
        url = (
            f"https://raw.githubusercontent.com/"
            f"{self._username}/{repo_name}/HEAD/{file_path}"
        )
        try:
            resp = self._session.get(url, timeout=20)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            log.warning("Could not fetch %s/%s: %s", repo_name, file_path, exc)
            return ""
