"""
project_parser.py — Enrich detected projects with AI-generated LinkedIn content.

Fetches README content from GitHub and asks the AI provider to generate
optimised title, summary, bullets, and skills.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ai_provider import AIProvider
from github_service import GitHubService
from logger import get_logger

log = get_logger("parser")


class ProjectParser:
    """Combines GitHub data + AI to produce LinkedIn-ready project content."""

    def __init__(self, github: GitHubService, ai: AIProvider) -> None:
        self._github = github
        self._ai = ai

    def parse(
        self,
        project: Dict[str, Any],
        repo_meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate LinkedIn-optimised content for a single project.

        Args:
            project: Dict from ProjectDetector (repo_name, project_name,
                path, github_url).
            repo_meta: Repo-level metadata from GitHubService (description,
                language, topics).

        Returns:
            Enriched dict with added keys: ``title``, ``summary``,
            ``bullets``, ``skills``.
        """
        repo_name = project["repo_name"]
        readme_path = (
            f"{project['path']}/README.md"
            if project["path"] != "/"
            else "README.md"
        )
        readme_content = self._github.get_file_content(repo_name, readme_path)

        ai_input: Dict[str, Any] = {
            "repo_name": repo_name,
            "project_name": project["project_name"],
            "github_url": project["github_url"],
            "description": repo_meta.get("description", ""),
            "language": repo_meta.get("language", "Unknown"),
            "topics": repo_meta.get("topics", []),
            "readme_excerpt": readme_content[:3000],
        }

        log.info("Generating AI content for '%s' …", project["project_name"])
        try:
            ai_result = self._ai.generate_project_content(ai_input)
        except ValueError as exc:
            log.error("AI generation failed for '%s': %s", project["project_name"], exc)
            ai_result = self._fallback_content(project, repo_meta)

        return {**project, **ai_result}

    def parse_all(
        self,
        projects: List[Dict[str, Any]],
        repo_meta: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Parse a batch of projects from the same repository."""
        return [self.parse(p, repo_meta) for p in projects]

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_content(
        project: Dict[str, Any],
        repo_meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return minimal content when AI generation fails."""
        log.warning("Using fallback content for '%s'.", project["project_name"])
        return {
            "title": project["project_name"].replace("-", " ").replace("_", " ").title(),
            "summary": repo_meta.get("description", "A GitHub project."),
            "bullets": [
                f"Built with {repo_meta.get('language', 'multiple technologies')}",
                "Open-source project available on GitHub",
            ],
            "skills": [repo_meta.get("language", "Programming")] + repo_meta.get("topics", [])[:4],
        }
